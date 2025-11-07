# jobcards/apps.py

from django.apps import AppConfig


class JobcardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobcards'

    # 🚀 CRITICAL: Add the ready method to import and register signals
    def ready(self):
        """
        Imports the signals module to ensure all signal handlers 
        (like stock adjustment) are registered when Django starts.
        """
        import jobcards.signals