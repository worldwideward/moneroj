FROM python:3.12-slim

RUN apt update && apt install -y locales

RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

ENV LANGUAGE=en_US:en
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

WORKDIR src

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY app/ app/

WORKDIR /src/app

CMD ["gunicorn", "moneropro.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "8"]
