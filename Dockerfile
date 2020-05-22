FROM python:3.8-slim

RUN (apt update || true) && apt --yes install git

WORKDIR /app

# Performance trick: install dependencies first
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -q

# Configure git to use passwords stored in /secret/.git-credentials and create data directory for git repositories
# Make sure that your .git-credentials only use LF as linebreaks, otherwise your credentials will not be found by git!
RUN git config --global credential.helper store \
    && mkdir /secret \
    && ln -s /secret/.git-credentials ~/.git-credentials \
    && mkdir /data \
    && mkdir /config

# Copy everything else
COPY git_sync.py ./
COPY gitsync ./gitsync

CMD python git_sync.py -vv --workdir /data --use_smtp --smtp_config /secret/.email_credentials.yml --to hgessner@uni-potsdam.de /config/*
