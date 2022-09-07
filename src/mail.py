import os
import ssl
import smtplib

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

from typing import Callable, Any


def send_mail(
    subject: str, log_path: str, img_path: str, get: Callable[[str], Any]
) -> None:
    sender = get('email')
    api_key = get('api_key')
    receiver = get('target_email')

    message = MIMEMultipart()

    message['Subject'] = subject
    message['From'] = sender
    message['To'] = receiver

    with open(log_path) as raw_log, open(img_path, 'rb') as raw_img:
        log = raw_log.read()
        image = raw_img.read()

    log_file = MIMEText(log)
    image_file = MIMEImage(image, name=os.path.basename(img_path))

    message.attach(log_file)
    message.attach(image_file)

    text = message.as_string()

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(sender, api_key)
        server.sendmail(sender, receiver, text)
