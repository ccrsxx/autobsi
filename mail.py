import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from environment import *


def send_mail(subject, text, img_path, mode=get_from_config):
    logging.info('Sending attendance report...')

    with open(img_path, 'rb') as f:
        img_data = f.read()

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = mode('email')
    msg['To'] = mode('email')

    if os.path.exists(text):
        with open(text) as t:
            text = t.read()

    text = MIMEText(text)
    msg.attach(text)
    image = MIMEImage(img_data, name=os.path.basename(img_path))
    msg.attach(image)

    conn = smtplib.SMTP('smtp.gmail.com', 587)
    conn.ehlo()
    conn.starttls()
    conn.ehlo()
    conn.login(mode('email'), mode('email_app_password'))
    conn.sendmail(msg['From'], msg['To'], msg.as_string())
    conn.quit()

    logging.info(f'Attendance report sent.')
