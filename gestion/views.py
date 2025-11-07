# gestion/views.py

from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from .models import Cliente, Servicio, Turno, Abono, ClienteAbono, Caja, DeudaEmpleado, Empleado, Asistencia, Configuracion, Producto, Plan, ClientePlan, Comision
from .forms import TurnoForm, VentaAbonoForm, ConfiguracionForm, EgresoForm, ReporteFechasForm, ClienteForm, ServicioForm, RegistroEmpleadoForm, RegistroClienteForm, VentaProductoForm, ProductoForm, AdminEditarUsuarioForm, VentaPlanForm, AbonoForm, PlanForm, IngresoProfesionalForm
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.utils import timezone
from django.conf import settings 
from django.contrib import messages
from django.db.models import Sum, Q
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
import json
from django.core.paginator import Paginator
from dateutil.relativedelta import relativedelta
from .decorators import group_required, cliente_access_decorator
from django.contrib.admin.views.decorators import staff_member_required

# --- Vistas de Dashboard y Listas ---

@login_required
@staff_member_required
def dashboard(request):
    hoy = timezone.now().date()
    proxima_semana = hoy + timedelta(days=7)

    # Lógica de Cumpleaños
    cumpleanos_proximos = Cliente.objects.filter(
        fecha_nacimiento__month__gte=hoy.month,
        fecha_nacimiento__day__gte=hoy.day,
        fecha_nacimiento__month__lte=proxima_semana.month,
        fecha_nacimiento__day__lte=proxima_semana.day
    ).order_by('fecha_nacimiento__day')
    
    # Turnos para hoy
    turnos_hoy = Turno.objects.filter(fecha_hora_inicio__date=hoy, estado__in=['Pendiente', 'Confirmado']).order_by('fecha_hora_inicio')
    
    # Últimos 5 movimientos de caja
    ultimos_movimientos = Caja.objects.order_by('-fecha_hora')[:5]
    
    # Comisiones pendientes
    deudas_pendientes = DeudaEmpleado.objects.filter(estado='Pendiente')
    total_deudas_pendientes = sum(d.monto for d in deudas_pendientes)

    contexto = {
        'turnos_hoy': turnos_hoy,
        'ultimos_movimientos': ultimos_movimientos,
        'total_deudas_pendientes': total_deudas_pendientes,
        'cumpleanos_proximos': cumpleanos_proximos,
    }
    return render(request, 'gestion/dashboard.html', contexto)

@login_required
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Cliente creado exitosamente!')
            return redirect('lista-clientes')
    else:
        form = ClienteForm()
    return render(request, 'gestion/crear_cliente.html', {'form': form})

@login_required
def lista_clientes(request):
    query = request.GET.get('q')
    if query:
        clientes = Cliente.objects.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(email__icontains=query)
        ).order_by('apellido')
    else:
        clientes = Cliente.objects.all().order_by('apellido')
    contexto = {'clientes': clientes, 'query': query}
    return render(request, 'gestion/lista_clientes.html', contexto)

@login_required
def detalle_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    turnos_cliente = Turno.objects.filter(cliente=cliente).order_by('-fecha_hora_inicio')
    abonos_cliente = ClienteAbono.objects.filter(cliente=cliente).order_by('-fecha_compra')
    contexto = {'cliente': cliente, 'turnos': turnos_cliente, 'abonos': abonos_cliente}
    return render(request, 'gestion/detalle_cliente.html', contexto)

@login_required
def crear_servicio(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Servicio creado exitosamente!')
            return redirect('lista-servicios')
    else:
        form = ServicioForm()
    return render(request, 'gestion/crear_servicio.html', {'form': form})

@login_required
def lista_servicios(request):
    servicios = Servicio.objects.all()
    contexto = {'servicios': servicios}
    return render(request, 'gestion/lista_servicios.html', contexto)

@login_required
def lista_turnos(request):
    # Buscamos los turnos de hoy para la barra lateral
    hoy = timezone.now().date()
    turnos_de_hoy = Turno.objects.filter(
        fecha_hora_inicio__date=hoy,
        estado__in=['Pendiente', 'Confirmado']
    ).order_by('fecha_hora_inicio')

    config = Configuracion.objects.first()

    contexto = {
        'turnos_de_hoy': turnos_de_hoy,
        'configuracion': config,
    }
    return render(request, 'gestion/agenda_moderna.html', contexto)

@login_required
def crear_turno(request):
    if request.method == 'POST':
        form = TurnoForm(request.POST)
        if form.is_valid():
            nuevo_turno = form.save()
            config = Configuracion.objects.first()
            email_desde = config.email_remitente if config and config.email_remitente else settings.EMAIL_HOST_USER

            try:
                cliente = nuevo_turno.cliente
                asunto = f'Confirmación de tu Turno - {config.nombre_comercio if config else ""}'
                mensaje = (
                    f'Hola {cliente.nombre},\n\n'
                    f'Te confirmamos que tu turno ha sido agendado con éxito.\n\n'
                    f'Detalles del turno:\n'
                    f'- Servicio: {nuevo_turno.servicio.nombre}\n'
                    f'- Fecha y Hora: {nuevo_turno.fecha_hora_inicio.strftime("%d/%m/%Y a las %H:%M hs")}\n\n'
                    f'¡Te esperamos!'
                )
                email_para = [cliente.email]
                send_mail(asunto, mensaje, email_desde, email_para)
            except Exception as e:
                print(f"Error al enviar email: {e}")

            messages.success(request, '¡Turno agendado con éxito!')
            return redirect('lista-turnos')
    else:
        form = TurnoForm()
    return render(request, 'gestion/crear_turno.html', {'form': form})

@login_required
def editar_turno(request, turno_id):
    turno = get_object_or_404(Turno, id=turno_id)
    if request.method == 'POST':
        form = TurnoForm(request.POST, instance=turno)
        if form.is_valid():
            form.save()
            messages.success(request, 'Turno modificado correctamente.')
            return redirect('lista-turnos')
    else:
        form = TurnoForm(instance=turno)
    return render(request, 'gestion/editar_turno.html', {'form': form})

@login_required
def cancelar_turno(request, turno_id):
    turno = get_object_or_404(Turno, id=turno_id)
    if request.method == 'POST':
        turno.estado = 'Cancelado'
        turno.save()
        messages.warning(request, f'El turno de {turno.cliente.nombre} ha sido cancelado.')
        return redirect('lista-turnos')
    return render(request, 'gestion/confirmar_cancelacion.html', {'turno': turno})

# --- Vistas Financieras (Abonos, Caja, Comisiones) ---

@login_required
@staff_member_required
def vender_abono(request):
    if request.method == 'POST':
        form = VentaAbonoForm(request.POST)
        if form.is_valid():
            cliente = form.cleaned_data['cliente']
            abono = form.cleaned_data['abono']
            empleado = form.cleaned_data['empleado']

            ClienteAbono.objects.create(cliente=cliente, abono=abono)

            # Lógica de Caja/Deuda
            if empleado.es_dueño:
                # Si vende el dueño, es un ingreso directo a la caja
                Caja.objects.create(
                    concepto=f'Venta de Abono: {abono.nombre} - {cliente.nombre}',
                    monto=abono.precio,
                    tipo='Ingreso'
                )
            else:
                # Si vende un empleado, se genera una deuda para el dueño
                monto_para_dueño = abono.precio * (abono.porcentaje_dueño / 100)
                if monto_para_dueño > 0:
                    DeudaEmpleado.objects.create(
                        empleado=empleado,
                        monto=monto_para_dueño,
                        # No asociamos a un turno, sino al concepto
                        concepto_adicional=f"Venta de Abono '{abono.nombre}' a {cliente.nombre}"
                    )

            messages.success(request, f'Abono "{abono.nombre}" vendido a {cliente.nombre} exitosamente.')
            return redirect('dashboard')
    else:
        form = VentaAbonoForm()

    return render(request, 'gestion/vender_abono.html', {'form': form})

@login_required
@staff_member_required
def vista_caja(request):
    movimientos = Caja.objects.order_by('-fecha_hora')
    total_ingresos = Caja.objects.filter(tipo='Ingreso').aggregate(total=Sum('monto'))['total'] or 0
    total_egresos = Caja.objects.filter(tipo='Egreso').aggregate(total=Sum('monto'))['total'] or 0
    balance_total = total_ingresos - total_egresos
    contexto = {'movimientos': movimientos, 'balance_total': balance_total}
    return render(request, 'gestion/vista_caja.html', contexto)

@login_required
@staff_member_required
def registrar_egreso(request):
    if request.method == 'POST':
        form = EgresoForm(request.POST)
        if form.is_valid():
            Caja.objects.create(
                concepto=form.cleaned_data['concepto'],
                monto=form.cleaned_data['monto'],
                tipo='Egreso'
            )
            messages.success(request, '¡Gasto registrado exitosamente!')
            return redirect('vista-caja')
    else:
        form = EgresoForm()
    return render(request, 'gestion/registrar_egreso.html', {'form': form})

@login_required
@staff_member_required
def lista_deudas(request):
    deudas = DeudaEmpleado.objects.order_by('estado', '-fecha_generada')
    contexto = {'deudas': deudas}
    return render(request, 'gestion/lista_deudas.html', contexto)

@login_required
@staff_member_required
def pagar_deuda(request, deuda_id):
    if request.method == 'POST':
        deuda = get_object_or_404(DeudaEmpleado, id=deuda_id)

        # 1. Marcamos la deuda como pagada
        deuda.estado = 'Pagada'
        deuda.save()

        # 2. AHORA SÍ, registramos el INGRESO en la caja
        Caja.objects.create(
            concepto=f'Cobro de porcentaje a {deuda.empleado}',
            monto=deuda.monto,
            tipo='Ingreso',
            turno_asociado=deuda.turno
        )
        messages.success(request, f'Deuda de ${deuda.monto} de {deuda.empleado} registrada como pagada.')

    return redirect('lista-deudas')

# --- Vistas de Reportes y Configuración ---

@login_required
@staff_member_required
def reporte_financiero(request):
    now = datetime.now()
    movimientos_mes = Caja.objects.filter(fecha_hora__month=now.month, fecha_hora__year=now.year)
    total_ingresos = movimientos_mes.filter(tipo='Ingreso').aggregate(total=Sum('monto'))['total'] or 0
    total_egresos = movimientos_mes.filter(tipo='Egreso').aggregate(total=Sum('monto'))['total'] or 0
    balance = total_ingresos - total_egresos
    contexto = {
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'balance': balance,
        'mes_actual': now.strftime("%B de %Y")
    }
    return render(request, 'gestion/reporte_financiero.html', contexto)

@login_required
def generar_pdf_turnos_hoy(request):
    hoy = timezone.now().date()
    turnos = Turno.objects.filter(fecha_hora_inicio__date=hoy, estado__in=['Pendiente', 'Confirmado']).order_by('fecha_hora_inicio')
    contexto = {'turnos': turnos, 'hoy': hoy}
    html_string = render_to_string('gestion/pdf_turnos.html', contexto)
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="turnos_{hoy}.pdf"'
    return response

@login_required
@staff_member_required
def configuracion_view(request):
    config, created = Configuracion.objects.get_or_create(pk=1)
    if request.method == 'POST':
        form = ConfiguracionForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, '¡La configuración ha sido guardada!')
            return redirect('configuracion')
    else:
        form = ConfiguracionForm(instance=config)
    return render(request, 'gestion/configuracion.html', {'form': form})

# --- Vista Pública de Asistencia ---

def asistencia_cliente(request):
    config = Configuracion.objects.first()
    contexto = {'configuracion': config}
    if request.method == 'POST':
        dni = request.POST.get('dni')
        try:
            cliente = Cliente.objects.get(dni=dni)
            # Registramos la asistencia
            Asistencia.objects.create(cliente=cliente)

            # Buscamos su abono activo
            abono_activo = ClienteAbono.objects.filter(cliente=cliente, sesiones_restantes__gt=0).first()

            # ↓↓↓ AÑADIMOS LA BÚSQUEDA DEL PLAN ACTIVO ↓↓↓
            hoy = timezone.now().date()
            plan_activo = ClientePlan.objects.filter(
                cliente=cliente,
                fecha_inicio__lte=hoy,
                fecha_fin__gte=hoy
            ).first()

            contexto['cliente'] = cliente
            contexto['abono_activo'] = abono_activo
            contexto['plan_activo'] = plan_activo # <-- Pasamos el plan a la plantilla

        except Cliente.DoesNotExist:
            contexto['error'] = 'No se encontró ningún cliente con ese DNI. Por favor, verificá los datos.'

    return render(request, 'gestion/asistencia.html', contexto)

# --- Vistas de API para Calendario ---

@login_required
def all_turnos(request):
    turnos = Turno.objects.all()
    eventos = []
    for turno in turnos:
        if turno.estado == 'Pendiente': color = '#ffc107'
        elif turno.estado == 'Confirmado': color = '#198754'
        elif turno.estado == 'Completado': color = '#6c757d'
        else: color = '#dc3545'
        eventos.append({
            'id': turno.id,
            'title': f'{turno.cliente.nombre} - {turno.servicio.nombre}',
            'start': turno.fecha_hora_inicio.isoformat(),
            'color': color,
            'url': f'/turnos/{turno.id}/editar/'
        })
    return JsonResponse(eventos, safe=False)

@login_required
def update_turno(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            turno = Turno.objects.get(id=data.get('id'))
            turno.fecha_hora_inicio = data.get('start')
            turno.save()
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@login_required
@staff_member_required
def reportes_hub(request):
    return render(request, 'gestion/reportes_hub.html')

@login_required
@staff_member_required
def reporte_asistencias(request):
    form = ReporteFechasForm(request.GET or None)
    asistencias = None

    if form.is_valid():
        fecha_inicio = form.cleaned_data['fecha_inicio']
        fecha_fin = form.cleaned_data['fecha_fin']
        # Filtramos las asistencias en el rango de fechas
        asistencias = Asistencia.objects.filter(
            fecha_hora_ingreso__date__range=[fecha_inicio, fecha_fin]
        ).order_by('-fecha_hora_ingreso')

    contexto = {
        'form': form,
        'asistencias': asistencias
    }
    return render(request, 'gestion/reporte_asistencias.html', contexto)

@login_required
@staff_member_required
def vista_caja(request):
    # La lógica para calcular los totales no cambia
    total_ingresos = Caja.objects.filter(tipo='Ingreso').aggregate(total=Sum('monto'))['total'] or 0
    total_egresos = Caja.objects.filter(tipo='Egreso').aggregate(total=Sum('monto'))['total'] or 0
    balance_total = total_ingresos - total_egresos

    # Obtenemos la lista completa de movimientos
    movimientos_list = Caja.objects.order_by('-fecha_hora')

    # --- INICIO DE LA LÓGICA DE PAGINACIÓN ---
    # 1. Creamos el objeto Paginator, indicando que queremos 15 items por página
    paginator = Paginator(movimientos_list, 15)

    # 2. Obtenemos el número de página de la URL (ej: /caja/?page=2)
    page_number = request.GET.get('page')

    # 3. Obtenemos el objeto Page que corresponde a esa página
    page_obj = paginator.get_page(page_number)
    # --- FIN DE LA LÓGICA DE PAGINACIÓN ---

    contexto = {
        'page_obj': page_obj, # Le pasamos el objeto Page a la plantilla
        'balance_total': balance_total
    }
    return render(request, 'gestion/vista_caja.html', contexto)

@login_required
@staff_member_required
def financial_chart_data(request):
    labels = []
    income_data = []
    expense_data = []

    # Calculamos los datos para los últimos 6 meses
    for i in range(5, -1, -1):
        # Obtenemos el mes y año restando 'i' meses a la fecha actual
        date = timezone.now().date() - relativedelta(months=i)
        month_name = date.strftime("%B") # Nombre del mes en español
        labels.append(month_name.capitalize())

        # Filtramos movimientos por mes y año
        movimientos_mes = Caja.objects.filter(fecha_hora__month=date.month, fecha_hora__year=date.year)

        # Calculamos y añadimos los totales a las listas
        total_ingresos = movimientos_mes.filter(tipo='Ingreso').aggregate(total=Sum('monto'))['total'] or 0
        income_data.append(total_ingresos)

        total_egresos = movimientos_mes.filter(tipo='Egreso').aggregate(total=Sum('monto'))['total'] or 0
        expense_data.append(total_egresos)

    # Preparamos los datos para Chart.js
    data = {
        'labels': labels,
        'datasets': [
            {
                'label': 'Ingresos',
                'data': income_data,
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1
            },
            {
                'label': 'Egresos',
                'data': expense_data,
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 1
            }
        ]
    }
    return JsonResponse(data)

@login_required
@staff_member_required
def registrar_empleado(request):
    if request.method == 'POST':
        form = RegistroEmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Empleado registrado exitosamente!')
            return redirect('lista-empleados') # Redirigimos a una nueva lista de empleados
    else:
        form = RegistroEmpleadoForm()
    return render(request, 'gestion/registrar_empleado.html', {'form': form})

@login_required
@staff_member_required
def lista_empleados(request):
    empleados = Empleado.objects.all()
    return render(request, 'gestion/lista_empleados.html', {'empleados': empleados})

def registro_cliente(request):
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'¡Cuenta creada para {username}! Ahora podés iniciar sesión.')
            return redirect('login') # Lo redirigimos al login de empleados por ahora
    else:
        form = RegistroClienteForm()
    return render(request, 'gestion/registro_cliente.html', {'form': form})

@login_required
@cliente_access_decorator
def cliente_dashboard(request):
    # Obtenemos el perfil de cliente asociado al usuario logueado
    cliente = get_object_or_404(Cliente, user=request.user)

    # Buscamos sus próximos turnos (desde ahora en adelante)
    proximos_turnos = Turno.objects.filter(
        cliente=cliente, 
        fecha_hora_inicio__gte=timezone.now()
    ).order_by('fecha_hora_inicio')

    # Buscamos sus abonos activos
    abonos_activos = ClienteAbono.objects.filter(
        cliente=cliente, 
        sesiones_restantes__gt=0
    )

    contexto = {
        'cliente': cliente,
        'proximos_turnos': proximos_turnos,
        'abonos_activos': abonos_activos
    }
    return render(request, 'gestion/cliente_dashboard.html', contexto)

@login_required
@staff_member_required
def registrar_venta_producto(request):
    if request.method == 'POST':
        form = VentaProductoForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data['producto']
            cantidad = form.cleaned_data['cantidad']

            # Verificación de stock
            if producto.stock >= cantidad:
                # Actualizar stock
                producto.stock -= cantidad
                producto.save()

                # Registrar ingreso en la caja
                Caja.objects.create(
                    concepto=f'Venta de Producto: {cantidad} x {producto.nombre}',
                    monto=producto.precio * cantidad,
                    tipo='Ingreso'
                )
                messages.success(request, f'Venta de {cantidad} x {producto.nombre} registrada.')
                return redirect('vista-caja')
            else:
                # Si no hay stock suficiente, mostrar un error
                messages.error(request, f'No hay stock suficiente para vender {cantidad} unidad(es) de {producto.nombre}. Stock actual: {producto.stock}.')
    else:
        form = VentaProductoForm()

    return render(request, 'gestion/registrar_venta_producto.html', {'form': form})

@login_required
@staff_member_required
def lista_productos(request):
    query = request.GET.get('q')
    if query:
        productos = Producto.objects.filter(nombre__icontains=query).order_by('nombre')
    else:
        productos = Producto.objects.all().order_by('nombre')

    return render(request, 'gestion/lista_productos.html', {'productos': productos, 'query': query})

@login_required
@staff_member_required
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Producto creado exitosamente!')
            return redirect('lista-productos')
    else:
        form = ProductoForm()
    return render(request, 'gestion/crear_producto.html', {'form': form})

@login_required
@staff_member_required
def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('lista-productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'gestion/editar_producto.html', {'form': form})

@login_required
@staff_member_required
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        producto.delete()
        messages.warning(request, f'El producto "{producto.nombre}" ha sido eliminado.')
        return redirect('lista-productos')
    return render(request, 'gestion/confirmar_eliminacion.html', {'objeto': producto})

@login_required
def enviar_saludo_cumpleanos(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    config = Configuracion.objects.first()
    email_desde = config.email_remitente if config and config.email_remitente else settings.EMAIL_HOST_USER

    try:
        asunto = f'¡Feliz Cumpleaños, {cliente.nombre}!'
        mensaje = (
            f'Hola {cliente.nombre},\n\n'
            f'Todo el equipo de {config.nombre_comercio if config else "nuestro centro"} te desea un muy feliz cumpleaños.\n\n'
            f'¡Esperamos que tengas un día maravilloso!'
        )
        email_para = [cliente.email]

        send_mail(asunto, mensaje, email_desde, email_para)
        messages.success(request, f'¡Saludo de cumpleaños enviado a {cliente.nombre}!')
    except Exception as e:
        messages.error(request, f'Hubo un error al enviar el email: {e}')

    return redirect('dashboard')

@login_required
@staff_member_required
def lista_usuarios(request):
    # Excluimos al superusuario de la lista para no editarlo por error
    usuarios = User.objects.filter(is_superuser=False).order_by('username')
    return render(request, 'gestion/lista_usuarios.html', {'usuarios': usuarios})

@login_required
@staff_member_required
def editar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = AdminEditarUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Usuario "{usuario.username}" actualizado correctamente.')
            return redirect('lista-usuarios')
    else:
        form = AdminEditarUsuarioForm(instance=usuario)
    return render(request, 'gestion/editar_usuario.html', {'form': form, 'usuario': usuario})

@login_required
@staff_member_required
def cambiar_password(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = SetPasswordForm(usuario, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Contraseña para "{usuario.username}" cambiada exitosamente.')
            return redirect('lista-usuarios')
    else:
        form = SetPasswordForm(usuario)
    return render(request, 'gestion/cambiar_password.html', {'form': form, 'usuario': usuario})

@login_required
@staff_member_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f'Los datos de {cliente.nombre} han sido actualizados.')
            # Redirigimos de vuelta a la página de detalle del cliente
            return redirect('detalle-cliente', cliente_id=cliente.id)
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'gestion/editar_cliente.html', {'form': form, 'cliente': cliente})

@login_required
@staff_member_required
def editar_servicio(request, servicio_id):
    servicio = get_object_or_404(Servicio, id=servicio_id)
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Servicio actualizado exitosamente!')
            return redirect('lista-servicios')
    else:
        form = ServicioForm(instance=servicio)

    return render(request, 'gestion/editar_servicio.html', {'form': form, 'servicio': servicio})

@login_required
@staff_member_required
def vender_plan(request):
    if request.method == 'POST':
        form = VentaPlanForm(request.POST)
        if form.is_valid():
            cliente = form.cleaned_data['cliente']
            plan = form.cleaned_data['plan']
            empleado = form.cleaned_data['empleado']

            ClientePlan.objects.create(cliente=cliente, plan=plan)

            # Lógica de Caja/Deuda
            if empleado.es_dueño:
                Caja.objects.create(
                    concepto=f'Venta de Plan: {plan.nombre} - {cliente.nombre}',
                    monto=plan.precio,
                    tipo='Ingreso'
                )
            else:
                monto_para_dueño = plan.precio * (plan.porcentaje_dueño / 100)
                if monto_para_dueño > 0:
                    DeudaEmpleado.objects.create(
                        empleado=empleado,
                        monto=monto_para_dueño,
                        concepto_adicional=f"Venta de Plan '{plan.nombre}' a {cliente.nombre}"
                    )

            messages.success(request, f'Plan "{plan.nombre}" vendido a {cliente.nombre} exitosamente.')
            return redirect('dashboard')
    else:
        form = VentaPlanForm()

    return render(request, 'gestion/vender_plan.html', {'form': form})

@login_required
@staff_member_required
def lista_abonos(request):
    abonos = Abono.objects.all().order_by('nombre')
    return render(request, 'gestion/lista_abonos.html', {'abonos': abonos})

@login_required
@staff_member_required
def crear_abono(request):
    if request.method == 'POST':
        form = AbonoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Abono creado exitosamente!')
            return redirect('lista-abonos')
    else:
        form = AbonoForm()
    return render(request, 'gestion/crear_abono.html', {'form': form})

@login_required
@staff_member_required
def editar_abono(request, abono_id):
    abono = get_object_or_404(Abono, id=abono_id)
    if request.method == 'POST':
        form = AbonoForm(request.POST, instance=abono)
        if form.is_valid():
            form.save()
            messages.success(request, 'Abono actualizado correctamente.')
            return redirect('lista-abonos')
    else:
        form = AbonoForm(instance=abono)
    return render(request, 'gestion/editar_abono.html', {'form': form})

@login_required
@staff_member_required
def eliminar_abono(request, abono_id):
    abono = get_object_or_404(Abono, id=abono_id)
    if request.method == 'POST':
        abono.delete()
        messages.warning(request, f'El abono "{abono.nombre}" ha sido eliminado.')
        return redirect('lista-abonos')
    return render(request, 'gestion/confirmar_eliminacion.html', {'objeto': abono})

@login_required
@staff_member_required
def lista_planes(request):
    planes = Plan.objects.all().order_by('nombre')
    return render(request, 'gestion/lista_planes.html', {'planes': planes})

@login_required
@staff_member_required
def lista_planes(request):
    planes = Plan.objects.all().order_by('nombre')
    return render(request, 'gestion/lista_planes.html', {'planes': planes})

@login_required
@staff_member_required
def crear_plan(request):
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Plan/Suscripción creado exitosamente!')
            return redirect('lista-planes')
    else:
        form = PlanForm()
    return render(request, 'gestion/crear_plan.html', {'form': form})

@login_required
@staff_member_required
def editar_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    if request.method == 'POST':
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, 'Plan/Suscripción actualizado correctamente.')
            return redirect('lista-planes')
    else:
        form = PlanForm(instance=plan)
    return render(request, 'gestion/editar_plan.html', {'form': form})

@login_required
@staff_member_required
def eliminar_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    if request.method == 'POST':
        plan.delete()
        messages.warning(request, f'El plan "{plan.nombre}" ha sido eliminado.')
        return redirect('lista-planes')
    return render(request, 'gestion/confirmar_eliminacion.html', {'objeto': plan})

@login_required
@staff_member_required
def registrar_ingreso_profesional(request):
    if request.method == 'POST':
        form = IngresoProfesionalForm(request.POST)
        if form.is_valid():
            # Guardamos el formulario.
            # El modelo se encarga de:
            # 1. Calcular el 'monto_para_centro'
            # 2. Poner el 'estado_pago' en 'Pendiente'
            form.save()
            messages.success(request, '¡Deuda registrada! El profesional ahora tiene un pago pendiente.')
            return redirect('dashboard') # Redirigimos al dashboard
    else:
        form = IngresoProfesionalForm()

    return render(request, 'gestion/registrar_ingreso_profesional.html', {'form': form})

@login_required
@staff_member_required
def pagar_comision(request, comision_id):
    if request.method == 'POST':
        # (Asegurate de que 'Comision' y 'Caja' estén importados al principio del archivo)
        comision = get_object_or_404(Comision, id=comision_id)
        
        # 1. Cambiamos el estado de la comisión
        comision.estado = 'Pagada'
        comision.save()

        # 2. Creamos el egreso en la caja
        Caja.objects.create(
            concepto=f'Pago de comisión: {comision.venta_abono.abono.nombre} a {comision.venta_abono.cliente.nombre}',
            monto=comision.monto,
            tipo='Egreso'
        )
    
    # Redirigimos siempre a la lista de comisiones
    return redirect('lista-comisiones')

