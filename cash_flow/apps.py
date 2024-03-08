from django.apps import AppConfig


class CashflowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cash_flow'

    def ready(self):
        import cash_flow.signals
