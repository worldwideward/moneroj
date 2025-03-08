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
