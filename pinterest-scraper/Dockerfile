FROM python:3.11.5

ENV PYTHON_ENV=production

# install telnet
RUN apt-get update && apt-get install telnet -y

WORKDIR /usr/src/app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install firefox && \
    playwright install-deps

COPY . .
