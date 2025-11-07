# gestion/admin.py

from django.contrib import admin
# La importación ahora usa DeudaEmpleado en lugar de Comision
from .models import (
    Cliente, Servicio, Turno, Abono, 
    ClienteAbono, Caja, DeudaEmpleado, Empleado, 
    Asistencia, Configuracion, Producto, Plan, ClientePlan, Profesional, IngresoProfesional
)

class AbonoAdmin(admin.ModelAdmin):
    filter_horizontal = ('servicios',)

class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'stock')
    search_fields = ('nombre',)

# Registramos todos los modelos
admin.site.register(Cliente)
admin.site.register(Servicio)
admin.site.register(Turno)
admin.site.register(Abono, AbonoAdmin) 
admin.site.register(ClienteAbono)
admin.site.register(Plan)
admin.site.register(ClientePlan)
admin.site.register(Caja)
admin.site.register(DeudaEmpleado) 
admin.site.register(Empleado)
admin.site.register(Asistencia)
admin.site.register(Configuracion)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Profesional)
admin.site.register(IngresoProfesional)


