# git-sync keeps Git repositories in sync
git-sync pulls and pushes the latest `master`branch changes between two or more Git repositories. If it runs into a problem, it can send you an email with the repository name and an error report. git-sync supports multiple repositories and different users per repository. The script runs on Windows as well as Linux (and probably macOS, too).

The [CRC 1294 "Data Assimilation"](https://www.sfb1294.de/) developed git-sync as a tool to synchronize Overleaf projects with our institutional GitLab server, but it can be used on any Git repositories. You can run git-sync from your working machine, it doesn't need to be configured at the Git server (unlike [git-mirror](https://www.ralfj.de/projects/git-mirror/)).

## What does it do
git-sync basically runs the following commands.
```
git init . <or> git reset --hard

for each repository:
  git pull --progress <index> master
  git push --progress <index> master
```
If a run fails (most likely because the repositories could not be merged), git-sync can send you an email. In practice, there are more commands that get executed, see "Why not just run git pull / git push" below.

## Installation
The script requires Python 3.6+ and Git.

1. Download the files and run `pip install -r requirements.txt`
2. Create a `config.yml` (see usage examples below)
3. Configure your Git to access the repositories without user interaction (see configuration below)
4. Run git-sync with `python git_sync.py <your options>` (see usage examples below)

## How to configure your Git to access the repositories without user interaction
These commands give a fast overview. For more details, see https://git-scm.com/docs/gitcredentials and https://git-scm.com/docs/git-credential-store

```shell
$ git config credential.helper store
$ git push https://example.com/repo.git
Username: <type your username>
Password: <type your password>

[several days later]
$ git push http://example.com/repo.git
[your credentials are used automatically]
```

## How to use it
git-sync uses a command line interface and a configuration file to know what to keep in sync. A full usage description is printed when running `python git_sync.py -h`. This also includes usage examples.

git-sync expects Git to handle all login data. It will not touch your Git login credentials. If you want to run git-sync without supervision, take a look at https://git-scm.com/docs/git-credential-store to learn how Git manages your login credentials.

```
usage: git_sync.py [-h] [--verbose] [--workdir WORKING_DIRECTORY] [--log FILE] [--mail TO] [--smtp SMTP] repositories [repositories ...]

Synchronize Git remotes repositories via pull and push.

positional arguments:
  repositories          one or more configuration files with Git remote repositories. Each configuration file is a YAML file. For more details on the config file structure, see the usage examples below

optional arguments:
  -h, --help            show this help message and exit
  --verbose, -v         verbose mode prints progress messages. Multiple -v options increase the verbosity, the maximum is 3
  --workdir WORKING_DIRECTORY, -w WORKING_DIRECTORY
                        directory where the local Git repositories are stored, default is '~/git-sync'
  --log FILE, -l FILE   log file where all 'git' input and output is written, default is one temporary file per repository per run. git-sync truncates the log file at start
  --mail TO, -m TO      send error report via system 'mail' command to the specified TO address. For connecting to an SMTP server, see --smtp
  --smtp SMTP, -s SMTP  connect to an SMTP server as specified in the SMTP file instead of using the system 'mail' command. The SMTP file must contain the SMTP server name, port and sender address. For more details on the SMTP file structure, see the usage examples below. Requires
                        --mail or 'mail' field in configuration files. A --mail parameter always overwrites the 'mail' field in a configuration file.

usage examples:
  python git_sync.py -m hgessner@uni-potsdam.de config.yml
  python git_sync.py -m hgessner@uni-potsdam.de -s smtp.yml config.yml
  python git_sync.py -vvv -w /data config/*

  The above examples all use this config.yml structure:

  mail: optional-address@example.com
  repositories:
  - name: some-repository
    remotes:
    - url: https://github.com/ItsNotYou/git-sync.git
      user: henge01@gmail.com
    - url: https://gitup.uni-potsdam.de/CRC1294/Z03/git-sync.git
      user: hgessner@uni-potsdam.de
    - [...]
  - name: some-other-repository
    - [...]

  One example uses the following smtp.yml structure:

  from: sender@uni-potsdam.de
  host: smtp.uni-potsdam.de
  port: 587
  user: sender
  password: sender_password
```

## Why not just run git pull / git push
We started with a simple script that only did `git pull` and `git push`. However, over time we discovered several pitfalls that required more and more commands and better error handling. This included email sending on Windows (where "mail" is not available), different user accounts for Overleaf and GitLab and recovering from merge conflicts. This eventually developed into git-sync, which is still in active use today.

## Limitations
git-sync only keeps the master branch in sync. Overleaf only supports the master branch, so we don't need more than that.
