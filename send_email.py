import os
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import yaml


def send_email(credentials_path, subject, body, log):
    # load error report credentials
    with open(os.path.expanduser(credentials_path), "r") as credentials_file:
        email_cfg = yaml.safe_load(credentials_file)

    # compose email
    msg = MIMEMultipart()
    msg['From'] = email_cfg["from"]
    msg['To'] = email_cfg["to"]
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # set attachment
    p = MIMEBase('text', 'plain')
    p.set_payload(log.read())
    p.add_header('Content-Disposition', f"attachment; filename={os.path.basename(log.name)}")
    msg.attach(p)

    # create SMTP session
    s = smtplib.SMTP(email_cfg["host"], email_cfg["port"])
    try:
        s.starttls()
        s.login(email_cfg["user"], email_cfg["password"])
        s.sendmail(email_cfg["from"], email_cfg["to"], msg.as_string())
    finally:
        s.quit()
