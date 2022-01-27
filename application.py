from typing import List
from flask import Flask, render_template, request
from locationEntropy import just_country_info, just_city_info, no_location_known
# from locationEntropy import just_country_gender, just_country_age, just_country_age_gender
# from locationEntropy import just_city_gender, just_city_age, just_city_age_gender

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/calculation", methods=["POST"])
def calculation():
    known_loc : str = request.form.get("known_loc")
    known_gender : bool = request.form.get("known_gender",False)
    known_age : bool= request.form.get("known_age",False)
    known_security : List[str] = request.form.get("known_security",[])
    info_now : str = ""
    if known_loc == "Country":
        known_loc_specific : str = request.form.get("Country","All countries")
        if known_loc_specific == "All countries" and len(known_security)==0:
            if not(known_gender) and not(known_age):
                info_now = just_country_info()
            elif known_gender and not(known_age):
                return render_template("error.html")
                info_now = just_country_gender()
            elif known_age and not(known_gender):
                return render_template("error.html")
                info_now = just_country_age()
            else:
                return render_template("error.html")
                info_now = just_country_age_gender()
        else:
            return render_template("error.html")
    elif known_loc == "City":
        known_loc_specific : str = request.form.get("City","All cities")
        if known_loc_specific == "All cities" and len(known_security)==0:
            if not(known_gender) and not(known_age):
                info_now = just_city_info(None,None)
            elif known_gender and not(known_age):
                return render_template("error.html")
                info_now = just_city_gender()
            elif known_age and not(known_gender):
                return render_template("error.html")
                info_now = just_city_age()
            else:
                return render_template("error.html")
                info_now = just_city_age_gender()
        else:
            return render_template("error.html")
    elif known_loc == "State":
        return render_template("error.html")
    elif known_loc == "NoLocation":
        if len(known_security)==0:
            try:
                info_now = no_location_known(known_age,known_gender)
            except ValueError:
                return render_template("error.html")     
        else:
            return render_template("error.html")
    else:
        return render_template("error.html")
    return render_template("calculation.html", info_importance=info_now)