# gestion/tests.py

from django.test import TestCase
from .models import Cliente

class ClienteModelTest(TestCase):

    def test_puede_crear_un_cliente(self):
        """
        Prueba que un objeto Cliente se puede crear y guardar en la base de datos,
        y que su representación en string es correcta.
        """
        # 1. Crear un nuevo objeto Cliente
        cliente = Cliente.objects.create(
            nombre='Juan',
            apellido='Perez',
            email='juan.perez@example.com',
            dni='12345678'
        )

        # 2. Recuperar el cliente de la base de datos
        cliente_guardado = Cliente.objects.get(id=cliente.id)

        # 3. Hacer las "afirmaciones" (Assertions)
        # Esto es el corazón del test: verificamos que las cosas son como esperamos.
        self.assertEqual(cliente_guardado.nombre, 'Juan')
        self.assertEqual(str(cliente_guardado), 'Juan Perez')
