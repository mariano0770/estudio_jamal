# gestion/forms.py
from django import forms
from django.contrib.auth.models import User, Group
from .models import Turno, Cliente, Abono, Configuracion, Servicio, Empleado, Producto, Plan
from django.db import transaction

class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = ['cliente', 'servicio', 'empleado', 'fecha_hora_inicio', 'estado']

        widgets = {
            'fecha_hora_inicio': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local', 
                    'class': 'form-control',  # <-- CORREGIDO de 'form-select' a 'form-control'
                    'step': '1800'
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'servicio': forms.Select(attrs={'class': 'form-select'}),
            'empleado': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

class VentaAbonoForm(forms.Form):
    # Creamos campos desplegables que se llenan con los datos de la base de datos
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        label="Cliente",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    abono = forms.ModelChoiceField(
        queryset=Abono.objects.all(),
        label="Tipo de Abono",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    empleado = forms.ModelChoiceField(
        queryset=Empleado.objects.all(),
        label="Vendido por",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class ConfiguracionForm(forms.ModelForm):
    class Meta:
        model = Configuracion
        fields = '__all__'

class EgresoForm(forms.Form):
    concepto = forms.CharField(
        label="Concepto del Gasto",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    monto = forms.DecimalField(
        label="Monto",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

class ReporteFechasForm(forms.Form):
    fecha_inicio = forms.DateField(
        label="Fecha de Inicio",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_fin = forms.DateField(
        label="Fecha de Fin",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        # Incluimos todos los campos excepto la fecha de alta que es automática
        fields = ['nombre', 'apellido', 'email', 'dni', 'telefono', 'fecha_nacimiento']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['nombre', 'descripcion', 'precio', 'duracion_minutos', 'porcentaje_dueño']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'duracion_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
            'porcentaje_dueño': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# gestion/forms.py

class RegistroEmpleadoForm(forms.ModelForm):
    # ... (los campos del formulario se quedan igual) ...
    username = forms.CharField(label="Nombre de Usuario", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Empleado
        fields = ['nombre', 'apellido', 'puesto']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'puesto': forms.TextInput(attrs={'class': 'form-control'}),
        }

    # ↓↓↓ AÑADIMOS ESTA VALIDACIÓN INTELIGENTE ↓↓↓
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso. Por favor, elegí otro.")
        return username

    @transaction.atomic
    def save(self, commit=True):
        # ... (el método save que ya teníamos se queda igual) ...
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['nombre'],
            last_name=self.cleaned_data['apellido']
        )

        try:
            grupo_empleado = Group.objects.get(name='Empleado')
            user.groups.add(grupo_empleado)
        except Group.DoesNotExist:
            pass

        empleado = super().save(commit=False)
        empleado.user = user

        if commit:
            empleado.save()

        return empleado
    
class RegistroClienteForm(forms.ModelForm):
    # Campos para el modelo User
    username = forms.CharField(label="Nombre de Usuario", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Contraseña", required=True, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Cliente
        # Campos del modelo Cliente
        fields = ['nombre', 'apellido', 'dni', 'telefono', 'fecha_nacimiento']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def save(self, commit=True):
        # Creamos el objeto User pero sin guardarlo aún en la BBDD
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['nombre'],
            last_name=self.cleaned_data['apellido']
        )
        # Creamos el objeto Cliente a partir del formulario
        cliente = super().save(commit=False)
        # Vinculamos el user recién creado con el cliente
        cliente.user = user

        if commit:
            cliente.save() # Guardamos el cliente (y el user se guarda por la relación)

        return cliente
    
class VentaProductoForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(stock__gt=0), # Solo mostrar productos con stock
        label="Producto",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cantidad = forms.IntegerField(
        label="Cantidad",
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio', 'stock']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class AdminEditarUsuarioForm(forms.ModelForm):
    # Hacemos que el campo de grupo sea obligatorio y lo mostramos como botones de radio
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        widget=forms.RadioSelect,
        empty_label=None,
        label="Rol / Permiso"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si el usuario ya tiene un grupo, lo preseleccionamos en el formulario
        if self.instance and self.instance.groups.exists():
            self.fields['grupo'].initial = self.instance.groups.first()

    def save(self, commit=True):
        user = super().save(commit=False)
        # Guardamos el grupo/rol seleccionado
        user.groups.set([self.cleaned_data['grupo']])
        if commit:
            user.save()
        return user
    
class VentaPlanForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        label="Cliente",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.all(),
        label="Plan / Suscripción",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    empleado = forms.ModelChoiceField(
        queryset=Empleado.objects.all(),
        label="Vendido por",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class AbonoForm(forms.ModelForm):
    class Meta:
        model = Abono
        fields = ['nombre', 'descripcion', 'precio', 'cantidad_sesiones', 'servicios']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'cantidad_sesiones': forms.NumberInput(attrs={'class': 'form-control'}),
            # Usamos checkboxes para una selección más fácil
            'servicios': forms.CheckboxSelectMultiple,
        }

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['nombre', 'servicios', 'precio', 'frecuencia', 'sesiones_por_periodo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'servicios': forms.CheckboxSelectMultiple,
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'frecuencia': forms.Select(attrs={'class': 'form-select'}),
            'sesiones_por_periodo': forms.NumberInput(attrs={'class': 'form-control'}),
        }