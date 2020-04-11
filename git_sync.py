import os
import subprocess
import sys
import tempfile

import yaml

from send_email import send_email


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


def create_local_repository(work_dir, remotes, log):
    os.makedirs(work_dir, exist_ok=True)
    run_command("git init", work_dir, log)
    for index, remote in enumerate(remotes):
        run_command(f"git config credential.username {remote['user']}", work_dir, log)
        run_command(f"git remote add {str(index)} {remote['url']}", work_dir, log)


def push_pull_local_repository(work_dir, remotes, log):
    # pull from all remotes
    pull_failed = False
    for index, remote in enumerate(remotes):
        run_command(f"git config credential.username {remote['user']}", work_dir, log)
        try:
            run_command(f"git pull --progress {str(index)} master", work_dir, log)
        except IOError:
            pull_failed = True

    # push to all remotes
    for index, remote in enumerate(remotes):
        run_command(f"git config credential.username {remote['user']}", work_dir, log)
        run_command(f"git push --progress {str(index)} master", work_dir, log)

    if pull_failed:
        raise IOError("A pull failed")


def sync_repository(work_dir, repo_name, remotes, report_cfg):
    with tempfile.NamedTemporaryFile(mode="w+t", prefix="git-sync-log-", suffix=".txt", delete=False) as log:
        print(f"Syncing {repo_name}, using directory {work_dir}, logging in {log.name}")

        try:
            # silently create repository if it doesn't already exist
            create_local_repository(work_dir, remotes, log)
        except IOError:
            pass

        try:
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

    sync_repositories(cfg["work_dir"], cfg["repositories"], cfg["email_credentials"])
