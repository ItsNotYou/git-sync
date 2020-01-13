import os
import shutil
import stat
import subprocess
import tempfile
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
    log.write("| Return code: " + str(process.returncode))
    if process.returncode != 0:
        raise IOError("Command failed")


def report_error(repo, repo_dir, log):
    print(f"Manual intervention required for {repo} in {repo_dir}, log below")
    print()

    log.flush()
    log.seek(0)

    print(log.read())
    print()


def sync_repositories(repo_dir, repo_name, url_1, url_2):
    with tempfile.NamedTemporaryFile(mode="w+t", prefix="git-sync-log-", suffix=".txt", delete=False) as log:
        print(f"Syncing {repo_name}, using directory {repo_dir}, logging in {log.name}")

        try:
            # synchronize both repositories
            run_command(["git", "clone", "--progress", url_1, "."], repo_dir, log)
            run_command(["git", "remote", "add", "other", url_2], repo_dir, log)
            run_command(["git", "pull", "--progress", "other", "master"], repo_dir, log)
            run_command(["git", "push", "--progress", "origin", "master"], repo_dir, log)
            run_command(["git", "push", "--progress", "other", "master"], repo_dir, log)
        except IOError:
            # a command went wrong, most probably a failed merge
            report_error(repo_name, repo_dir, log)


if __name__ == "__main__":
    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)

    for repo in cfg["repositories"]:
        with tempfile.TemporaryDirectory(prefix="git-sync-") as repo_dir:
            sync_repositories(repo_dir, repo['name'], repo["repo1"], repo["repo2"])

            # workaround for bug in TemporaryDirectory that was fixed in Python 3.9
            aggressive_cleanup(repo_dir)
