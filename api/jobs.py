from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from django_apscheduler import util

from api.models import Contest


scheduler = BackgroundScheduler()


@scheduler.scheduled_job("interval", seconds=15)
@util.close_old_connections
def check_contests_status():
    """
    Check contests that have ended and update their state to CHECKING.
    Runs every minute to find contests where:
    - current state is IN_PROGRESS
    - end_datetime has been reached
    """
    Contest.objects.filter(
        stage=Contest.Stages.IN_PROGRESS, end_datetime__lte=timezone.now()
    ).update(stage=Contest.Stages.CHECKING)
