# wallets/apps.py
from django.apps import AppConfig

class WalletsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wallets'

    def ready(self):
        # This line is crucial to ensure the signals are registered when the app starts.
        import wallets.signals