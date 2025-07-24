# gestion/decorators.py

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect

def group_required(*group_names):
    """
    Decorador que restringe el acceso a usuarios que pertenecen a un grupo específico.
    """
    def check_perms(user):
        # Si el usuario es un superusuario, tiene acceso a todo
        if user.is_superuser:
            return True
        # Verificamos si el usuario pertenece a alguno de los grupos requeridos
        return user.groups.filter(name__in=group_names).exists()

    return user_passes_test(check_perms, login_url='/login/')

def cliente_required(user):
    # Verifica que el usuario sea autenticado y que tenga un perfil de cliente asociado.
    return user.is_authenticated and hasattr(user, 'cliente')

def cliente_access_decorator(view_func):
    """Decorador que usa user_passes_test para verificar si el usuario es un cliente."""
    decorated_view_func = user_passes_test(cliente_required, login_url='/login/')
    return decorated_view_func(view_func)