FROM python:3.11.5-alpine

ENV PYTHON_ENV=production

# install telnet
RUN apk add busybox-extras

WORKDIR /usr/src/app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .