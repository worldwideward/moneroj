FROM python:3.12-slim

RUN apt update && apt install -y locales gettext

RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

ENV LANGUAGE=en_US:en
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

RUN groupadd -r moneroj && useradd --no-log-init -r -g moneroj moneroj

WORKDIR /src

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=moneroj:moneroj app/ app/

USER moneroj:moneroj

WORKDIR /src/app

RUN pylint \
    --rcfile="/src/app/.pylintrc" \
    /src/app

ENTRYPOINT ["gunicorn", "moneropro.wsgi:application"]
