from app import app, bcrypt
from config import db
from models import Usuario, Rol, Categoria, Empleado, Producto, Inventario, Transaccion, Laboratorios, Cliente
from datetime import datetime

def init_db():
    with app.app_context():
        # Elimina la base de datos existente y crea una nueva
        db.drop_all()
        db.create_all()
        
        # **1. Insertar Roles**
        rol_admin = Rol(rol_usuario='administrador', descripcion='Tiene acceso total al sistema.')
        rol_empleado = Rol(rol_usuario='empleado', descripcion='Acceso restringido para ventas y gestión de productos.')
        db.session.add_all([rol_admin, rol_empleado])
        db.session.commit()

        # **2. Insertar Usuarios**
        usuario_admin = Usuario(
            usuario="admin",
            contraseña=bcrypt.generate_password_hash("admin123"),
            rol_FK=rol_admin.rol_ID,
            email="jberriotorrado@gmail.com" 
        )
        usuario_empleado = Usuario(
            usuario="empleado",
            contraseña=bcrypt.generate_password_hash("empleado123"),
            rol_FK=rol_empleado.rol_ID
        )
        db.session.add_all([usuario_admin, usuario_empleado])
        db.session.commit()

        # **3. Insertar Categorías**
        categoria_medicamentos = Categoria(nombre_categoria="Medicamentos", descripcion="Fármacos y tratamientos médicos.")
        categoria_cuidado = Categoria(nombre_categoria="Cuidado personal", descripcion="Productos para higiene y cuidado.")
        db.session.add_all([categoria_medicamentos, categoria_cuidado])
        db.session.commit()

        # **4. Insertar Empleados**
        empleado1 = Empleado(
            usuario_FK=usuario_empleado.usuario_ID,
            nombre1="Carlos",
            apellido1="Pérez",
            direccion="Calle 123",
            documento_identificacion="123456789",
            email="carlos@email.com",
            telefono="3216549870",
            fecha_contratacion=datetime(2024, 1, 10),
            estado="activo"
        )
        db.session.add(empleado1)
        db.session.commit()

        # **5. Insertar Productos**
        producto1 = Producto(
            categoria_FK=categoria_medicamentos.categoria_ID,
            nombre_producto="Paracetamol",
            cantidad=100,
            precio=12000,
            fecha_caducidad=datetime(2025, 6, 1)
        )
        producto2 = Producto(
            categoria_FK=categoria_cuidado.categoria_ID,
            nombre_producto="Shampoo Anticaspa",
            cantidad=50,
            precio=3000,
            fecha_caducidad=datetime(2026, 1, 15)
        )
        db.session.add_all([producto1, producto2])
        db.session.commit()

        # **6. Insertar Inventario**
        inventario1 = Inventario(producto_FK=producto1.producto_ID, cantidad=100, tipo="entrada")
        inventario2 = Inventario(producto_FK=producto2.producto_ID, cantidad=50, tipo="entrada")
        db.session.add_all([inventario1, inventario2])
        db.session.commit()

        # **7. Insertar Transacciones**
        transaccion1 = Transaccion(producto_FK=producto1.producto_ID, cantidad=20, tipo="salida")
        transaccion2 = Transaccion(producto_FK=producto2.producto_ID, cantidad=10, tipo="salida")
        db.session.add_all([transaccion1, transaccion2])
        db.session.commit()

        # **8. Insertar Laboratorios**
        laboratorio1 = Laboratorios(producto_FK=producto1.producto_ID, nombre_laboratorio="PharmaTech")
        laboratorio2 = Laboratorios(producto_FK=producto2.producto_ID, nombre_laboratorio="NaturalCare")
        db.session.add_all([laboratorio1, laboratorio2])
        db.session.commit()

        cliente1 = Cliente(
            nombre="Ana María López",
            cedula= "1234456789",
            telefono="3001234567"
        )
        cliente2 = Cliente(
            nombre="Luis Fernando Gómez",
            cedula="1007654321",
            telefono="3019876543"
        )
        db.session.add_all([cliente1, cliente2])
        db.session.commit()

        print("Base de datos inicializada correctamente con datos de prueba.")

if __name__ == "__main__":
    init_db()
