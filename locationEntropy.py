from math import log2
import dill
import traceback
import qwikidata
import qwikidata.sparql
from multiprocessing import Pool
from typing import List,Dict,Any,Tuple,Optional,Set

def population_entropy(my_dict : Dict[Any,int]) -> Tuple[int,int,float]:
    total_population : int = sum(my_dict.values())
    if total_population<=0:
        raise ValueError("There must be a strictly positive total number of counts")
    entropy_contrib : List[float] = [-p/total_population*log2(p/total_population) for p in my_dict.values() if p>0]
    return (total_population,len(my_dict),sum(entropy_contrib))

def just_country_info() -> str:
    query : str = """
    SELECT ?country ?countryLabel ?population
    WHERE
    {
    ?country wdt:P31 wd:Q6256.
    ?country wdt:P1082 ?population.
    FILTER(?population > 0).
    ?country rdfs:label ?countryLabel.
    FILTER(LANG(?countryLabel) = "en").
    }
    """
    res : Dict = qwikidata.sparql.return_sparql_query_results(query)
    res2 : Dict = res['results']['bindings']
    country_pops : Dict[str,int] = {item['countryLabel']['value']:int(item['population']['value']) for item in res2}

    total_population : int
    num_items : int
    entropy : float
    total_population, num_items, entropy = population_entropy(country_pops)
    return (f"There are {entropy} bits of entropy in just country information.\n"
        f"That is to say if you took the pushforward of the uniform probability measure on all people along the map which sends everyone to their country\n"
        f"{log2(total_population)} would be required for unique identification.")

def get_all_cities(limit : Optional[int] = None,failLoud : bool =True) -> List[Tuple[str,str]]:
    query : str = """
    SELECT ?country ?countryLabel ?city ?cityLabel
    WHERE
    {
        ?country wdt:P31 wd:Q6256.
        ?city wdt:P31/wdt:P279* wd:Q515.
        ?city wdt:P17 ?country.
        ?city wdt:P1082 ?population.
        FILTER(?population > 0).
        ?city rdfs:label ?cityLabel.
        ?country rdfs:label ?countryLabel.
        FILTER(LANG(?cityLabel) = "en").
        FILTER(LANG(?countryLabel) = "en").
    }
    """
    if not(limit is None):
        query = query + """LIMIT %s""" % (str(limit))
    try:
        res : Dict = qwikidata.sparql.return_sparql_query_results(query)
        res2 : Dict = res['results']['bindings']
        out : Set[Tuple[str,str]] = {(item['cityLabel']['value'],item['countryLabel']['value']) for item in res2}
    except Exception as e:
        if failLoud:
            raise e
        else:
            out = {}
    return list(out)

def get_city_wikidata(city : str, country : str, failLoud : bool =True) -> Dict:
    query : str = """
    SELECT ?city ?cityLabel ?country ?countryLabel ?population
    WHERE
    {
      ?country wdt:P31 wd:Q6256.
      ?city rdfs:label '%s'@en.
      ?city wdt:P1082 ?population.
      ?city wdt:P17 ?country.
      ?city rdfs:label ?cityLabel.
      ?country rdfs:label ?countryLabel.
      FILTER(LANG(?cityLabel) = "en").
      FILTER(LANG(?countryLabel) = "en").
      FILTER(CONTAINS(?countryLabel, "%s")).
    }
    """ % (city, country)

    try:
        res : Dict = qwikidata.sparql.return_sparql_query_results(query)
        out : Dict = res['results']['bindings']
    except Exception as e:
        if failLoud:
            traceback.print_exc()
        out = None
    if out is None:
        out = []
    return out

def get_city_population(city : str,country : str,failLoud : bool = True) -> Dict[Tuple[str,str,int],int]:
    wd : Dict
    try:
        wd = get_city_wikidata(city,country,failLoud)
    except Exception as e:
        if failLoud:
            raise e
        else:
            wd = []
    if len(wd) == 0:
        if failLoud:
            traceback.print_exc()
            raise ValueError(f"No such city as {city}, {country}")
        else:
            return {(city,country,0):0}
    else:
        possible_populations : List[str] = [x.get('population',{}).get('value','0') for x in wd]
        possible_populations : List[int] = [int(x) for x in possible_populations]
        with_index : List[Tuple[int,int]] = [y for y in enumerate(possible_populations)]
        return {(city,country,index):possible_population for (index,possible_population) in with_index}

def run_dill_encoded(payload):
    fun, args = dill.loads(payload)
    return fun(*args)


def apply_async(pool, fun, args):
    payload = dill.dumps((fun, args))
    return pool.apply_async(run_dill_encoded, (payload,))

def just_city_info(all_cities : Optional[List[Tuple[str,str]]] =None,limit : Optional[int] =None, city_qualifier : Optional[str] = None) -> str:
    if all_cities is None:
        all_cities = get_all_cities(limit,failLoud=False)
        city_qualifier = "any city"
    elif city_qualifier is None:
        raise ValueError("If a list of cities is provided there must be some description on how this subset was chosen")
    else:
        limit = len(all_cities)
    if limit is None:
        limit = len(all_cities)
    city_pops : Dict[Tuple[str,str,int],int] = {}
    with Pool() as pool:
        jobs = [ apply_async(pool, lambda x, y, z: get_city_population(x,y,z), (city[0], city[1], False )) for city in all_cities ]
        for job in jobs:
            current_dict : Optional[Dict[Tuple[str,str,int],int]] = job.get()
            if not(current_dict is None):
                city_pops.update(current_dict)
    try:
        total_population : int
        num_items : int
        entropy : float
        total_population, num_items, entropy = population_entropy(city_pops)
        return (f"There are {entropy} bits of entropy in just city information.\n"
            f"That is to say if you took the pushforward of the uniform probability measure on all people in {city_qualifier} along the map which sends everyone to their city\n"
            f"{log2(total_population)} would be required for unique identification.")
    except ValueError as e:
        breakpoint()

def no_location_known(age_known : bool = False, gender_known : bool = False) -> str:
    query : str = """
    SELECT ?country ?countryLabel ?population
    WHERE
    {
    ?country wdt:P31 wd:Q6256.
    ?country wdt:P1082 ?population.
    FILTER(?population > 0).
    ?country rdfs:label ?countryLabel.
    FILTER(LANG(?countryLabel) = "en").
    }
    """
    res : Dict = qwikidata.sparql.return_sparql_query_results(query)
    res2 : Dict = res['results']['bindings']
    country_pops : Dict[str,int] = {item['countryLabel']['value']:int(item['population']['value']) for item in res2}

    total_population : int
    num_items : int
    entropy : float
    total_population, _, _ = population_entropy(country_pops)
    if not age_known and not gender_known:
        return (f"That is shocking in the era of surveilance capitalism.\n"
            f"{log2(total_population)} bits of entropy would be required for unique identification")
    elif not age_known and gender_known:
        raise ValueError("TODO")
    elif age_known and not gender_known:
        raise ValueError("TODO")
    else:
        raise ValueError("TODO")

def city_population_test():
    print(f"Berlin, Germany has {get_city_population('Berlin', 'Germany')} people")
    print(f"San Francisco, America has {get_city_population('San Francisco', 'America')} people")
    print(f"Beijing, China has {get_city_population('Beijing', 'China')} people")
    print(f"Mumbai, India has {get_city_population('Mumbai', 'India')} people")


if __name__ == '__main__':
    info_country : str = just_country_info()
    print(f"{info_country}")
    info_1city : str = just_city_info(all_cities=[("New York City","America")])
    print(f"Using only New York City\n{info_1city}")
    info_5cities : str = just_city_info(all_cities=[("New York City","America"),("San Francisco","America"),("Berlin","Germany"),("Beijing","China"),("Mumbai","India")])
    print(f"Using only New York City, San Francisco, Berlin, Beijing and Mumbai\n{info_5cities}")
    limit_number : int = 100
    info_manycities : str = just_city_info(all_cities=None,limit=limit_number)
    print(f"Using only a nondeterministic set of {limit_number} cities drawn from WikiData.\n{info_manycities}")