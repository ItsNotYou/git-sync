import argparse
import logging
import sys

import yaml

from gitsync import sync_repository, GitError
from gitsync.reporting import send_email


def parse_arguments():
    # prepare command line parser
    # Christians Vorschläge:
    #
    # - usage: git_sync.py [--verbose] [--workdir WORKING_DIRECTORY] [--mail TO [--smtp CONFIG]] repository [repository ...]
    #        git_sync.py [--help]
    # Hier sieht man, dass --smtp nur bei --mail verwendet werden kann.
    #
    # Es wäre praktisch, für alle üblichen Parameter eine Kurzform zu haben.
    #
    # -v      Verbose mode.  Causes ssh to print debugging messages about its progress.  This is
    #              helpful in debugging connection, authentication, and configuration problems.  Multiple
    #              -v options increase the verbosity.  The maximum is 3.
    #
    # Bei --workdir meinst du mit 'data' einen relativen Pfad, oder?
    # Hier wäre vielleicht besser, den Pfade nicht vom aktuellen Ort abhängig zu machen und dem Ordner einen klarer zuordenbaren Namen zu geben, z.B. '~/git_sync'.
    # Als Kurzfassung kannst du hier z.B. -w nehmen.
    #    -w --workdir
    #
    # Hier ist die Frage, ob du eine Logfile verwenden willst, an welche du hinten anhängst:
    #     -l --log FILE
    # Das sorgt dafür, dass man auch ohne mail die Ausgaben bekommt
    #
    # Ich würde statt --use_mail und --to einfach nur:
    #     -m --mail TO               send error report to recipient TO using 'mail' command
    # verwenden, du weißt dann ja, dass eine Email versendet werden soll und per default 'mail' annehmen.
    # Zusätzlich würde ich den Parameter:
    #     -s --smtp CONFIG                  send mail using 'smtp' instead of 'mail', requires --mail
    # direkt ergänzend verwenden, um den default von 'mail' auf 'smtp' zu ändern.
    # Du kannst sogar überlegen, ob du die "TO" email hier ebenfalls ablegst, dann spart man sich den --mail parameter.
    #
    # Der Parameter "repositories" ist nicht genau genug beschrieben,
    # hier ist mir unklar, wie der Pfad auszusehen hat und warum "repositories" mit -es (Mehrzahl) in den Argumenten mehrfach vorkommt.
    # Ich würde hier einfach
    #     repository
    # draus machen. (Ist Repository der richtige Begriff? Oder ist es eher der Pfad in einem Repository bzw. URL, die du angibst?)
    parser = argparse.ArgumentParser(description="Synchronize Git remotes repositories via pull and push.")
    parser.add_argument("--log", choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"], default="WARNING",
                        help="set log output level, default is 'WARNING'")
    parser.add_argument("--workdir", metavar="WORKING_DIRECTORY", default="data",
                        help="directory where the local Git repositories are stored, default is 'data'")
    parser.add_argument("repositories", nargs="+", type=argparse.FileType("r"),
                        help="remotes config files")

    # command line parser for email reporting
    mail_parser = parser.add_argument_group("email reporting", "sending reports via email is optional")
    use_mail_parser = mail_parser.add_mutually_exclusive_group()
    use_mail_parser.add_argument("--use_mail", action="store_true",
                                 help=("send error report via system 'mail' command, "
                                       "requires --to argument"))
    use_mail_parser.add_argument("--use_smtp", action="store_true",
                                 help=("send error report via SMTP server, "
                                       "requires --to and --smtp_config arguments"))
    mail_parser.add_argument("--to",
                             help="recipient email address")
    mail_parser.add_argument("--smtp_config", type=argparse.FileType("r"),
                             help="SMTP config file, containing SMTP server name, port and sender address")

    args = parser.parse_args()

    # check parameter dependencies that ArgumentParser cannot express
    if (args.use_mail or args.use_smtp) and not args.to:
        raise argparse.ArgumentTypeError("--use_mail and --use_smtp require --to argument")
    if args.use_smtp and not args.smtp_config:
        raise argparse.ArgumentTypeError("--use_smtp requires --smtp_config argument")

    return args


if __name__ == "__main__":
    args = parse_arguments()

    # set logging level
    logging.basicConfig(level=args.log)
    logger = logging.getLogger(__name__)

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
    if error_text and (args.use_mail or args.use_smtp):
        report_cfg = {
            "use_mail": args.use_mail,
            "use_smtp": args.use_smtp,
            "to": args.to,
            "email_credentials": yaml.safe_load(args.smtp_config)["email_credentials"] if args.use_smtp else None
        }
        send_email(report_cfg, subject="git-sync error occurred", body="\n\n".join(error_text))

    # return 1 if an error occurred
    sys.exit(1 if error_text else 0)
