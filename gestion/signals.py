# gestion/signals.py

from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
# La importación ahora usa DeudaEmpleado
from .models import Turno, Caja, ClienteAbono, DeudaEmpleado

# gestion/signals.py
from .models import Turno, Caja, ClienteAbono, DeudaEmpleado, ClientePlan # Importar ClientePlan

@receiver(post_save, sender=Turno)
def registrar_movimiento_turno_completado(sender, instance, **kwargs):
    if instance.estado == 'Completado':
        # Verificamos que no hayamos procesado ya este turno
        if DeudaEmpleado.objects.filter(turno=instance).exists() or Caja.objects.filter(turno_asociado=instance).exists():
            return

        cliente = instance.cliente
        servicio = instance.servicio
        hoy = timezone.now().date()

        # --- NUEVA LÓGICA DE SUSCRIPCIONES ---
        # 1. Buscamos si el cliente tiene una suscripción activa y válida para este servicio
        suscripcion_activa = ClientePlan.objects.filter(
            cliente=cliente,
            plan__servicios=servicio,
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        ).first()

        if suscripcion_activa:
            # Reseteamos el contador si ya empezó un nuevo período
            from dateutil.relativedelta import relativedelta
            periodo_pasado = False
            if suscripcion_activa.plan.frecuencia == 'Mensual' and hoy >= suscripcion_activa.fecha_fin:
                suscripcion_activa.fecha_inicio = hoy
                suscripcion_activa.fecha_fin = hoy + relativedelta(months=1)
                suscripcion_activa.sesiones_usadas = 0
                periodo_pasado = True
            elif suscripcion_activa.plan.frecuencia == 'Semanal' and hoy >= suscripcion_activa.fecha_fin:
                suscripcion_activa.fecha_inicio = hoy
                suscripcion_activa.fecha_fin = hoy + relativedelta(weeks=1)
                suscripcion_activa.sesiones_usadas = 0
                periodo_pasado = True

            # Verificamos si aún le quedan sesiones en el período
            if suscripcion_activa.sesiones_usadas < suscripcion_activa.plan.sesiones_por_periodo:
                suscripcion_activa.sesiones_usadas += 1
                suscripcion_activa.save()
                # ¡No se genera ingreso en caja ni deuda! El turno está cubierto por el plan.
                return # Terminamos la ejecución aquí

        # 2. Si no hay suscripción válida, buscamos un abono de sesiones (lógica antigua)
        abono_activo = ClienteAbono.objects.filter(
            cliente=cliente, 
            sesiones_restantes__gt=0,
            abono__servicios=servicio
        ).first()

        if abono_activo:
            abono_activo.sesiones_restantes -= 1
            abono_activo.save()
            return # El turno está cubierto por el abono

        # 3. Si no hay ni suscripción ni abono, se procesa el pago/deuda (lógica antigua)
        empleado = instance.empleado
        if not empleado: return

        if empleado.es_dueño:
            Caja.objects.create(
                concepto=f'Ingreso por servicio propio: {servicio.nombre}',
                monto=servicio.precio,
                tipo='Ingreso',
                turno_asociado=instance
            )
        else:
            monto_para_dueño = servicio.precio * (servicio.porcentaje_dueño / 100)
            if monto_para_dueño > 0:
                DeudaEmpleado.objects.create(
                    empleado=empleado,
                    turno=instance,
                    monto=monto_para_dueño,
                    estado='Pendiente'
                )