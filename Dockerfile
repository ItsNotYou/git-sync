FROM python:3.8-slim

RUN apt update || true
RUN apt --yes install git

WORKDIR /app

# Performance trick: install dependencies first
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -q

# Configure git to use passwords stored in ~/.git-credentials
# Make sure that your .git-credentials only use LF as linebreaks, otherwise your credentials will not be found by git!
RUN git config --global credential.helper store && mkdir /secret && ln -s /secret/.git-credentials ~/.git-credentials

# Copy everything else
COPY git_sync.py ./
COPY config.yml ./

CMD ["python", "git_sync.py"]
