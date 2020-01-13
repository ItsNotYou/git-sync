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


def aggressive_cleanup(path):
    """
    Removes all contents of a given directory
    """

    # Clear the readonly bit and reattempt the removal
    def remove_readonly(func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    # Try to shutil.rmtree() every item in the directory, even if it is not a directory
    for file_or_dir in os.listdir(path):
        try:
            shutil.rmtree(f"{path}/{file_or_dir}", onerror=remove_readonly)
        except OSError:
            # Ignore the errors we can't fix
            pass


def run_command(args, repo_dir, log):
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


def sync_repositories(work_dir, repo_name, git_url_1, git_url_2, report_cfg):
    with tempfile.NamedTemporaryFile(mode="w+t", prefix="git-sync-log-", suffix=".txt", delete=False) as log:
        print(f"Syncing {repo_name}, using directory {work_dir}, logging in {log.name}")

        try:
            # synchronize both repositories
            run_command(["git", "clone", "--progress", git_url_1, "."], work_dir, log)
            run_command(["git", "remote", "add", "other", git_url_2], work_dir, log)
            run_command(["git", "pull", "--progress", "other", "master"], work_dir, log)
            run_command(["git", "push", "--progress", "origin", "master"], work_dir, log)
            run_command(["git", "push", "--progress", "other", "master"], work_dir, log)
        except IOError:
            # a command went wrong, most probably a failed merge
            log.flush()
            log.seek(0)
            report_error(repo_name, work_dir, log, report_cfg)


if __name__ == "__main__":
    # load basic configuration
    with open("config.yml", "r") as yml_file:
        cfg = yaml.safe_load(yml_file)

    # load error report credentials
    with open(os.path.expanduser(cfg["email_credentials"]), "r") as credentials_file:
        report_cfg = yaml.safe_load(credentials_file)

    for repo in cfg["repositories"]:
        with tempfile.TemporaryDirectory(prefix="git-sync-") as work_dir:
            try:
                sync_repositories(work_dir, repo['name'], repo["repo1"], repo["repo2"], report_cfg)
            except:
                print("Unhandled error occurred while synchronizing", repo['name'], sys.exc_info()[0])

            # workaround for bug in TemporaryDirectory that was fixed in Python 3.9
            # see https://github.com/python/cpython/commit/e9b51c0ad81da1da11ae65840ac8b50a8521373c for details
            aggressive_cleanup(work_dir)
