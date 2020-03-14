import os
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import yaml


def send_email(email_cfg, subject, body, log):
    if "path" in email_cfg:
        # load separate error report credentials
        with open(os.path.expanduser(email_cfg["path"]), "r") as credentials_file:
            email_cfg = yaml.safe_load(credentials_file)
        use_sendmail(email_cfg, subject, body, log)
    elif "to" in email_cfg and "use_cmd" in email_cfg and email_cfg["use_cmd"]:
        # use mail on command line
        use_snail(subject, body, log, email_cfg["to"])
    else:
        # invalid configuration
        print("No valid email configuration found")


def use_sendmail(email_cfg, subject, body, log):
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


def use_snail(subject, body, log, to):
    process = os.subprocess.run(["mail", "-s", subject, "-a", log, to], input=body)
    if process.returncode != 0:
        print(f"Sending mail via command line failed, error code {process.returncode}")
