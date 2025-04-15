import logging

from django.apps import AppConfig

from django.conf import settings


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        if settings.DEBUG:
            logging.basicConfig()
            logging.getLogger("apscheduler").setLevel(logging.DEBUG)

        from .jobs import scheduler

        scheduler.start()
