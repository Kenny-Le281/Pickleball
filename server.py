from flask import Flask, request, render_template_string, redirect
import json
from datetime import datetime, timedelta

app = Flask(__name__)

FORM_TEMPLATE = """
<h2>Pickleball Time Preference for {{ date }}</h2>
<form method="POST">
    <p>Do you want to play tomorrow?</p>
    <input type="radio" name="play" value="yes" required> Yes<br>
    <input type="radio" name="play" value="no"> No<br><br>

    <div id="slots" style="display:none;">
        <p>Select preferred time slots:</p>
        {% for slot in slots %}
            <input type="checkbox" name="slots" value="{{ slot }}"> {{ slot }}<br>
        {% endfor %}
    </div><br>

    <input type="submit" value="Submit">
</form>

<script>
    document.querySelectorAll("input[name='play']").forEach(radio => {
        radio.addEventListener('change', function() {
            document.getElementById("slots").style.display = (this.value === "yes") ? "block" : "none";
        });
    });
</script>
"""

@app.route("/", methods=["GET", "POST"])
def booking_form():
    date = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    slots = ["19:00 - 20:00", "20:00 - 21:00", "21:00 - 22:00", "22:00 - 23:00"]

    if request.method == "POST":
        if request.form["play"] == "yes":
            selected_slots = request.form.getlist("slots")
        else:
            selected_slots = []

        with open("priority_slots.json", "w") as f:
            json.dump({"slots": selected_slots}, f)

        return "<h3>Thank you! Your preference has been recorded.</h3>"

    return render_template_string(FORM_TEMPLATE, slots=slots, date=date)

if __name__ == "__main__":
    app.run(port=5000)
