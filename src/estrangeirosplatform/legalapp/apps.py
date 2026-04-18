from django.apps import AppConfig


class LegalappConfig(AppConfig):
    name = 'legalapp'

    def ready(self):
        # Register signal handlers.
        from . import signals  # noqa: F401

