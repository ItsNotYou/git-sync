import argparse
import logging
import os.path as path
import sys

from gitsync import sync_repository, GitError
from gitsync.reporting import send_email
import gitsync.arghelp as arghelp


def parse_arguments():
    # prepare command line parser
    parser = argparse.ArgumentParser(description="Synchronize Git remotes repositories via pull and push.",
                                     epilog=("usage examples:\n"
                                             "  python git_sync.py -m hgessner@uni-potsdam.de config.yml\n"
                                             "  python git_sync.py -m hgessner@uni-potsdam.de -s smtp.yml config.yml\n"
                                             "  python git_sync.py -vvv -w /data config/*\n"
                                             "  \n"
                                             "  The above examples all use this config.yml structure:\n"
                                             "  \n"
                                             "  mail: optional-address@example.com\n"
                                             "  repositories:\n"
                                             "  - name: some-repository\n"
                                             "    remotes:\n"
                                             "    - url: https://github.com/ItsNotYou/git-sync.git\n"
                                             "      user: henge01@gmail.com\n"
                                             "    - url: https://gitup.uni-potsdam.de/CRC1294/Z03/git-sync.git\n"
                                             "      user: hgessner@uni-potsdam.de\n"
                                             "    - [...]\n"
                                             "  - name: some-other-repository\n"
                                             "    - [...]\n"
                                             "  \n"
                                             "  One example uses the following smtp.yml structure:\n"
                                             "  \n"
                                             "  from: sender@uni-potsdam.de\n"
                                             "  host: smtp.uni-potsdam.de\n"
                                             "  port: 587\n"
                                             "  user: sender\n"
                                             "  password: sender_password"),
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verbose", "-v", action="count", default=0,
                        help=("verbose mode prints progress messages. "
                              "Multiple -v options increase the verbosity, the maximum is 3"))
    parser.add_argument("--workdir", "-w", metavar="WORKING_DIRECTORY", default=path.expanduser("~/git-sync"),
                        help="directory where the local Git repositories are stored, default is '~/git-sync'")
    parser.add_argument("--log", "-l", metavar="FILE", type=argparse.FileType(mode="w+t"),
                        help=("log file where all 'git' input and output is written, default is one temporary file "
                              "per repository per run. git-sync truncates the log file at start"))
    parser.add_argument("--ignore-failed-push", "-f", action="store_true",
                        help=("does not create an error if a push fails. Useful if pushes get rejected regularly, "
                              "e.g. because a repository is actively worked on and receives a new push between pulls"))
    parser.add_argument("repositories", nargs="+", type=arghelp.YamlFileType(),
                        help=("one or more configuration files with Git remote repositories. Each configuration file "
                              "is a YAML file. For more details on the config file structure, see the usage examples "
                              "below"))

    # command line parser for email reporting
    parser.add_argument("--mail", "-m", metavar="TO",
                        help=("send error report via system 'mail' command to the specified TO address. "
                              "For connecting to an SMTP server, see --smtp"))
    parser.add_argument("--smtp", "-s", metavar="SMTP", type=arghelp.YamlFileType(),
                        help=("connect to an SMTP server as specified in the SMTP file instead of using "
                              "the system 'mail' command. The SMTP file must contain the SMTP server name, port and "
                              "sender address. For more details on the SMTP file structure, see the usage examples "
                              "below. Requires --mail or 'mail' field in configuration files. A --mail parameter "
                              "always overwrites the 'mail' field in a configuration file."))

    args = parser.parse_args()

    # check parameter dependencies that ArgumentParser cannot express
    for repo_cfg in args.repositories:
        if args.smtp and not args.mail and 'mail' not in repo_cfg:
            parser.error(f"smtp: requires --mail parameter or 'mail' field in configuration file")

    # select appropriate log level
    if args.verbose > 3:
        parser.error("verbose: maximum verbosity is 3")
    else:
        args.loglevel = ["ERROR", "WARNING", "INFO", "DEBUG"][args.verbose]

    return args


if __name__ == "__main__":
    args = parse_arguments()

    # set logging level
    logging.basicConfig(level=args.loglevel)
    logger = logging.getLogger(__name__)

    # synchronize repositories
    error = False
    for repo_cfg in args.repositories:
        error_text = []
        for repo in repo_cfg["repositories"]:
            try:
                sync_repository(repo["remotes"], f"{args.workdir}/{repo['name']}", git_log=args.log)
            except GitError as err:
                error = True
                logger.warning(f"Manual intervention required for {err.repo_dir}, log available at {err.log_path}")
                error_text.append(f"Manual intervention required for {err.repo_dir}. See the attached log for details.")
                error_text.append(err.log_content)

        # report errors via mail if necessary
        report_credentials = args.smtp or None
        report_to = args.mail or (repo_cfg["mail"] if "mail" in repo_cfg else None)
        if error_text and report_to:
            send_email(report_to,
                       smtp=report_credentials,
                       subject="git-sync error occurred",
                       body="\n\n".join(error_text))

    # return 1 if an error occurred
    sys.exit(1 if error else 0)
