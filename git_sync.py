import argparse
import logging
import os.path as path
import sys

import yaml

from gitsync import sync_repository, GitError
from gitsync.reporting import send_email


def parse_arguments():
    # prepare command line parser
    # Christians Vorschläge:
    #
    # Es wäre praktisch, für alle üblichen Parameter eine Kurzform zu haben.
    #
    # Hier ist die Frage, ob du eine Logfile verwenden willst, an welche du hinten anhängst:
    #     -l --log FILE
    # Das sorgt dafür, dass man auch ohne mail die Ausgaben bekommt
    #
    # Der Parameter "repositories" ist nicht genau genug beschrieben,
    # hier ist mir unklar, wie der Pfad auszusehen hat und warum "repositories" mit -es (Mehrzahl) in den Argumenten mehrfach vorkommt.
    # Ich würde hier einfach
    #     repository
    # draus machen. (Ist Repository der richtige Begriff? Oder ist es eher der Pfad in einem Repository bzw. URL, die du angibst?)
    parser = argparse.ArgumentParser(description="Synchronize Git remotes repositories via pull and push.",
                                     epilog=("usage examples:\n"
                                             "  python git_sync.py -m hgessner@uni-potsdam.de config.yml\n"
                                             "  python git_sync.py -m hgessner@uni-potsdam.de -s smtp.yml config.yml\n"
                                             "  python git_sync.py -vvv -w /data config/*\n"
                                             "  \n"
                                             "  The above examples all use this config.yml structure:\n"
                                             "  \n"
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
    parser.add_argument("repositories", nargs="+", type=argparse.FileType("r"),
                        help=("configuration files with Git remote repositories. Each configuration file is a YAML "
                              "file. For more details on the config file structure, see the usage examples below"))

    # command line parser for email reporting
    parser.add_argument("--mail", "-m", metavar="TO",
                        help=("send error report via system 'mail' command to the specified TO address. "
                              "For connecting to an SMTP server, see --smtp"))
    parser.add_argument("--smtp", "-s", metavar="SMTP", type=argparse.FileType("r"),
                        help=("connect to an SMTP server as specified in the SMTP file instead of using "
                              "the system 'mail' command. Requires --mail. The SMTP file must contain "
                              "the SMTP server name, port and sender address. For more details on the SMTP file "
                              "structure, see the usage examples below"))

    args = parser.parse_args()

    # check parameter dependencies that ArgumentParser cannot express
    if args.smtp and not args.mail:
        parser.error("smtp: requires --mail")

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

    # prepare reporting config
    report_cfg = {
        "to": args.mail,
        "email_credentials": yaml.safe_load(args.smtp) if args.smtp else None
    }

    # load configs and add all contained repositories
    repositories = [repository for fp in args.repositories for repository in yaml.safe_load(fp)["repositories"]]

    # synchronize repositories
    error_text = []
    for repo in repositories:
        try:
            sync_repository(repo["remotes"], f"{args.workdir}/{repo['name']}")
        except GitError as err:
            logger.warning(f"Manual intervention required for {err.repo_dir}, log available at {err.log_path}")
            error_text.append(f"Manual intervention required for {err.repo_dir}. See the attached log for details.")
            error_text.append(err.log_content)

    # report errors via mail if necessary
    if error_text and args.mail:
        send_email(report_cfg, subject="git-sync error occurred", body="\n\n".join(error_text))

    # return 1 if an error occurred
    sys.exit(1 if error_text else 0)
