# gestion/models.py

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

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
    porcentaje_dueño = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.nombre} (${self.precio})"

class Empleado(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    puesto = models.CharField(max_length=100, blank=True)
    fecha_contratacion = models.DateField(default=timezone.now)
    es_dueño = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Turno(models.Model):
    ESTADO_OPCIONES = [
        ('Pendiente', 'Pendiente'),
        ('Confirmado', 'Confirmado'),
        ('Cancelado', 'Cancelado'),
        ('Completado', 'Completado'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    servicio = models.ForeignKey(Servicio, on_delete=models.SET_NULL, null=True)
    empleado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_hora_inicio = models.DateTimeField()
    estado = models.CharField(max_length=10, choices=ESTADO_OPCIONES, default='Pendiente')

    def __str__(self):
        # Formateamos la fecha para que se vea más amigable
        fecha_formateada = self.fecha_hora_inicio.strftime("%d/%m/%Y a las %H:%M hs")
        return f"Turno de {self.cliente.nombre} para {self.servicio.nombre} - {fecha_formateada}"

class Abono(models.Model):
    """Define un tipo de paquete de servicios que se puede vender."""
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_sesiones = models.PositiveIntegerField()
    servicios = models.ManyToManyField(Servicio, related_name='abonos')
    porcentaje_dueño = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Porcentaje del precio de venta que corresponde al dueño.")
      
    def __str__(self):
        return f"{self.nombre} ({self.cantidad_sesiones} sesiones)"

class ClienteAbono(models.Model):
    """Registra la compra de un abono por parte de un cliente."""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    abono = models.ForeignKey(Abono, on_delete=models.CASCADE)
    fecha_compra = models.DateField(default=timezone.now)
    sesiones_restantes = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        # Si es la primera vez que se guarda, se asignan las sesiones del abono.
        if self.pk is None:
            self.sesiones_restantes = self.abono.cantidad_sesiones
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Abono de {self.cliente} - {self.abono.nombre} ({self.sesiones_restantes} restantes)"

class Caja(models.Model):
    """Registra todos los movimientos de dinero."""
    TIPO_MOVIMIENTO = [
        ('Ingreso', 'Ingreso'),
        ('Egreso', 'Egreso'),
    ]
    fecha_hora = models.DateTimeField(default=timezone.now)
    concepto = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=7, choices=TIPO_MOVIMIENTO)

    # Este campo es opcional, para vincular un pago a un turno específico.
    turno_asociado = models.ForeignKey(Turno, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.fecha_hora.strftime('%d/%m/%Y %H:%M')} - {self.tipo}: ${self.monto} ({self.concepto})"    

class DeudaEmpleado(models.Model):
    """Registra el dinero que un empleado le debe al dueño."""
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente de Pago'),
        ('Pagada', 'Pagada'),
    ]

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE)
    concepto_adicional = models.CharField(max_length=255, blank=True, null=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_generada = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Pendiente')

    def __str__(self):
        return f"Deuda de {self.empleado} por turno del {self.turno.fecha_hora_inicio.strftime('%d/%m/%y')}"

    class Meta:
        verbose_name_plural = "Deudas de Empleados"
    
class Configuracion(models.Model):
    nombre_comercio = models.CharField(max_length=100, default="Mi Centro de Estética")
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    email_remitente = models.EmailField(blank=True, help_text="Email desde donde se enviarán las notificaciones.")

    # Campos para configuración de SMTP (para el futuro)
    email_host = models.CharField(max_length=100, blank=True)
    email_port = models.PositiveIntegerField(null=True, blank=True)
    email_user = models.CharField(max_length=100, blank=True)
    email_password = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return "Configuración del Sitio"

    # Con esto nos aseguramos de que solo haya una fila de configuración en la BBDD
    def save(self, *args, **kwargs):
        self.pk = 1
        super(Configuracion, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Configuración"

class Asistencia(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha_hora_ingreso = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Asistencia de {self.cliente} - {self.fecha_hora_ingreso.strftime('%d/%m/%Y %H:%M')}"
    
class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0, help_text="Cantidad actual en inventario")

    def __str__(self):
        return f"{self.nombre} (${self.precio})"

    class Meta:
        verbose_name_plural = "Productos"

class Plan(models.Model):
    FRECUENCIA_CHOICES = [
        ('Semanal', 'Semanal'),
        ('Mensual', 'Mensual'),
    ]
    nombre = models.CharField(max_length=150, help_text="Ej: Plan Pilates Mensual")
    servicios = models.ManyToManyField(Servicio, help_text="¿Qué servicios incluye este plan?")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    frecuencia = models.CharField(max_length=10, choices=FRECUENCIA_CHOICES)
    sesiones_por_periodo = models.PositiveIntegerField(help_text="¿Cuántas clases puede tomar por semana/mes?")
    porcentaje_dueño = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Porcentaje del precio de venta que corresponde al dueño.")

    def __str__(self):
        return f"{self.nombre} ({self.sesiones_por_periodo} sesiones por {self.frecuencia.lower()})"

class ClientePlan(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    fecha_inicio = models.DateField(default=timezone.now)
    fecha_fin = models.DateField()
    sesiones_usadas = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        # Calculamos la fecha de fin automáticamente al guardar
        if not self.pk: # Solo si es un objeto nuevo
            from dateutil.relativedelta import relativedelta
            if self.plan.frecuencia == 'Mensual':
                self.fecha_fin = self.fecha_inicio + relativedelta(months=1)
            else: # Semanal
                self.fecha_fin = self.fecha_inicio + relativedelta(weeks=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Suscripción de {self.cliente} al {self.plan.nombre}"