import logging
import smtplib
import subprocess
from email.message import EmailMessage


def send_email(email_cfg, subject="", body=""):
    if email_cfg["email_credentials"]:
        use_sendmail(email_cfg["email_credentials"], subject, body, email_cfg["to"])
    else:
        use_mail(subject, body, email_cfg["to"])


def use_sendmail(email_cfg, subject, body, to):
    # compose email
    msg = EmailMessage()
    msg['From'] = email_cfg["from"]
    msg['To'] = to
    msg['Subject'] = subject
    msg.set_content(body)

    # create SMTP session
    s = smtplib.SMTP(email_cfg["host"], email_cfg["port"])
    try:
        s.starttls()
        s.login(email_cfg["user"], email_cfg["password"])
        s.sendmail(email_cfg["from"], email_cfg["to"], msg)
    finally:
        s.quit()


def use_mail(subject, body, to):
    logger = logging.getLogger(__name__)
    try:
        process = subprocess.run(["mail", "-s", subject, to], input=body)
        if process.returncode != 0:
            logger.error(f"Sending mail via command line failed, error code: {process.returncode}")
    except FileNotFoundError as err:
        logger.error(f"Sending mail via command line failed, error: {err}")
