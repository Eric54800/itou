from .base import *  # noqa

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger

ALLOWED_HOSTS = ["127.0.0.1", ".cleverapps.io"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ROOT_URLCONF = "config.urls"

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "HOST": os.environ.get("POSTGRESQL_ADDON_HOST"),
        "PORT": os.environ.get("POSTGRESQL_ADDON_PORT"),
        "NAME": os.environ.get("DEMO_APP_DB_NAME"),
        "USER": os.environ.get("POSTGRESQL_ADDON_USER"),
        "PASSWORD": os.environ.get("POSTGRESQL_ADDON_PASSWORD"),
    }
}

# Remove admin from demo env
# ------------------------------------------------------------------------------
# DJANGO_APPS.remove("django.contrib.admin")
# INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


ITOU_PROTOCOL = "https"
ITOU_FQDN = "staging.inclusion.beta.gouv.fr"
ITOU_EMAIL_CONTACT = "contact+demo@inclusion.beta.gouv.fr"
DEFAULT_FROM_EMAIL = "noreply+demo@inclusion.beta.gouv.fr"

sentry_sdk.init(dsn=os.environ["SENTRY_DSN_STAGING"], integrations=[DjangoIntegration()])
ignore_logger("django.security.DisallowedHost")
