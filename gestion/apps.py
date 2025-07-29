# gestion/apps.py

from django.apps import AppConfig
import os

class GestionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion'

    def ready(self):
        # Importamos las señales
        import gestion.signals

        # --- LÓGICA PARA CREAR SUPERUSUARIO EN PRODUCCIÓN ---
        # Verificamos si estamos en el entorno de Render y si el flag de creación ya se usó
        if 'RENDER' in os.environ and not os.environ.get('SUPERUSER_CREATED'):
            from django.contrib.auth import get_user_model
            User = get_user_model()

            # Verificamos si ya existe algún usuario
            if not User.objects.exists():
                username = os.environ.get('ADMIN_USER')
                email = os.environ.get('ADMIN_EMAIL')
                password = os.environ.get('ADMIN_PASS')

                if username and email and password:
                    print("Creando cuenta de superusuario...")
                    User.objects.create_superuser(username, email, password)
                    print("Superusuario creado.")
                    # Marcamos que el superusuario ya fue creado para no volver a intentarlo
                    os.environ['SUPERUSER_CREATED'] = 'True'
                else:
                    print("No se encontraron las variables de entorno para crear el superusuario.")