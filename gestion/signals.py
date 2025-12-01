# gestion/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Cliente

# Esta señal sirve para que si creas un User desde el panel de Admin,
# se intente crear un Cliente automáticamente.
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        # Si el usuario es superusuario o staff, no hacemos nada obligatorio
        if not (instance.is_staff or instance.is_superuser):
            # Si es un usuario normal, verificamos que no tenga ya un cliente asignado
            if not hasattr(instance, 'cliente'):
                Cliente.objects.create(
                    user=instance,
                    nombre=instance.first_name,
                    apellido=instance.last_name,
                    email=instance.email
                )