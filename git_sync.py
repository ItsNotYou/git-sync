import yaml

from gitsync import sync_repository
from gitsync.reporting import send_email


def report_error(repo, repo_dir, log, report_cfg):
    print(f"Manual intervention required for {repo} in {repo_dir}, log below")

    subject = f"Error during git-sync for {repo}"
    body = f"Manual intervention required for {repo}. See the attached log for details."
    send_email(report_cfg, subject, body, log)


def sync_repositories(work_dir, repositories_cfg, report_cfg):
    for repo in repositories_cfg:
        try:
            sync_repository(f"{work_dir}/{repo['name']}", repo['name'], repo["remotes"], report_cfg, report_error)
        except:
            print("Unhandled error occurred while synchronizing", repo['name'], sys.exc_info()[0])


if __name__ == "__main__":
    # load basic configuration
    with open("config.yml", "r") as yml_file:
        cfg = yaml.safe_load(yml_file)

    sync_repositories(cfg["work_dir"], cfg["repositories"], cfg["email_credentials"])
