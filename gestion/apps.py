from django.apps import AppConfig


class GestionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion'

    def ready(self):
        # Importa las señales para que se registren
        import gestion.signals
