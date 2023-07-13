FROM python:3.11.3

RUN apt update && apt upgrade -y

ENV PYTHON_ENV production
ENV OUTPUT_FOLDER /output
ENV LOGGING_LEVEL INFO
ENV HEADED false
ENV DS_EMAIL ""
ENV DS_PASSWORD ""
ENV PROXY_LIST ""

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache -r requirements.txt
RUN playwright install --with-deps firefox

COPY . .
