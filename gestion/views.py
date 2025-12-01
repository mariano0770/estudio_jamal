# gestion/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Cliente, Servicio, Turno, Caja, Empleado, Asistencia, Configuracion, Producto, Plan, ClientePlan, Profesional
from .forms import TurnoForm, ConfiguracionForm, EgresoForm, ClienteForm, ServicioForm, RegistroEmpleadoForm, VentaProductoForm, ProductoForm, VentaPlanForm, PlanForm, ProfesionalForm
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.utils import timezone
from django.conf import settings 
from django.contrib import messages
from django.db.models import Sum, Q
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

@login_required
def dashboard(request):
    hoy = timezone.now().date()
    turnos_hoy = Turno.objects.filter(fecha_hora_inicio__date=hoy, estado__in=['Pendiente', 'Confirmado']).order_by('fecha_hora_inicio')
    ultimos_movimientos = Caja.objects.order_by('-fecha_hora')[:5]
    
    # Calcular cuánto debemos a los profesores
    deuda_total_profes = ClientePlan.objects.filter(pagado_al_profesional=False).aggregate(total=Sum('monto_profesional'))['total'] or 0

    contexto = {
        'turnos_hoy': turnos_hoy,
        'ultimos_movimientos': ultimos_movimientos,
        'deuda_total_profes': deuda_total_profes,
    }
    return render(request, 'gestion/dashboard.html', contexto)

# --- CLIENTES ---

@login_required
def lista_clientes(request):
    query = request.GET.get('q')
    if query:
        clientes = Cliente.objects.filter(Q(nombre__icontains=query) | Q(apellido__icontains=query))
    else:
        clientes = Cliente.objects.all().order_by('apellido')
    return render(request, 'gestion/lista_clientes.html', {'clientes': clientes})

@login_required
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente creado.')
            return redirect('lista-clientes')
    else:
        form = ClienteForm()
    return render(request, 'gestion/crear_cliente.html', {'form': form})

@login_required
def detalle_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    planes_activos = ClientePlan.objects.filter(cliente=cliente).order_by('-fecha_inicio')
    return render(request, 'gestion/detalle_cliente.html', {'cliente': cliente, 'planes': planes_activos})

@login_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('detalle-cliente', cliente_id=cliente.id)
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'gestion/editar_cliente.html', {'form': form, 'cliente': cliente})

# --- PLANES Y VENTAS (Lógica Simplificada) ---

@login_required
def lista_planes(request):
    planes = Plan.objects.all()
    return render(request, 'gestion/lista_planes.html', {'planes': planes})

@login_required
def crear_plan(request):
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista-planes')
    else:
        form = PlanForm()
    return render(request, 'gestion/crear_plan.html', {'form': form})

@login_required
def vender_plan(request):
    if request.method == 'POST':
        form = VentaPlanForm(request.POST)
        if form.is_valid():
            cliente = form.cleaned_data['cliente']
            plan = form.cleaned_data['plan']

            # 1. Crear la suscripción (Esto calcula automático la deuda al profe en models.py)
            suscripcion = ClientePlan.objects.create(cliente=cliente, plan=plan)

            # 2. Registrar Ingreso Total en Caja
            Caja.objects.create(
                concepto=f"Venta Plan: {plan.nombre} - {cliente.nombre}",
                monto=plan.precio,
                tipo='Ingreso'
            )

            messages.success(request, f'Plan vendido a {cliente.nombre}. Se generó una deuda de ${suscripcion.monto_profesional} con {plan.profesional.nombre}.')
            return redirect('dashboard')
    else:
        form = VentaPlanForm()
    return render(request, 'gestion/vender_plan.html', {'form': form})

# --- PROFESIONALES Y PAGOS ---

@login_required
def lista_profesionales(request):
    profesionales = Profesional.objects.all()
    return render(request, 'gestion/lista_profesionales.html', {'profesionales': profesionales})

@login_required
def crear_profesional(request):
    if request.method == 'POST':
        form = ProfesionalForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista-profesionales')
    else:
        form = ProfesionalForm()
    return render(request, 'gestion/crear_profesional.html', {'form': form})

@login_required
def balance_profesionales(request):
    """Muestra cuánto le debemos a cada profesor por planes vendidos"""
    # Buscamos todas las ventas de planes que aun no le pagamos al profe
    deudas = ClientePlan.objects.filter(pagado_al_profesional=False).order_by('plan__profesional')
    
    total_a_pagar = deudas.aggregate(total=Sum('monto_profesional'))['total'] or 0

    return render(request, 'gestion/balance_profesionales.html', {'deudas': deudas, 'total': total_a_pagar})

@login_required
def pagar_a_profesional(request, venta_id):
    """Registra que le pagamos al profesor su parte de una venta"""
    venta = get_object_or_404(ClientePlan, id=venta_id)
    
    if request.method == 'POST':
        venta.pagado_al_profesional = True
        venta.save()

        # Sacamos la plata de la caja (Egreso)
        Caja.objects.create(
            concepto=f"Pago comisión a {venta.plan.profesional.nombre} (Plan: {venta.cliente.nombre})",
            monto=venta.monto_profesional,
            tipo='Egreso'
        )
        messages.success(request, f"Pago registrado a {venta.plan.profesional.nombre}")
    
    return redirect('balance-profesionales')

# --- CAJA Y OTROS ---

@login_required
def vista_caja(request):
    movimientos_list = Caja.objects.order_by('-fecha_hora')
    paginator = Paginator(movimientos_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    ingresos = Caja.objects.filter(tipo='Ingreso').aggregate(Sum('monto'))['monto__sum'] or 0
    egresos = Caja.objects.filter(tipo='Egreso').aggregate(Sum('monto'))['monto__sum'] or 0
    
    return render(request, 'gestion/vista_caja.html', {'page_obj': page_obj, 'balance': ingresos - egresos})

@login_required
def registrar_egreso(request):
    if request.method == 'POST':
        form = EgresoForm(request.POST)
        if form.is_valid():
            Caja.objects.create(concepto=form.cleaned_data['concepto'], monto=form.cleaned_data['monto'], tipo='Egreso')
            return redirect('vista-caja')
    else:
        form = EgresoForm()
    return render(request, 'gestion/registrar_egreso.html', {'form': form})

# --- TURNOS ---

@login_required
def lista_turnos(request):
    turnos = Turno.objects.filter(fecha_hora_inicio__gte=timezone.now()).order_by('fecha_hora_inicio')
    return render(request, 'gestion/agenda_moderna.html', {'turnos_de_hoy': turnos}) # Ajustar nombre template si hace falta

@login_required
def crear_turno(request):
    if request.method == 'POST':
        form = TurnoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Turno creado')
            return redirect('lista-turnos')
    else:
        form = TurnoForm()
    return render(request, 'gestion/crear_turno.html', {'form': form})

# --- CONFIG Y EMPLEADOS ---

@login_required
def configuracion_view(request):
    config, _ = Configuracion.objects.get_or_create(pk=1)
    if request.method == 'POST':
        form = ConfiguracionForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save()
            return redirect('configuracion')
    else:
        form = ConfiguracionForm(instance=config)
    return render(request, 'gestion/configuracion.html', {'form': form})

@login_required
def lista_empleados(request):
    empleados = Empleado.objects.all()
    return render(request, 'gestion/lista_empleados.html', {'empleados': empleados})

@login_required
def registrar_empleado(request):
    if request.method == 'POST':
        form = RegistroEmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista-empleados')
    else:
        form = RegistroEmpleadoForm()
    return render(request, 'gestion/registrar_empleado.html', {'form': form})