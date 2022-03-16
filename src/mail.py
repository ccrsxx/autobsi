import os
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart


def send_mail(subject, log_path, img_path, mode):
    email, api_key, target_email = mode('email'), mode('api_key'), mode('target_email')

    with open(img_path, 'rb') as raw_img, open(log_path) as raw_log:
        img = raw_img.read()
        log = raw_log.read()

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = mode('email')
    msg['To'] = mode('email')

    log = MIMEText(log)
    msg.attach(log)

    image = MIMEImage(img, name=os.path.basename(img_path))
    msg.attach(image)

    conn = smtplib.SMTP('smtp.gmail.com', 587)
    conn.ehlo()
    conn.starttls()
    conn.ehlo()
    conn.login(email, api_key)
    conn.sendmail(email, target_email, msg.as_string())
    conn.quit()
