import os
import sys

# +++++ BLOQUE DE VARIABLES DE ENTORNO CORREGIDO +++++

# Pegá aquí la clave larga y aleatoria de tu settings.py local
os.environ['SECRET_KEY'] = '30a@d^0*+@bu&$+i%!&$0k-a*l6cpi)1loim1h+a3z)#atiggs'
os.environ['DEBUG'] = 'False'

# Datos de la base de datos (verificalos en tu pestaña "Databases")
os.environ['DB_NAME'] = 'mariano0770$default'
os.environ['DB_USER'] = 'mariano0770'
os.environ['DB_PASSWORD'] = 'farma25351'
os.environ['DB_HOST'] = 'mariano0770.mysql.pythonanywhere-services.com'
os.environ['DB_PORT'] = '15432' # Revisa el puerto en la pestaña Databases, puede variar

# Datos del email
os.environ['EMAIL_HOST_USER'] = 'marianotrobo@gmail.com'
os.environ['EMAIL_HOST_PASSWORD'] = '<<TU_CONTRASEÑA_DE_APLICACIÓN_DE_16_LETRAS>>'
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# --- El resto del archivo (rutas del proyecto) ---
# Asegurate de que esta ruta sea correcta
path = '/home/mariano0770/estudio_jamal'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'centro_estetica.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()