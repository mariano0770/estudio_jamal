



# gestion/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [    
    path('', views.dashboard, name='dashboard'),
    
    # Clientes
    path('clientes/', views.lista_clientes, name='lista-clientes'),
    path('clientes/nuevo/', views.crear_cliente, name='crear-cliente'),
    path('clientes/<int:cliente_id>/', views.detalle_cliente, name='detalle-cliente'),
    path('clientes/<int:cliente_id>/editar/', views.editar_cliente, name='editar-cliente'),
    
    # Planes y Profesionales (NUEVO FLUJO)
    path('profesionales/', views.lista_profesionales, name='lista-profesionales'),
    path('profesionales/nuevo/', views.crear_profesional, name='crear-profesional'),
    path('profesionales/balance/', views.balance_profesionales, name='balance-profesionales'),
    path('profesionales/pagar/<int:venta_id>/', views.pagar_a_profesional, name='pagar-profesional'),
    
    path('planes/', views.lista_planes, name='lista-planes'),
    path('planes/nuevo/', views.crear_plan, name='crear-plan'),
    path('planes/vender/', views.vender_plan, name='vender-plan'),
    
    # Turnos
    path('turnos/', views.lista_turnos, name='lista-turnos'),
    path('turnos/nuevo/', views.crear_turno, name='crear-turno'),
    
    # Caja
    path('caja/', views.vista_caja, name='vista-caja'),
    path('caja/nuevo_egreso/', views.registrar_egreso, name='registrar-egreso'),
    
    # Config y Auth
    path('configuracion/', views.configuracion_view, name='configuracion'),
    path('empleados/', views.lista_empleados, name='lista-empleados'),
    path('empleados/nuevo/', views.registrar_empleado, name='registrar-empleado'),
    path('login/', auth_views.LoginView.as_view(template_name='gestion/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]