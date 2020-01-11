import os
import shutil
import stat
import subprocess
import tempfile
import yaml


def remove_readonly(func, path, _):
    # Clear the readonly bit and reattempt the removal
    os.chmod(path, stat.S_IWRITE)
    func(path)


def run_command(args, repo_dir):
    print(">", " ".join(args))
    process = subprocess.run(args, cwd=repo_dir)
    print("Exit code", process.returncode)


if __name__ == "__main__":
    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)

    work_dir = cfg["work_directory"]
    if not work_dir.endswith("/"):
        work_dir += "/"

    for repo in cfg["repositories"]:
        with tempfile.TemporaryDirectory(prefix="git-sync-") as repo_dir:
            print(f"Syncing {repo['name']}, using directory {repo_dir}")

            # synchronize both repositories
            run_command(["git", "clone", "--progress", repo["repo1"], "."], repo_dir)
            run_command(["git", "remote", "add", "other", repo["repo2"]], repo_dir)
            run_command(["git", "pull", "--progress", "other", "master"], repo_dir)
            run_command(["git", "push", "--progress", "origin", "master"], repo_dir)
            run_command(["git", "push", "--progress", "other", "master"], repo_dir)

            for file_or_dir in os.listdir(repo_dir):
                try:
                    shutil.rmtree(f"{repo_dir}/{file_or_dir}", onerror=remove_readonly)
                except OSError:
                    pass
