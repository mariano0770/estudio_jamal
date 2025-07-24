# gestion/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings         
from django.conf.urls.static import static 

urlpatterns = [    
    # Cuando alguien visite la raíz de nuestra app, se ejecutará la vista 'lista_clientes'
    path('registro/', views.registro_cliente, name='registro-cliente'),
    path('mi-cuenta/', views.cliente_dashboard, name='cliente_dashboard'),
    path('', views.dashboard, name='dashboard'), 
    path('asistencia/', views.asistencia_cliente, name='asistencia-cliente'),
    path('clientes/', views.lista_clientes, name='lista-clientes'),
    path('clientes/nuevo/', views.crear_cliente, name='crear-cliente'),
    path('clientes/<int:cliente_id>/', views.detalle_cliente, name='detalle-cliente'),
    path('clientes/<int:cliente_id>/editar/', views.editar_cliente, name='editar-cliente'),
    path('clientes/<int:cliente_id>/saludo/', views.enviar_saludo_cumpleanos, name='enviar-saludo'), 
    path('servicios/', views.lista_servicios, name='lista-servicios'),
    path('servicios/nuevo/', views.crear_servicio, name='crear-servicio'),
    path('servicios/<int:servicio_id>/editar/', views.editar_servicio, name='editar-servicio'),
    path('turnos/', views.lista_turnos, name='lista-turnos'),
    path('turnos/nuevo/', views.crear_turno, name='crear-turno'),
    path('turnos/<int:turno_id>/editar/', views.editar_turno, name='editar-turno'),
    path('turnos/<int:turno_id>/cancelar/', views.cancelar_turno, name='cancelar-turno'),
    path('turnos/reporte_hoy/', views.generar_pdf_turnos_hoy, name='reporte-turnos-hoy'),
    path('abonos/vender/', views.vender_abono, name='vender-abono'),
    path('deudas/', views.lista_deudas, name='lista-deudas'),
    path('deudas/<int:deuda_id>/pagar/', views.pagar_deuda, name='pagar-deuda'),
    path('reportes/', views.reportes_hub, name='reportes-hub'),
    path('reportes/financiero/', views.reporte_financiero, name='reporte-financiero'),
    path('reportes/asistencias/', views.reporte_asistencias, name='reporte-asistencias'),
    path('caja/', views.vista_caja, name='vista-caja'),
    path('productos/', views.lista_productos, name='lista-productos'),
    path('productos/nuevo/', views.crear_producto, name='crear-producto'),
    path('productos/<int:producto_id>/editar/', views.editar_producto, name='editar-producto'),
    path('productos/<int:producto_id>/eliminar/', views.eliminar_producto, name='eliminar-producto'),
    path('configuracion/', views.configuracion_view, name='configuracion'),
    path('empleados/', views.lista_empleados, name='lista-empleados'),
    path('empleados/nuevo/', views.registrar_empleado, name='registrar-empleado'),
    path('login/', auth_views.LoginView.as_view(template_name='gestion/login.html'), name='login'),
    path('caja/nuevo_egreso/', views.registrar_egreso, name='registrar-egreso'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/turnos/', views.all_turnos, name='api-all-turnos'),
    path('api/turnos/update/', views.update_turno, name='api-update-turno'),
    path('api/chart/financial_summary/', views.financial_chart_data, name='api-financial-chart'),
    path('productos/vender/', views.registrar_venta_producto, name='registrar-venta-producto'),
    path('usuarios/', views.lista_usuarios, name='lista-usuarios'),
    path('usuarios/<int:user_id>/editar/', views.editar_usuario, name='editar-usuario'),
    path('usuarios/<int:user_id>/password/', views.cambiar_password, name='cambiar-password'),
    path('planes/vender/', views.vender_plan, name='vender-plan'),
    path('abonos/', views.lista_abonos, name='lista-abonos'),
    path('abonos/nuevo/', views.crear_abono, name='crear-abono'),
    path('abonos/<int:abono_id>/editar/', views.editar_abono, name='editar-abono'),
    path('abonos/<int:abono_id>/eliminar/', views.eliminar_abono, name='eliminar-abono'),
    path('planes/', views.lista_planes, name='lista-planes'),
    path('planes/nuevo/', views.crear_plan, name='crear-plan'),
    path('planes/<int:plan_id>/editar/', views.editar_plan, name='editar-plan'),
    path('planes/<int:plan_id>/eliminar/', views.eliminar_plan, name='eliminar-plan'),
]



