# Moneropro

## Initial setup

```bash
# on the host
mkdir data
docker run --rm \
    -v ./app:/src/app \
    -v ./data:/opt \
    -p 8080:8000 moneropro

# in the container
python manage.py makemigrations
python manage.py makemigrations charts
python manage.py migrate

python manage.py createsuperuser
```

## Code quality

To ensure optimal code quality, the code should be linted with pylint.

```bash
pylint --rcfile="/src/app/.pylintrc" /src/app
```
#!/bin/bash

## Unit tests

We use [django's testsframework](https://docs.djangoproject.com/en/3.1/topics/testing/overview/) (based on unittest of the python standard library).

Run tests like

```bash
python manage.py test --failfast charts.asynchronous_test
```

# Data updates

Save this job as a script, eg named `$HOME/cron/coin_updates`

```bash
ts=$(date +%d%m%YT%H%M%S)

docker exec -t moneroj-django-1 python manage.py shell -c 'from tasks import celery' > $ts-data-sync.log
```

Schedule this script using crontab for daily coin updates:

```bash
# m h  dom mon dow   command
  0 */8  *   *   *   ~/cron/coin_updates.sh
```

