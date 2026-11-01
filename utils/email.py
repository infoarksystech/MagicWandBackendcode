import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart  # This is required


def send_otp_email(email: str, otp: str):
    sender_email = "pradipbewra25@gmail.com"  # Corrected
    sender_password = "ucgb dgao puwc oyud"  # Use App Password
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    subject = "Password Reset OTP"
    body = f"Your OTP for password reset is: {otp}. It is valid for 10 minutes."

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)  # Enable debugging
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")
