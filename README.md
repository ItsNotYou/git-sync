# git-sync
Synchronizes the `master` between branch two Git repositories. Sends a mail on error (usually caused by a failed merge). The script runs on Windows as well as Linux (and probably macOS, too).

We use this script to regularly synchronize between a GitLab and an Overleaf instance.

## Running the script
The script requires Python 3.x and Git.

Step 1: Configure the repositories under `config.yml`
```yaml
email_credentials: ~/.email_credentials.yml
repositories:
  - name: human_readable_name
    repo1: https://path_to_first_repository.git
    repo2: https://path_to_second_repository.git
```

Step 2: Configure the email credentials in `~/.email_credentials.yml` (the file `.email_credentials.yml` in your home directory).
```yaml
from: sender@example.com
to: receiver@example.com
host: smtp.example.com
port: 587
user: sender_account
password: sender_password
```

Step 3: Configure your Git to access the repositories without user interaction. For details see https://git-scm.com/docs/gitcredentials and https://git-scm.com/docs/git-credential-store
```shell
$ git config credential.helper store
$ git push https://example.com/repo.git
Username: <type your username>
Password: <type your password>

[several days later]
$ git push http://example.com/repo.git
[your credentials are used automatically]
```

Install packages from `requirements.txt` and run the script.
```
pip install -r requirements.txt
python git_sync.py
```
