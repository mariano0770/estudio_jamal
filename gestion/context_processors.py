# gestion/context_processors.py

from .models import Configuracion

def configuracion_global(request):
    config = None
    is_admin = False # Valor por defecto
    if request.user.is_authenticated:
        # Verificamos si el usuario es superusuario o pertenece al grupo Administrador
        is_admin = request.user.is_superuser or request.user.groups.filter(name='Administrador').exists()

    try:
        config = Configuracion.objects.get(pk=1)
    except Configuracion.DoesNotExist:
        pass

    return {'configuracion': config, 'is_admin': is_admin}