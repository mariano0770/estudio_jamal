# gestion/admin.py
from django.contrib import admin
from .models import (
    Cliente, 
    Servicio, 
    Turno, 
    Caja, 
    Configuracion, 
    Empleado, 
    Producto, 
    Plan, 
    ClientePlan,
    Profesional,
    Asistencia
)

# Registramos los modelos para que aparezcan en el panel de admin
admin.site.register(Cliente)
admin.site.register(Servicio)
admin.site.register(Turno)
admin.site.register(Caja)
admin.site.register(Configuracion)
admin.site.register(Empleado)
admin.site.register(Producto)
admin.site.register(Asistencia)

# Nuevos modelos de la lógica simplificada
admin.site.register(Profesional)
admin.site.register(Plan)
admin.site.register(ClientePlan)


