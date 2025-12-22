from celery import Celery

from .. import config

celery_app = Celery(
	"worker",
	broker=config.settings.CELERY_BROKER_URL,
	backend=config.settings.CELERY_BACKEND_URL
)

celery_app.conf.timezone=config.settings.CELERY_TIMEZONE