import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg["Subject"] = "Pickleball Reservation For Tomorrow"
msg["From"] = "kle@gestionzagora.com"
msg["To"] = "kle@gestionzagora.com"

msg.set_content("""Hi Tommy,

Do you want to play Pickleball tomorrow?

👉 Click to submit your time preference:
http://127.0.0.1:5000

Thanks!
""")

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    smtp.login("kle@gestionzagora.com", "jesrndkrngjosqbf")
    smtp.send_message(msg)
