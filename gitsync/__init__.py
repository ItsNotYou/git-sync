import os
import subprocess
import sys
import tempfile


def run_command(args, repo_dir, log):
    if isinstance(args, str):
        args = args.split(" ")

    log.write("> " + " ".join(args) + "\n")
    log.flush()
    process = subprocess.run(args, cwd=repo_dir, stdout=log, stderr=log)
    log.write("| Return code: " + str(process.returncode) + "\n")
    if process.returncode != 0:
        raise IOError("Command failed")


def create_local_repository(work_dir, remotes, log):
    os.makedirs(work_dir)
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


def sync_repository(work_dir, repo_name, remotes, report_cfg, report_error):
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
