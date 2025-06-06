from flask import Flask, redirect, request, render_template, url_for, flash, send_file, session, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt
from models import Rol, Categoria, Usuario, Empleado, Producto, Inventario, Transaccion, Laboratorios, Factura, FacturaDetalle
from config import DATABASE_URL, db
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import date, datetime, timezone, timedelta
import os
from io import BytesIO
import re
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '1234'

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))

@app.route('/')
def index():
    return redirect(url_for('login'))

#INICIO DE SESION
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contraseña = request.form['contraseña']

        usuario_existente = Usuario.query.filter_by(usuario=usuario).first()

        if usuario_existente and bcrypt.check_password_hash(usuario_existente.contraseña, contraseña):
            login_user(usuario_existente)

            rol_usuario = Rol.query.filter_by(rol_ID=usuario_existente.rol_FK).first()

            if rol_usuario and rol_usuario.rol_usuario == 'administrador':
                return redirect(url_for('adminMain'))
            else:
                return redirect(url_for('empleadoMain'))
        else:
            flash ('Usuario o contraseña incorrectos', 'danger')
            return redirect(url_for('login'))

        
    return render_template('login.html')

#MAIN DE ADMINISTRADOR
@app.route('/adminMain')
@login_required
def adminMain():
    if not current_user.is_authenticated or  db.session.get(Rol, current_user.rol_FK).rol_usuario != "administrador": 
        flash ('Acceso no autorizado', 'danger')
        return redirect(url_for('login'))
    
    fecha_actual = datetime.now().date()
    fecha_limite = fecha_actual + timedelta(days=30)

    productos_proximos_a_caducar = Producto.query.filter( 
        Producto.fecha_caducidad <= fecha_limite
    ).order_by(Producto.fecha_caducidad).limit(3).all()

    productos = []
    for producto in productos_proximos_a_caducar:
        dias_restantes = (producto.fecha_caducidad - fecha_actual).days
        productos.append({
            "nombre": producto.nombre_producto,
            "fecha_caducidad": producto.fecha_caducidad,
            "dias_restantes": dias_restantes
        })

    return render_template('adminMain.html', productos=productos)

@app.route('/productosDB')
@login_required
def productosDB():
    if db.session.get(Rol, current_user.rol_FK).rol_usuario != "administrador":
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('adminMain'))
    
    categorias = Categoria.query.all()

    search_query = request.args.get('search', '', type=str)

    if search_query:
        productos = Producto.query.filter(Producto.nombre_producto.ilike(f"%{search_query}%")).all()
    else: 
        productos = Producto.query.all()
    
    return render_template('productosDB.html', productos=productos, search_query=search_query, categorias=categorias)

@app.route('/productosDB/create', methods=['POST'])
@login_required
def create_producto():
    if Rol.query.get(current_user.rol_FK).rol_usuario != "administrador":
        flash("Acceso no autorizado", "danger")
        return redirect(url_for('productosDB'))

    data = request.form
    errores = []

    nombre = data.get('nombre_producto', '').strip()
    if not nombre.isalpha():
        errores.append("El nombre del producto debe contener solo letras.")

    try:
        cantidad = int(data.get('cantidad', ''))
        if cantidad < 0:
            errores.append("La cantidad no puede ser negativa.")
    except ValueError:
        errores.append("La cantidad debe ser un número entero.")

    try:
        precio = float(data.get('precio', ''))
        if precio < 0:
            errores.append("El precio no puede ser negativo.")
    except ValueError:
        errores.append("El precio debe ser un número válido.")

    try:
        fecha_caducidad = datetime.strptime(data.get('fecha_caducidad', ''), "%Y-%m-%d")
    except ValueError:
        errores.append("La fecha debe tener el formato YYYY-MM-DD.")

    categoria_id = data.get('categoria_ID')
    if not categoria_id or not categoria_id.isdigit():
        errores.append("La categoría debe ser un número válido.")

    producto_existente = Producto.query.filter_by(
        nombre_producto=nombre, categoria_FK=int(categoria_id)
    ).first()
    if producto_existente:
        errores.append("Ya existe un producto con ese nombre")

    if errores:
        for error in errores:
            flash(error, "danger")  
        return redirect(url_for('productosDB'))  

    nuevo_producto = Producto(
        categoria_FK=int(categoria_id),
        nombre_producto=nombre,
        cantidad=cantidad,
        precio=precio,
        fecha_caducidad=fecha_caducidad
    )
    db.session.add(nuevo_producto)
    db.session.commit()

    flash("Producto creado exitosamente", "success")
    return redirect(url_for('productosDB'))

@app.route('/productosDB/update/<int:id>', methods=['POST'])
@login_required
def update_producto(id):
    if Rol.query.get(current_user.rol_FK).rol_usuario != "administrador":
        flash("Acceso no autorizado", "danger")
        return redirect(url_for('productosDB'))

    producto = Producto.query.get_or_404(id)
    data = request.form

    errores = []

    nombre = data.get('nombre_producto', '').strip()
    if not nombre.isalpha() and not all(part.isalpha() for part in nombre.split()):
        errores.append("El nombre del producto debe contener solo letras.")

    try:
        cantidad = int(data.get('cantidad', ''))
        if cantidad < 0:
            errores.append("La cantidad no puede ser negativa.")
    except ValueError:
        errores.append("La cantidad debe ser un número entero.")

    try:
        precio = float(data.get('precio', ''))
        if precio < 0:
            errores.append("El precio no puede ser negativo.")
    except ValueError:
        errores.append("El precio debe ser un número válido.")

    try:
        fecha = datetime.strptime(data.get('fecha_caducidad', ''), "%Y-%m-%d")
        if fecha.date() < datetime.today().date():
            errores.append("La fecha de caducidad no puede estar en el pasado.")
    except ValueError:
        errores.append("Formato de fecha inválido.")

    categoria_id = data.get('categoria_ID')
    if not Categoria.query.get(categoria_id):
        errores.append("La categoría seleccionada no existe.")

    if errores:
        for e in errores:
            flash(e, "danger")
        return redirect(url_for('productosDB'))  

    producto.categoria_FK = categoria_id
    producto.nombre_producto = nombre
    producto.cantidad = cantidad
    producto.precio = precio
    producto.fecha_caducidad = fecha

    db.session.commit()
    flash("Producto actualizado correctamente.", "success")
    return redirect(url_for('productosDB'))

@app.route('/productosDB/edit/<int:id>', methods=['GET'])
@login_required
def edit_producto(id):             
    if Rol.query.get(current_user.rol_FK).rol_usuario != "administrador":
        return jsonify({"error": "Acceso no autorizado"}), 403

    producto = Producto.query.get_or_404(id)
    categorias = Categoria.query.all()
    return render_template('edit_producto.html', producto=producto, categorias=categorias                                                                                                     )

@app.route('/productosDB/delete/<int:id>', methods=['POST'])
@login_required
def delete_producto(id):
    if Rol.query.get(current_user.rol_FK).rol_usuario != "administrador":
        flash("Acceso no autorizado." , "danger")
        return redirect(url_for("productosDB"))
    
    producto = Producto.query.get_or_404(id)

    try:
        db.session.delete(producto)
        db.session.commit()
        flash(f"Producto '{producto.nombre_producto}' eliminado exitosamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Ocurrió un error al eliminar el producto. Inténtelo mas más tarde", "danger")

    return redirect(url_for('productosDB'))

@app.route('/empleadosDB')
@login_required
def empleadosDB():
    rol_usuario = Rol.query.get(current_user.rol_FK)
    if not rol_usuario or rol_usuario.rol_usuario != "administrador":
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('adminMain'))

    empleados = Empleado.query.all()
    return render_template('empleadosDB.html', empleados=empleados)

@app.route('/empleadosDB/create', methods=['POST'])
@login_required
def create_empleado():
    if Rol.query.get(current_user.rol_FK).rol_usuario != "administrador":
        flash ("Acceso no autorizado", "danger")
        return redirect(url_for("empleadosDB"))
        
    data = request.form

    if Usuario.query.filter_by(usuario=data['usuario']).first():
        flash ("El nombre de usuario ya está en uso", "danger")
        return redirect(url_for('empleadosDB'))
    
    if Empleado.query.filter_by(documento_identificacion=data['documento_identificacion']).first():
        flash ("El número de documento ya está registrado", "danger")
        return redirect(url_for('empleadosDB'))
    
    if len(data['contraseña']) < 6:
        flash ("La contraseña debe tener al menos 6 caracteres", "danger")
        return redirect(url_for('empleadosDB'))
    
    if not data['telefono'].isdigit() or len(data['telefono']) < 7:
        flash ("El teléfono debe contener solo numeros y ser valido", "danger")
        return redirect(url_for('empleadosDB'))
    
    try:
        fecha_contratacion = datetime.strptime(data['fecha_contratacion'], "%Y-%m-%d")
        if fecha_contratacion > datetime.today():
            flash ("La fecha de contratación no puede ser futura", "danger")
            return redirect(url_for("empleadosDB"))
    except ValueError:
        flash ("Fecha de contratación inválida", "danger")
        return redirect(url_for("empleadosDB"))
    
    email = data['email']
    email_regex = r'^[\w\.-]+@gmail\.com$'
    if not re.match(email_regex, email):
        flash ("Solo se permiten correos de tipo Gmail con formato válido (ej. tucorreo@gmail.com).", "danger")
        return redirect(url_for('empleadosDB'))

    nuevo_usuario = Usuario(
        usuario = data['usuario'],
        contraseña=bcrypt.generate_password_hash(data['contraseña']).decode('utf-8'),
        rol_FK = 2
    )
    db.session.add(nuevo_usuario)
    db.session.commit()

    nuevo_empleado = Empleado(
        usuario_FK=nuevo_usuario.usuario_ID,
        nombre1=data['nombre1'],
        nombre2=data.get('nombre2'),
        apellido1=data['apellido1'],
        apellido2=data.get('apellido2'),
        direccion=data['direccion'],
        documento_identificacion=data['documento_identificacion'],
        email=data['email'],
        telefono=data['telefono'],
        fecha_contratacion=datetime.strptime(data['fecha_contratacion'], "%Y-%m-%d"),
        estado="activo"
    )
    db.session.add(nuevo_empleado)
    db.session.commit()

    return redirect(url_for('empleadosDB'))

@app.route('/empleadosDB/update/<int:id>', methods=['POST'])
@login_required
def update_empleados(id):
    if Rol.query.get(current_user.rol_FK).rol_usuario != "administrador":
        flash ('Acceso no autorizado', 'danger')
        return redirect(url_for("empleadosDB"))


    empleado = Empleado.query.get_or_404(id)
    data = request.form

    campos_obligatorios = ['nombre1', 'apellido1', 'documento_identificacion', 'direccion', 'email', 'telefono', 'fecha_contratacion', 'estado']
    for campo in campos_obligatorios:
        if not data.get(campo):
            flash(f"El campo '{campo}' es obligatorio.", "danger")
            return redirect(url_for('edit_empleado', id=id))

    if not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
        flash("El correo electrónico no es válido.", "danger")
        return redirect(url_for('edit_empleado', id=id))

    doc_existente = Empleado.query.filter(
        Empleado.documento_identificacion == data['documento_identificacion'],
        Empleado.empleado_ID != id
    ).first()
    if doc_existente:
        flash("Este documento ya está registrado en otro empleado.", "danger")
        return redirect(url_for('edit_empleado', id=id))

    email_existente = Empleado.query.filter(
        Empleado.email == data['email'],
        Empleado.empleado_ID != id
    ).first()
    if email_existente:
        flash("Este correo electrónico ya está en uso por otro empleado.", "danger")
        return redirect(url_for('edit_empleado', id=id))

    empleado.nombre1 = data['nombre1']
    empleado.nombre2 = data.get('nombre2')
    empleado.apellido1 = data['apellido1']
    empleado.apellido2 = data.get('apellido2')
    empleado.direccion = data['direccion']
    empleado.documento_identificacion = data['documento_identificacion']
    empleado.email = data['email']
    empleado.telefono = data['telefono']
    empleado.fecha_contratacion = datetime.strptime(data['fecha_contratacion'], "%Y-%m-%d")
    empleado.estado = data['estado']

    db.session.commit()
    flash("Empleado actualizado correctamente.", "success")
    return redirect(url_for('empleadosDB'))


@app.route('/empleadosDB/edit/<int:id>', methods=['GET'])
@login_required
def edit_empleado(id):
    if Rol.query.get(current_user.rol_FK).rol_usuario != "administrador":
        return jsonify({"error": "Acceso no autorizado"}), 403

    empleado = Empleado.query.get_or_404(id)
    return render_template('edit_empleado.html', empleado=empleado)

@app.route('/empleadosDB/delete/<int:id>', methods=['POST'])
@login_required
def delete_empleado(id):
    if Rol.query.get(current_user.rol_FK).rol_usuario != "administrador":
        return jsonify({"error": "Acceso no autorizado"}), 403   

    empleado = Empleado.query.get_or_404(id)
    usuario = Usuario.query.get(empleado.usuario_FK)

    db.session.delete(usuario)
    db.session.delete(empleado)
    db.session.commit()

    return redirect(url_for('empleadosDB'))

#MAIN DE EMPLEADO
@app.route("/empleadoMain")
@login_required
def empleadoMain():
    if not current_user.is_authenticated or  db.session.get(Rol, current_user.rol_FK).rol_usuario != "empleado": #Rol.query.get(current_user.rol_FK).rol_usuario != "empleado":
        flash ('Acceso no autorizado', 'danger')
        return redirect(url_for('login'))
    
    return render_template('empleadoMain.html')

@app.route('/productoYfactura', methods=['GET', 'POST'])
@login_required
def productoYfactura():
    if request.method == 'POST':
        producto_id = request.form['producto']
        cantidad = int(request.form['cantidad'])

        producto = Producto.query.get(producto_id)
        if not producto or cantidad <= 0 or producto.cantidad < cantidad:
            flash('Cantidad inválida o producto sin stock suficiente', 'danger')
            return redirect(url_for('productoYfactura'))

        producto.cantidad -= cantidad
        transaccion = Transaccion(
            producto_FK=producto_id,
            cantidad=cantidad,
            tipo='salida',
            fecha=datetime.utcnow()
        )
        db.session.add(transaccion)
        db.session.commit()

        productos_comprados = session.get('productos_comprados', [])
        productos_comprados.append({
            'producto_id': producto_id,
            'nombre_producto': producto.nombre_producto,
            'cantidad': cantidad,
            'precio_unitario': float(producto.precio),
            'subtotal': cantidad * float(producto.precio)
        })
        session['productos_comprados'] = productos_comprados  

        return redirect(url_for('productoYfactura'))

    productos = Producto.query.all()
    return render_template('registro_compra.html', productos=productos)


@app.route('/vaciar_carrito')
@login_required
def vaciar_carrito():
    session.pop('productos_comprados', None)
    flash('Carrito vaciado correctamente.', 'info')
    return redirect(url_for('productoYfactura'))


@app.route('/confirmar_factura', methods=['GET', 'POST'])
@login_required
def confirmar_factura():
    if request.method == 'POST':
        desicion = request.form.get('desicion')
        if desicion == 'si':
            cancelada = 'si'
            return redirect(url_for('generar_factura', cancelada=cancelada))
        elif desicion == 'no':
            cancelada = 'no'
            return redirect(url_for('generar_factura', cancelada=cancelada))
        
    return render_template('confirmar_factura.html')

@app.route('/generar_factura', methods=['GET', 'POST'])
@login_required
def generar_factura():
    cancelada = request.args.get('cancelada')  

    if 'productos_comprados' not in session or not session['productos_comprados']:
        return redirect(url_for('productoYfactura'))

    productos = session.pop('productos_comprados')
    total = sum(p['subtotal'] for p in productos)

    empleado = Empleado.query.filter_by(usuario_FK=current_user.usuario_ID).first()
    nueva_factura = Factura(
        usuario_FK=current_user.usuario_ID,
        empleado_FK=empleado.empleado_ID,
        total=total,
        fecha=datetime.now(timezone.utc)
    )
    db.session.add(nueva_factura)
    db.session.commit()

    for p in productos:
        detalle = FacturaDetalle(
            factura_FK=nueva_factura.factura_ID,
            producto_FK=p["producto_id"],
            nombre_producto=p["nombre_producto"],
            cantidad=p["cantidad"],
            precio_unitario=p["precio_unitario"],
            subtotal=p["subtotal"]
        )
        db.session.add(detalle)
    db.session.commit()

    if cancelada == 'si':
        factura_id = nueva_factura.factura_ID
        pdf_stream = BytesIO()
        generar_pdf(nueva_factura, productos, pdf_stream)

        pdf_stream.seek(0)
        response = make_response(pdf_stream.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="Drogueía Farma Plus Junior".pdf'
        return response

    return redirect(url_for('empleadoMain'))


def generar_pdf(factura, productos, output_stream):
    doc = SimpleDocTemplate(output_stream, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"<b>Factura Nº {factura.factura_ID}</b>", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Fecha: {factura.fecha.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Paragraph(f"Total: <b>${factura.total:.2f}</b>", styles['Normal']))
    elements.append(Paragraph(f"Atendido por: {factura.empleado.nombre1} {factura.empleado.apellido1}", styles['Normal']))
    elements.append(Spacer(1, 20))

    data = [['Producto', 'Cantidad', 'Precio Unitario', 'Subtotal']]
    for p in productos:
        data.append([
            p["nombre_producto"],
            str(p["cantidad"]),
            f"${p['precio_unitario']:.2f}",
            f"${p['subtotal']:.2f}"
        ])

    table = Table(data, colWidths=[2.5*inch, 1*inch, 1.2*inch, 1.2*inch])

    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4B8BBE")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ])
    table.setStyle(style)

    elements.append(table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("¡Gracias por su compra!", styles['Heading2']))

    doc.build(elements)

@app.route('/historialVentas')
@login_required
def historialVentas():
    hoy = date.today()
    facturas_del_dia = Factura.query.filter(Factura.fecha >= hoy).all()

    productos_vendidos = []
    for factura in facturas_del_dia:
        detalles = FacturaDetalle.query.filter_by(factura_FK=factura.factura_ID).all()
        for detalle in detalles:
            productos_vendidos.append({
                'nombre_producto': detalle.nombre_producto,
                'cantidad': detalle.cantidad,
                'precio_unitario': detalle.precio_unitario,
                'subtotal': detalle.subtotal,
                'hora': factura.fecha.strftime('%H:%M:%S')
            })
    
    return render_template('historialVentas.html', productos=productos_vendidos)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash ('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
