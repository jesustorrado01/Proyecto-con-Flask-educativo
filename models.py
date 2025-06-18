from flask_login import UserMixin
from config import db
from datetime import datetime

#TABLA DE ROLES
class Rol(db.Model):
    __tablename__ = 'rol'
    rol_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rol_usuario = db.Column(db.String(50), unique=True, nullable=True)
    descripcion = db.Column(db.String(255))

#TABLA CATEGORIA DE PRODUCTOS
class Categoria(db.Model):
    __tablename__ = 'categoria'
    categoria_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_categoria = db.Column(db.String(100), unique=True, nullable=True)
    descripcion = db.Column(db.String(255))

#TABLA USUARIOS
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    usuario_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rol_FK = db.Column(db.Integer, db.ForeignKey('rol.rol_ID', ondelete='CASCADE'), nullable=True)
    usuario = db.Column(db.String(80), unique=True, nullable=False)
    contraseña = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(150), unique=True,  nullable=True)
    estado = db.Column(db.Enum('activo', 'inactivo'), default='activo')

    def get_id(self):
        return str(self.usuario_ID)
    
    facturas = db.relationship('Factura', backref='usuario', cascade='all, delete')

#TABLA EMPLEADOS
class Empleado(db.Model):
    __tablename__ = 'empleados'
    empleado_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_FK = db.Column(db.Integer, db.ForeignKey('usuarios.usuario_ID', ondelete='CASCADE'), nullable=False)
    nombre1 = db.Column(db.String(150), nullable=False)
    nombre2 = db.Column(db.String(150))
    apellido1 = db.Column(db.String(150), nullable=False)
    apellido2 = db.Column(db.String(150))
    direccion = db.Column(db.String(100), nullable=False)
    documento_identificacion = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    telefono = db.Column(db.String(12), nullable=False)
    fecha_contratacion = db.Column(db.Date)
    estado = db.Column(db.Enum('activo', 'inactivo'), default='activo')


#TABLA PRODUCTOS
class Producto(db.Model):
    __tablename__ = 'productos'
    producto_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    categoria_FK = db.Column(db.Integer, db.ForeignKey('categoria.categoria_ID', ondelete='CASCADE'), nullable=False)
    nombre_producto = db.Column(db.String(150), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Integer, nullable=False)
    fecha_caducidad = db.Column(db.Date, nullable=False)

    facturas_detalle = db.relationship('FacturaDetalle', backref='producto', cascade='all, delete')
    inventario = db.relationship('Inventario', backref='producto', cascade='all, delete')

#TABLA INVENTARIO
class Inventario(db.Model):
    __tablename__ = 'inventario'
    inventario_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    producto_FK = db.Column(db.Integer, db.ForeignKey('productos.producto_ID', ondelete='CASCADE'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.Enum('entrada', 'salida'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)


#TABLA TRANSACCIONES (Entradas y salidas de productos)
class Transaccion(db.Model):
    __tablename__ = 'transacciones'
    transaccion_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    producto_FK = db.Column(db.Integer, db.ForeignKey('productos.producto_ID', ondelete='CASCADE'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.Enum('entrada', 'salida'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow) 

#TABLA LABORAORIOS
class Laboratorios(db.Model):
    __tablename__ = 'laboratorios'
    laboratorio_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    producto_FK = db.Column(db.Integer, db.ForeignKey('productos.producto_ID', ondelete='CASCADE'), nullable=False)
    nombre_laboratorio = db.Column(db.String(150), nullable=False)

#TABLA FACTURAS
class Factura(db.Model):
    __tablename__ = 'facturas'
    factura_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_FK = db.Column(db.Integer, db.ForeignKey('usuarios.usuario_ID', ondelete='CASCADE'), nullable=False)
    empleado_FK = db.Column(db.Integer, db.ForeignKey('empleados.empleado_ID', ondelete='CASCADE'), nullable=True)
    cliente_FK = db.Column(db.Integer, db.ForeignKey('clientes.cliente_ID', ondelete='CASCADE'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Numeric(10,2), nullable=False)

    empleado = db.relationship('Empleado', backref='facturas') 

    detalles = db.relationship('FacturaDetalle', backref='factura', cascade='all, delete')


#TABLA DETALLE FACTURA
class FacturaDetalle(db.Model):
    __tablename__ = 'factura_Detalle'
    detalle_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    factura_FK = db.Column(db.Integer, db.ForeignKey('facturas.factura_ID', ondelete='CASCADE'), nullable=False)
    producto_FK = db.Column(db.Integer, db.ForeignKey('productos.producto_ID', ondelete='CASCADE'), nullable=False)
    nombre_producto = db.Column(db.String(150), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10,2), nullable=False)
    subtotal = db.Column(db.Numeric(10,2), nullable=False)

#TABLA CLIENTE

class Cliente(db.Model):
    __tablename__ = 'clientes'
    cliente_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(150), nullable=False)
    cedula = db.Column(db.String(20), unique=True)
    telefono = db.Column(db.String(15), nullable=False)

    facturas = db.relationship('Factura', backref='Cliente', lazy=True)