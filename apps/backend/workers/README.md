# workers/

Background workers for the backend.

- events_worker.py – dispatches domain events from Redis.
- 
otifications_worker.py – placeholder for notification queue processing.
- schedule_worker.py – cron-style scheduler runner.

TODO: evaluate migration to Celery or another queue backend; scripts live here to keep runtime targets in one place.
