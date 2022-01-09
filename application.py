from flask import Flask, render_template, request
from locationEntropy import just_country_info, just_city_info
# from locationEntropy import just_country_gender, just_country_age, just_country_age_gender
# from locationEntropy import just_city_gender, just_city_age, just_city_age_gender

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/calculation", methods=["POST"])
def calculation():
    known_loc = request.form.get("known_loc")
    known_gender = request.form.get("known_gender",False)
    known_age = request.form.get("known_age",False)
    known_security = request.form.get("known_security",[])
    if known_loc == "Country" and len(known_security)==0:
        if not(known_gender) and not(known_age):
            info_now = just_country_info()
        elif known_gender and not(known_age):
            info_now = just_country_gender()
        elif known_age and not(known_gender):
            info_now = just_country_age()
        else:
            info_now = just_country_age_gender()
    elif known_loc == "City" and len(known_security)==0:
        if not(known_gender) and not(known_age):
            info_now = just_city_info()
        elif known_gender and not(known_age):
            info_now = just_city_gender()
        elif known_age and not(known_gender):
            info_now = just_city_age()
        else:
            info_now = just_city_age_gender()
    elif known_loc == "State":
        return render_template("error.html")
    elif known_loc == "NoLocation":
        return render_template("error.html")
    else:
        return render_template("error.html")
    return render_template("calculation.html", info_importance=info_now)