FROM python:3.11.3

RUN apt update && apt upgrade -y

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache -r requirements.txt

COPY . .
