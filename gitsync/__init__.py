import logging
import os
import subprocess
import tempfile


class GitError(Exception):

    def __init__(self, repo_dir, log_path, log_content):
        self.repo_dir = repo_dir
        self.log_path = log_path
        self.log_content = log_content

    def __str__(self):
        return f"GitError for {self.repo_dir}, see log at {self.log_path}"


def __run_command(args, repo_dir, log):
    if isinstance(args, str):
        args = args.split(" ")

    log.write("$> " + " ".join(args) + "\n")
    log.flush()
    process = subprocess.run(args, cwd=repo_dir, stdout=log, stderr=log)
    log.write("| Return code: " + str(process.returncode) + "\n")
    if process.returncode != 0:
        raise IOError("Command failed")


def git_prepare_repository(remotes, work_dir, log):
    try:
        try:
            os.makedirs(work_dir, exist_ok=False)
            __run_command("git init", work_dir, log)
            return all([git_remote_add(index, remote, work_dir, log) for index, remote in enumerate(remotes)])
        except FileExistsError:
            __run_command("git reset --hard", work_dir, log)
            return True
    except IOError:
        return False


def git_remote_add(index, remote, work_dir, log):
    try:
        __run_command(f"git config credential.username {remote['user']}", work_dir, log)
        __run_command(f"git remote add {str(index)} {remote['url']}", work_dir, log)
        return True
    except IOError:
        return False


def git_pull(index, remote, work_dir, log):
    try:
        __run_command(f"git config credential.username {remote['user']}", work_dir, log)
        __run_command(f"git pull --progress {str(index)} master", work_dir, log)
        return True
    except IOError:
        return False


def git_push(index, remote, work_dir, log):
    try:
        __run_command(f"git config credential.username {remote['user']}", work_dir, log)
        __run_command(f"git push --progress {str(index)} master", work_dir, log)
        return True
    except IOError:
        return False


def sync_repository(remotes, work_dir, git_log=None):
    logger = logging.getLogger(__name__)

    # select given or temporary log file
    if git_log:
        log = git_log
    else:
        log = tempfile.NamedTemporaryFile(mode="w+t", prefix="git-sync-log-", suffix=".txt", delete=False)

    try:
        logger.info(f"Syncing {work_dir}, logging in {log.name}")
        log_pos = log.tell()
        log.write(f"= Syncing {work_dir}\n")

        # create the local repository if necessary
        prepare_succeeded = git_prepare_repository(remotes, work_dir, log)

        # pull from all remotes
        # a pull could fail if a remote is empty, so we have to continue with the other remotes
        pull_succeeded = [git_pull(index, remote, work_dir, log) for index, remote in enumerate(remotes)]

        # push to all remotes
        push_succeeded = [git_push(index, remote, work_dir, log) for index, remote in enumerate(remotes)]

        log.write("\n")

        # check whether a command went wrong (most probably a failed merge)
        if not prepare_succeeded or not all(pull_succeeded) or not all(push_succeeded):
            log.flush()
            log.seek(log_pos)
            raise GitError(work_dir, log.name, log.read())
    finally:
        # only close the temporary file
        if not git_log:
            log.close()
