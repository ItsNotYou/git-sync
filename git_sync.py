import yaml
import sys

from gitsync import sync_repository, GitError
from gitsync.reporting import send_email


def report_error(repo, repo_dir, log, report_cfg):
    print(f"Manual intervention required for {repo} in {repo_dir}, log below")

    subject = f"Error during git-sync for {repo}"
    body = f"Manual intervention required for {repo}. See the attached log for details."
    send_email(report_cfg, subject, body, log)


if __name__ == "__main__":
    # load basic configuration
    with open("config.yml", "r") as yml_file:
        cfg = yaml.safe_load(yml_file)

    # synchronize repositories
    work_dir = cfg["work_dir"]
    report_cfg = cfg["email_credentials"]
    for repo in cfg["repositories"]:
        try:
            sync_repository(f"{work_dir}/{repo['name']}", repo['name'], repo["remotes"])
        except GitError as err:
            print(f"Manual intervention required for {err.repo_name} in {err.repo_dir}, log below")

            subject = f"Error during git-sync for {err.repo_name}"
            body = f"Manual intervention required for {err.repo_name}. See the attached log for details."
            send_email(report_cfg, subject, body, err.log)
        except:
            print("Unhandled error occurred while synchronizing", repo['name'], sys.exc_info()[0])
