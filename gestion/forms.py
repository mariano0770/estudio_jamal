# gestion/forms.py
from django import forms
from django.contrib.auth.models import User, Group
from .models import Turno, Cliente, Configuracion, Servicio, Empleado, Producto, Plan, Profesional
from django.db import transaction

class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = ['cliente', 'servicio', 'fecha_hora_inicio', 'estado']
        widgets = {
            'fecha_hora_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'servicio': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

class VentaPlanForm(forms.Form):
    cliente = forms.ModelChoiceField(queryset=Cliente.objects.all(), label="Cliente", widget=forms.Select(attrs={'class': 'form-select'}))
    plan = forms.ModelChoiceField(queryset=Plan.objects.all(), label="Plan a Vender", widget=forms.Select(attrs={'class': 'form-select'}))

class ProfesionalForm(forms.ModelForm):
    class Meta:
        model = Profesional
        fields = ['nombre', 'actividad', 'porcentaje_centro']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'actividad': forms.TextInput(attrs={'class': 'form-control'}),
            'porcentaje_centro': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['nombre', 'profesional', 'precio', 'frecuencia', 'sesiones_por_periodo', 'servicios']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'profesional': forms.Select(attrs={'class': 'form-select'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'frecuencia': forms.Select(attrs={'class': 'form-select'}),
            'sesiones_por_periodo': forms.NumberInput(attrs={'class': 'form-control'}),
            'servicios': forms.CheckboxSelectMultiple,
        }

# --- Formularios Generales (Caja, Cliente, Producto, Config) ---

class EgresoForm(forms.Form):
    concepto = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    monto = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'form-control'}))

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
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
        fields = ['nombre', 'descripcion', 'precio', 'duracion_minutos']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'duracion_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
        }

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

class VentaProductoForm(forms.Form):
    producto = forms.ModelChoiceField(queryset=Producto.objects.filter(stock__gt=0), widget=forms.Select(attrs={'class': 'form-select'}))
    cantidad = forms.IntegerField(min_value=1, initial=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))

class ConfiguracionForm(forms.ModelForm):
    class Meta:
        model = Configuracion
        fields = '__all__'

# --- Registro de Usuarios (Admin/Recepcionista) ---

class RegistroEmpleadoForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Empleado
        fields = ['nombre', 'apellido', 'puesto']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'puesto': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Usuario ya existe.")
        return username

    @transaction.atomic
    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['nombre'],
            last_name=self.cleaned_data['apellido']
        )
        empleado = super().save(commit=False)
        empleado.user = user
        if commit: empleado.save()
        return empleado