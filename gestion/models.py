# gestion/models.py

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta

class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    dni = models.CharField(max_length=20, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    fecha_alta = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
class Servicio(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_minutos = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.nombre} (${self.precio})"

class Empleado(models.Model):
    # Esto es solo para usuarios del sistema (Admin, Recepcionista)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    puesto = models.CharField(max_length=100, blank=True)
    es_dueño = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Profesional(models.Model):
    """
    Profesores externos (ej: Profe de Pilates).
    No tienen usuario de sistema, solo se usan para calcular comisiones.
    """
    nombre = models.CharField(max_length=100)
    actividad = models.CharField(max_length=100, help_text="Ej: Pilates, Yoga")
    porcentaje_centro = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=30.0,
        help_text="Porcentaje que se queda la dueña (Ej: 30%)"
    )
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.actividad})"

class Plan(models.Model):
    """
    Ahora el Plan pertenece a un Profesional.
    Ej: Plan Pilates Mensual -> Pertenece al Profe Jorge.
    """
    FRECUENCIA_CHOICES = [
        ('Semanal', 'Semanal'),
        ('Mensual', 'Mensual'),
    ]
    nombre = models.CharField(max_length=150, help_text="Ej: Pase Libre Pilates")
    profesional = models.ForeignKey(Profesional, on_delete=models.CASCADE, related_name='planes')
    servicios = models.ManyToManyField(Servicio, help_text="Servicios incluidos")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    frecuencia = models.CharField(max_length=10, choices=FRECUENCIA_CHOICES)
    sesiones_por_periodo = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.nombre} - ${self.precio} ({self.profesional.nombre})"

class ClientePlan(models.Model):
    """Suscripciones activas de los clientes"""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    fecha_inicio = models.DateField(default=timezone.now)
    fecha_fin = models.DateField()
    sesiones_usadas = models.PositiveIntegerField(default=0)
    # Guardamos cuánto le debemos al profe por esta venta específica
    monto_profesional = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pagado_al_profesional = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk:
            # Calcular fecha fin
            if self.plan.frecuencia == 'Mensual':
                self.fecha_fin = self.fecha_inicio + relativedelta(months=1)
            else:
                self.fecha_fin = self.fecha_inicio + relativedelta(weeks=1)
            
            # Calcular cuánto le toca al profesional (Precio - % del centro)
            porcentaje_profe = 100 - self.plan.profesional.porcentaje_centro
            self.monto_profesional = self.plan.precio * (porcentaje_profe / 100)
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cliente} - {self.plan.nombre}"

class Turno(models.Model):
    ESTADO_OPCIONES = [
        ('Pendiente', 'Pendiente'),
        ('Confirmado', 'Confirmado'),
        ('Cancelado', 'Cancelado'),
        ('Completado', 'Completado'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    servicio = models.ForeignKey(Servicio, on_delete=models.SET_NULL, null=True)
    # Vinculamos turno a un plan activo para descontar sesiones
    plan_usado = models.ForeignKey(ClientePlan, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_hora_inicio = models.DateTimeField()
    estado = models.CharField(max_length=10, choices=ESTADO_OPCIONES, default='Pendiente')

    def __str__(self):
        return f"Turno {self.cliente} - {self.fecha_hora_inicio}"

class Caja(models.Model):
    TIPO_MOVIMIENTO = [('Ingreso', 'Ingreso'), ('Egreso', 'Egreso')]
    fecha_hora = models.DateTimeField(default=timezone.now)
    concepto = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=7, choices=TIPO_MOVIMIENTO)

    def __str__(self):
        return f"{self.tipo}: ${self.monto} ({self.concepto})"    

class Configuracion(models.Model):
    nombre_comercio = models.CharField(max_length=100, default="Mi Centro")
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    email_remitente = models.EmailField(blank=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super(Configuracion, self).save(*args, **kwargs)

class Asistencia(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha_hora_ingreso = models.DateTimeField(default=timezone.now)

class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.nombre}"