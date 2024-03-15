# pull official base image
#FROM python:latest

# set work directory
#WORKDIR /app
#COPY . .

#ARG requirements=requirements.txt

# set environment variables
#ENV PYTHONDONTWRITEBYTECODE 1    # Prevents Python from writing pyc files to disc
#ENV PYTHONUNBUFFERED 1           # Prevents Python from buffering stdout and stderr

#RUN apt update
#RUN apt install  bash git gcc musl-dev python3-dev libpq-dev build-essential  vim cron net-tools telnet postgresql-client  cron  -y




#RUN python -m pip install --upgrade pip setuptools wheel
#RUN pip install  --default-timeout=100 -r ${requirements}

#COPY crontab.txt /crontab.txt

#ENTRYPOINT ["/bin/bash", "runserver.sh"]


FROM python:3.11 AS builder
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    bash git gcc musl-dev python3-dev swig libpq-dev build-essential netcat-openbsd supervisor vim cron net-tools telnet postgresql-client libqpdf-dev gdal-bin neovim zsh gfortran libopenblas-dev liblapack-dev && \
    rm -rf /var/lib/apt/lists/*
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install --no-cache-dir --default-timeout=100 -r requirements.txt

FROM builder AS deployer
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . .
