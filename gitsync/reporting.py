import logging
import smtplib
import subprocess
from email.message import EmailMessage


def send_email(to, smtp=None, subject="", body=""):
    if smtp:
        use_sendmail(smtp, subject, body, to)
    else:
        use_mail(subject, body, to)


def use_sendmail(smtp, subject, body, to):
    # compose email
    msg = EmailMessage()
    msg['From'] = smtp["from"]
    msg['To'] = to
    msg['Subject'] = subject
    msg.set_content(body)

    # create SMTP session
    s = smtplib.SMTP(smtp["host"], smtp["port"])
    try:
        s.starttls()
        s.login(smtp["user"], smtp["password"])
        s.sendmail(smtp["from"], smtp["to"], msg)
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
