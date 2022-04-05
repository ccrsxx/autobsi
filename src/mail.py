import smtplib

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from .autobsi import os, Callable


def send_mail(subject: str, log_path: str, img_path: str, get: Callable):
    email, api_key, target_email = [
        get(key) for key in ['email', 'api_key', 'target_email']
    ]

    with open(img_path, 'rb') as raw_img, open(log_path) as raw_log:
        img = raw_img.read()
        log = raw_log.read()

    msg = MIMEMultipart()

    msg['Subject'] = subject
    msg['From'] = email
    msg['To'] = target_email

    log = MIMEText(log)  # type: ignore

    msg.attach(log)  # type: ignore

    image = MIMEImage(img, name=os.path.basename(img_path))

    msg.attach(image)

    conn = smtplib.SMTP('smtp.gmail.com', 587)

    conn.ehlo()
    conn.starttls()
    conn.ehlo()
    conn.login(email, api_key)
    conn.sendmail(email, target_email, msg.as_string())
    conn.quit()
