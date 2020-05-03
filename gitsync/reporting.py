import logging
import os
import smtplib
import subprocess
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(email_cfg, subject="", body="", log=None):
    logger = logging.getLogger(__name__)

    if email_cfg.use_mail:
        use_snail(subject, body, log, email_cfg["to"])
    elif email_cfg.use_smtp:
        use_sendmail(email_cfg["email_credentials"], subject, body, log, email_cfg["to"])
    else:
        logger.info("No email reporting selected")


def use_sendmail(email_cfg, subject, body, log, to):
    # compose email
    msg = MIMEMultipart()
    msg['From'] = email_cfg["from"]
    msg['To'] = to
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
    process = subprocess.run(["mail", "-s", subject, "-a", log.name, to], input=body)
    if process.returncode != 0:
        logger = logging.getLogger(__name__)
        logger.error(f"Sending mail via command line failed, error code {process.returncode}")
