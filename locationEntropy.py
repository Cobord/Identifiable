from math import log2
import dill
import traceback
import qwikidata
import qwikidata.sparql
from multiprocessing import Pool

def population_entropy(my_dict):
    total_population = sum(my_dict.values())
    if total_population<=0:
        raise ValueError("There must be a strictly positive total number of counts")
    entropy_contrib = [-p/total_population*log2(p/total_population) for p in my_dict.values() if p>0]
    return (total_population,len(my_dict),sum(entropy_contrib))

def just_country_info():
    query = """
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
    res = qwikidata.sparql.return_sparql_query_results(query)
    res2 = res['results']['bindings']
    country_pops = {item['countryLabel']['value']:int(item['population']['value']) for item in res2}

    # country = CountryInfo().all()
    # country_pops = {k:v.get('population',0) for (k,v) in country.items()}
    total_population, num_items,entropy = population_entropy(country_pops)
    return (f"Just country information provides {entropy} bits of entropy. "
        f"It would be {log2(num_items)} if all the possibilities were equal. "
        f"{log2(total_population)} would be required for unique identification.")

def get_all_cities(limit=None,failLoud=True):
    query = """
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
        res = qwikidata.sparql.return_sparql_query_results(query)
        res2 = res['results']['bindings']
        out = {(item['cityLabel']['value'],item['countryLabel']['value']) for item in res2}
    except Exception as e:
        if failLoud:
            raise e
        else:
            out = {}
    return list(out)

def get_city_wikidata(city, country, failLoud=True):
    query = """
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
        res = qwikidata.sparql.return_sparql_query_results(query)
        out = res['results']['bindings']
    except Exception as e:
        if failLoud:
            traceback.print_exc()
        out = None
    if out is None:
        out = []
    return out

def get_city_population(city,country,failLoud=True):
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
        possible_populations = [x.get('population',{}).get('value','0') for x in wd]
        possible_populations = [int(x) for x in possible_populations]
        with_index = [y for y in enumerate(possible_populations)]
        return {(city,country,index):possible_population for (index,possible_population) in with_index}

def run_dill_encoded(payload):
    fun, args = dill.loads(payload)
    return fun(*args)


def apply_async(pool, fun, args):
    payload = dill.dumps((fun, args))
    return pool.apply_async(run_dill_encoded, (payload,))

def just_city_info(all_cities=None,limit=None):
    if all_cities is None:
        all_cities = get_all_cities(limit,failLoud=False)
    else:
        limit = len(all_cities)
    if limit is None:
        limit = len(all_cities)
    city_pops = {}
    with Pool() as pool:
        jobs = [ apply_async(pool, lambda x, y, z: get_city_population(x,y,z), (city[0], city[1], False )) for city in all_cities ]
        for job in jobs:
            current_dict = job.get()
            if not(current_dict is None):
                city_pops.update(current_dict)
    try:
        total_population, num_items,entropy = population_entropy(city_pops)
        return (f"Just city information provides {entropy} bits of entropy. "
                f"It would be {log2(num_items)} if all the possibilities were equal. "
                f"{log2(total_population)} would be required for unique identification")
    except ValueError as e:
        breakpoint()

def city_population_test():
    print(f"Berlin, Germany has {get_city_population('Berlin', 'Germany')} people")
    print(f"San Francisco, America has {get_city_population('San Francisco', 'America')} people")
    print(f"Beijing, China has {get_city_population('Beijing', 'China')} people")
    print(f"Mumbai, India has {get_city_population('Mumbai', 'India')} people")


if __name__ == '__main__':
    info_country = just_country_info()
    print(f"{info_country}")
    info_1city = just_city_info(all_cities=[("New York City","America")])
    print(f"Using only New York City\n{info_1city}")
    info_5cities = just_city_info(all_cities=[("New York City","America"),("San Francisco","America"),("Berlin","Germany"),("Beijing","China"),("Mumbai","India")])
    print(f"Using only New York City, San Francisco, Berlin, Beijing and Mumbai\n{info_5cities}")
    limit_number = 100
    info_manycities = just_city_info(all_cities=None,limit=limit_number)
    print(f"Using only a nondeterministic set of {limit_number} cities drawn from WikiData.\n{info_manycities}")