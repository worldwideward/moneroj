# Celery Tasks

Run the tasks using the django shell (eg through cron).

```bash
python manage.py shell -c 'from tasks import celery'
```

This is a lightweight method of using Celery, without needing a separate worker instance from the beginning.
