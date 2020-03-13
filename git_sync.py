import os
import shutil
import smtplib
import stat
import subprocess
import sys
import tempfile
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import yaml


def run_command(args, repo_dir, log):
    if isinstance(args, str):
        args = args.split(" ")

    log.write("> " + " ".join(args) + "\n")
    log.flush()
    process = subprocess.run(args, cwd=repo_dir, stdout=log, stderr=log)
    log.write("| Return code: " + str(process.returncode) + "\n")
    if process.returncode != 0:
        raise IOError("Command failed")


def report_error(repo, repo_dir, log, report_cfg):
    print(f"Manual intervention required for {repo} in {repo_dir}, log below")

    subject = f"Error during git-sync for {repo}"
    body = f"Manual intervention required for {repo}. See the attached log for details."
    send_email(report_cfg, subject, body, log)


def send_email(email_cfg, subject, body, log):
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


def create_local_repository(work_dir, remotes, log):
    os.makedirs(work_dir)
    run_command("git init", work_dir, log)
    for index, remote in enumerate(remotes):
        run_command(f"git config credential.username {remote['user']}", work_dir, log)
        run_command(f"git remote add {str(index)} {remote['url']}", work_dir, log)


def push_pull_local_repository(work_dir, remotes, log):
    # pull from all remotes
    for index, remote in enumerate(remotes):
        run_command(f"git config credential.username {remote['user']}", work_dir, log)
        run_command(f"git pull --progress {str(index)} master", work_dir, log)

    # push to all remotes
    for index, remote in enumerate(remotes):
        run_command(f"git config credential.username {remote['user']}", work_dir, log)
        run_command(f"git push --progress {str(index)} master", work_dir, log)


def sync_repository(work_dir, repo_name, remotes, report_cfg):
    with tempfile.NamedTemporaryFile(mode="w+t", prefix="git-sync-log-", suffix=".txt", delete=False) as log:
        print(f"Syncing {repo_name}, using directory {work_dir}, logging in {log.name}")

        try:
            if not os.path.exists(work_dir):
                create_local_repository(work_dir, remotes, log)
            push_pull_local_repository(work_dir, remotes, log)
        except IOError:
            # a command went wrong, most probably a failed merge
            log.flush()
            log.seek(0)
            report_error(repo_name, work_dir, log, report_cfg)


def sync_repositories(work_dir, repositories_cfg, report_cfg):
    for repo in repositories_cfg:
        try:
            sync_repository(f"{work_dir}/{repo['name']}", repo['name'], repo["remotes"], report_cfg)
        except:
            print("Unhandled error occurred while synchronizing", repo['name'], sys.exc_info()[0])


if __name__ == "__main__":
    # load basic configuration
    with open("config.yml", "r") as yml_file:
        cfg = yaml.safe_load(yml_file)

    # load error report credentials
    with open(os.path.expanduser(cfg["email_credentials"]), "r") as credentials_file:
        report_cfg = yaml.safe_load(credentials_file)

    sync_repositories(cfg["work_dir"], cfg["repositories"], report_cfg)
