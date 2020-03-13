FROM python:3.9-rc-buster

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
    && mkdir /data

# Copy everything else
COPY git_sync.py ./
COPY send_email.py ./

CMD ["python", "git_sync.py"]
