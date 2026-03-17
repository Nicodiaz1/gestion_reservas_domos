from flask import Flask, render_template, request, jsonify, redirect, session, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from functools import wraps
import os
import io
import json
import uuid
from sqlalchemy import inspect, text
from werkzeug.utils import secure_filename
from urllib.parse import quote_plus
from config import Config
from models import db, Domo, Reserva, Configuracion, Feriado, GaleriaFoto, Promocion, DocumentoInstrucciones, ReservaPago

app = Flask(__name__)
app.config.from_object(Config)

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
DOCS_FOLDER = os.path.join(app.root_path, 'static', 'docs')
ALLOWED_DOC_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOCS_FOLDER'] = DOCS_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOCS_FOLDER, exist_ok=True)

db.init_app(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file_storage):
    if not file_storage or file_storage.filename == '':
        return None
    if not allowed_file(file_storage.filename):
        return None
    filename = secure_filename(file_storage.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file_storage.save(file_path)
    return f"/static/uploads/{unique_name}"

def allowed_doc_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_DOC_EXTENSIONS

def save_uploaded_doc(file_storage):
    if not file_storage or file_storage.filename == '':
        return None
    if not allowed_doc_file(file_storage.filename):
        return None
    filename = secure_filename(file_storage.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    # Guardar en uploads para mantener el mismo flujo que imágenes
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file_storage.save(file_path)
    return f"/static/uploads/{unique_name}"


def resolver_ruta_documento(archivo_url):
    """Resuelve ruta física del PDF soportando esquemas previos y actuales"""
    if not archivo_url:
        return None

    nombre = archivo_url.split('/')[-1]
    posibles = [
        os.path.join(app.config['UPLOAD_FOLDER'], nombre),
        os.path.join(app.config['DOCS_FOLDER'], nombre)
    ]
    for ruta in posibles:
        if os.path.exists(ruta):
            return ruta
    return None

def admin_required(f):
    """Decorador para rutas que requieren autenticación de admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== INICIALIZACIÓN ====================

def crear_domos_defecto():
    """Crea los domos por defecto en la BD"""
    try:
        # Verificar si ya existen
        if Domo.query.first() is not None:
            return
        
        domos = [
            Domo(
                nombre='Domo Aguaribay',
                descripcion='Experiencia única rodeado de naturaleza, con todas las comodidades',
                capacidad=2,
                precio_semana=75000,
                precio_fin_semana=110000
            ),
            Domo(
                nombre='Domo Espinillo',
                descripcion='Confort y tranquilidad en un entorno natural privilegiado',
                capacidad=2,
                precio_semana=75000,
                precio_fin_semana=110000
            ),
            Domo(
                nombre='Domo Eucalipto',
                descripcion='Relax total con vistas espectaculares y máxima privacidad',
                capacidad=2,
                precio_semana=75000,
                precio_fin_semana=110000
            )
        ]
        for domo in domos:
            db.session.add(domo)
        db.session.commit()
        print("✓ Domos creados exitosamente")
    except Exception as e:
        print(f"✗ Error creando domos: {e}")
        db.session.rollback()

def init_db():
    """Inicializa las tablas de la base de datos"""
    with app.app_context():
        try:
            db.create_all()
            crear_domos_defecto()
            crear_feriados_argentina()
            asegurar_columnas()
            asegurar_galeria_defecto()
            print("✓ Base de datos inicializada")
        except Exception as e:
            print(f"✗ Error: {e}")

def asegurar_columnas():
    """Asegura columnas nuevas sin migraciones formales"""
    try:
        inspector = inspect(db.engine)
        
        # Columna image_url en promociones
        if inspector.has_table('promociones'):
            columnas = [col['name'] for col in inspector.get_columns('promociones')]
            if 'image_url' not in columnas:
                db.session.execute(text('ALTER TABLE promociones ADD COLUMN image_url VARCHAR(500)'))
                db.session.commit()
        
        # Columna tipo_check en reservas
        if inspector.has_table('reservas'):
            columnas = [col['name'] for col in inspector.get_columns('reservas')]
            if 'tipo_check' not in columnas:
                db.session.execute(text("ALTER TABLE reservas ADD COLUMN tipo_check VARCHAR(20) DEFAULT 'normal'"))
                db.session.commit()

        # Tabla de documentos de instrucciones y compatibilidad de columnas
        if inspector.has_table('documentos_instrucciones'):
            columnas_docs = [col['name'] for col in inspector.get_columns('documentos_instrucciones')]

            # Compatibilidad: versiones anteriores usaban archivo_pdf
            if 'archivo_url' not in columnas_docs:
                db.session.execute(text("ALTER TABLE documentos_instrucciones ADD COLUMN archivo_url VARCHAR(500)"))
                db.session.commit()

                if 'archivo_pdf' in columnas_docs:
                    db.session.execute(text("UPDATE documentos_instrucciones SET archivo_url = archivo_pdf WHERE archivo_url IS NULL"))
                    db.session.commit()

            # Compatibilidad: usar es_activo como columna base
            if 'es_activo' not in columnas_docs:
                db.session.execute(text("ALTER TABLE documentos_instrucciones ADD COLUMN es_activo BOOLEAN DEFAULT FALSE"))
                db.session.commit()

                if 'activo' in columnas_docs:
                    db.session.execute(text("UPDATE documentos_instrucciones SET es_activo = activo WHERE es_activo IS NULL"))
                    db.session.commit()

            # Respaldo en base para entornos efímeros (Railway)
            if 'archivo_blob' not in columnas_docs:
                try:
                    db.session.execute(text("ALTER TABLE documentos_instrucciones ADD COLUMN archivo_blob BYTEA"))
                except Exception:
                    db.session.rollback()
                    db.session.execute(text("ALTER TABLE documentos_instrucciones ADD COLUMN archivo_blob BLOB"))
                db.session.commit()

        # Tabla de pagos por reserva
        if not inspector.has_table('reserva_pagos'):
            db.create_all()
            db.session.commit()
                
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error agregando columnas: {e}")

def crear_feriados_argentina():
    """Crea los feriados de Argentina 2026"""
    try:
        # Verificar si ya existen
        if Feriado.query.first() is not None:
            return
        
        feriados = [
            # 2026
            {'fecha': '2026-01-01', 'descripcion': 'Año Nuevo'},
            {'fecha': '2026-02-16', 'descripcion': 'Carnaval'},
            {'fecha': '2026-02-17', 'descripcion': 'Carnaval'},
            {'fecha': '2026-03-24', 'descripcion': 'Día de la Memoria'},
            {'fecha': '2026-04-02', 'descripcion': 'Día del Veterano'},
            {'fecha': '2026-04-03', 'descripcion': 'Viernes Santo'},
            {'fecha': '2026-05-01', 'descripcion': 'Día del Trabajador'},
            {'fecha': '2026-05-25', 'descripcion': 'Revolución de Mayo'},
            {'fecha': '2026-06-15', 'descripcion': 'Paso a la Inmortalidad de Güemes'},
            {'fecha': '2026-06-20', 'descripcion': 'Día de la Bandera'},
            {'fecha': '2026-07-09', 'descripcion': 'Día de la Independencia'},
            {'fecha': '2026-08-17', 'descripcion': 'Paso a la Inmortalidad de San Martín'},
            {'fecha': '2026-10-12', 'descripcion': 'Día del Respeto a la Diversidad Cultural'},
            {'fecha': '2026-11-23', 'descripcion': 'Día de la Soberanía Nacional'},
            {'fecha': '2026-12-08', 'descripcion': 'Inmaculada Concepción'},
            {'fecha': '2026-12-25', 'descripcion': 'Navidad'},
        ]
        
        for f in feriados:
            feriado = Feriado(
                fecha=datetime.strptime(f['fecha'], '%Y-%m-%d').date(),
                descripcion=f['descripcion']
            )
            db.session.add(feriado)
        
        db.session.commit()
        print("✓ Feriados de Argentina creados")
    except Exception as e:
        print(f"✗ Error creando feriados: {e}")
        db.session.rollback()

def asegurar_galeria_defecto():
    """Agrega fotos por defecto si no existen"""
    try:
        urls_defecto = [
            'https://i.imgur.com/1rwus0F.jpg',
            'https://i.imgur.com/SdZazOK.jpg',
            'https://i.imgur.com/pfmT1Yo.jpg',
            'https://i.imgur.com/iO1sjPm.jpg',
            'https://i.imgur.com/eKUpwpH.jpg',
            'https://i.imgur.com/YwRBI5N.jpg',
            'https://i.imgur.com/4tDPyEV.jpg',
            'https://i.imgur.com/eXTTLZy.jpg',
            'https://i.imgur.com/Xk4wM4R.jpg',
            'https://i.imgur.com/lUI8A1z.jpg',
            'https://i.imgur.com/XEA5rpM.jpg',
            'https://i.imgur.com/B1ydkwh.jpg'
        ]

        existentes = {f.url for f in GaleriaFoto.query.all()}
        agregadas = 0
        for idx, url in enumerate(urls_defecto):
            if url in existentes:
                continue
            db.session.add(GaleriaFoto(url=url, orden=idx))
            agregadas += 1
        if agregadas:
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error agregando galería por defecto: {e}")

# Inicializar al crear la app
init_db()

@app.route('/migrate-db', methods=['POST'])
def migrate_db():
    """Migra la base de datos a la nueva estructura"""
    try:
        with app.app_context():
            # Recrear todas las tablas con la nueva estructura
            db.drop_all()
            db.create_all()
            crear_domos_defecto()
            crear_feriados_argentina()
        return jsonify({'mensaje': 'Base de datos migrada exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/init-db', methods=['POST'])
def init_db_route():
    """Inicializa la base de datos con datos de ejemplo"""
    try:
        db.drop_all()
        db.create_all()
        
        # Crear domos
        domos_data = [
            Domo(nombre='Domo 1', descripcion='Domo frente al bosque', capacidad=2, precio_semana=100, precio_fin_semana=150),
            Domo(nombre='Domo 2', descripcion='Domo con vista al lago', capacidad=2, precio_semana=100, precio_fin_semana=150),
            Domo(nombre='Domo 3', descripcion='Domo premium', capacidad=2, precio_semana=120, precio_fin_semana=180),
        ]
        
        for domo in domos_data:
            db.session.add(domo)
        
        db.session.commit()
        return jsonify({'mensaje': 'Base de datos inicializada'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ==================== RUTAS PÚBLICAS ====================

@app.route('/')
def index():
    """Página principal con calendario de reservas"""
    domos = Domo.query.all()
    return render_template('index.html', domos=domos)

@app.route('/api/domos')
def get_domos():
    """Retorna la lista de domos en formato JSON"""
    domos = Domo.query.all()
    
    # Si no hay domos, crear los por defecto
    if not domos:
        crear_domos_defecto()
        domos = Domo.query.all()
    
    resultado = []
    for domo in domos:
        resultado.append({
            'id': domo.id,
            'nombre': domo.nombre,
            'descripcion': domo.descripcion,
            'capacidad': domo.capacidad,
            'precio_semana': domo.precio_semana,
            'precio_fin_semana': domo.precio_fin_semana,
            'imagen': f'/static/img/domo{domo.id}.jpg'
        })
    return jsonify(resultado), 200


@app.route('/api/galeria')
def get_galeria():
    """Retorna las fotos de la galería"""
    fotos = GaleriaFoto.query.order_by(GaleriaFoto.orden.asc(), GaleriaFoto.id.asc()).all()
    return jsonify([f.to_dict() for f in fotos]), 200


@app.route('/api/promociones')
def get_promociones():
    """Retorna las promociones activas"""
    promos = Promocion.query.filter_by(activo=True).order_by(Promocion.orden.asc(), Promocion.id.asc()).all()
    return jsonify([p.to_dict() for p in promos]), 200

@app.route('/api/disponibilidad/<int:domo_id>')
def get_disponibilidad(domo_id):
    """Retorna las fechas ocupadas y de checkout de un domo"""
    reservas = Reserva.query.filter_by(domo_id=domo_id, estado='confirmada').all()
    
    ocupadas = []
    checkouts = []
    inicios = []
    
    for reserva in reservas:
        # Inicio de reserva
        inicios.append(reserva.fecha_inicio.isoformat())

        # Ocupadas: desde fecha_inicio hasta fecha_fin-1 (noches en que está ocupado)
        fecha_actual = reserva.fecha_inicio
        while fecha_actual < reserva.fecha_fin:
            ocupadas.append(fecha_actual.isoformat())
            fecha_actual += timedelta(days=1)
        
        # Checkouts: la fecha_fin se muestra como "checkout" (salida pero disponible como entrada siguiente)
        checkouts.append(reserva.fecha_fin.isoformat())
    
    return jsonify({'ocupadas': ocupadas, 'checkouts': checkouts, 'inicios': inicios}), 200

@app.route('/api/calcular-precio', methods=['POST'])
def calcular_precio():
    """Calcula el precio de una reserva según fechas y domo"""
    data = request.json
    domo_id = data.get('domo_id')
    fecha_inicio_str = data.get('fecha_inicio')
    fecha_fin_str = data.get('fecha_fin')
    
    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
    except Exception as e:
        return jsonify({'error': f'Formato de fecha inválido: {str(e)}'}), 400
    
    domo = Domo.query.get(domo_id)
    if not domo:
        return jsonify({'error': 'Domo no encontrado'}), 404
    
    # Calcular cantidad de noches
    cantidad_noches = (fecha_fin - fecha_inicio).days
    if cantidad_noches <= 0:
        return jsonify({'error': 'La fecha final debe ser posterior a la inicial'}), 400
    
    # Calcular precio por noche
    precio_total = 0
    fecha_actual = fecha_inicio
    
    # Obtener feriados
    try:
        feriados = {f.fecha for f in Feriado.query.all()}
    except:
        feriados = set()
    
    while fecha_actual < fecha_fin:
        # Verificar si es feriado o fin de semana
        es_feriado = fecha_actual in feriados
        # Viernes=4, Sábado=5, Domingo=6
        es_fin_semana = fecha_actual.weekday() >= 4
        
        if es_feriado or es_fin_semana:
            precio_total += domo.precio_fin_semana
        else:
            precio_total += domo.precio_semana
        
        fecha_actual += timedelta(days=1)
    
    # Aplicar descuento si aplica (simplificado, sin configuración)
    descuento = 0
    porcentaje_descuento = 0
    
    # Descuentos básicos por cantidad de noches
    if cantidad_noches >= 7:
        porcentaje_descuento = 0.15  # 15% por 7+ noches
    elif cantidad_noches >= 3:
        porcentaje_descuento = 0.10  # 10% por 3+ noches
    
    descuento = precio_total * porcentaje_descuento
    precio_con_descuento = precio_total - descuento
    
    return jsonify({
        'precio_base': int(precio_total),
        'descuento': int(descuento),
        'precio_total': int(precio_con_descuento),
        'noches': cantidad_noches
    }), 200

@app.route('/api/crear-reserva', methods=['POST'])
def crear_reserva():
    """Crea una nueva reserva"""
    data = request.json
    
    try:
        fecha_inicio = datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()
    except Exception as e:
        return jsonify({'error': f'Formato de fecha inválido: {str(e)}'}), 400
    
    # Validar que al menos email o teléfono estén presentes
    email = data.get('email_cliente', '').strip()
    telefono = data.get('telefono_cliente', '').strip()
    
    if not telefono:
        return jsonify({'error': 'Debes proporcionar un teléfono'}), 400
    
    try:
        # Verificar disponibilidad usando SQL raw para evitar problemas con nombres de columnas
        from sqlalchemy import text
        
        sql = text("""
            SELECT COUNT(*) as count FROM reservas 
            WHERE domo_id = :domo_id 
            AND estado = 'confirmada'
            AND fecha_inicio < :fecha_fin 
            AND fecha_fin > :fecha_inicio
        """)
        
        result = db.session.execute(sql, {
            'domo_id': data['domo_id'],
            'fecha_fin': fecha_fin,
            'fecha_inicio': fecha_inicio
        }).fetchone()
        
        if result[0] > 0:
            return jsonify({'error': 'Estas fechas no están disponibles'}), 409
        
        domo = Domo.query.get(data['domo_id'])
        if not domo:
            return jsonify({'error': 'Domo no encontrado'}), 404
        
        cantidad_noches = (fecha_fin - fecha_inicio).days
        
        # Calcular precio total
        precio_total = 0
        fecha_actual = fecha_inicio
        
        # Obtener feriados
        try:
            feriados = {f.fecha for f in Feriado.query.all()}
        except:
            feriados = set()
        
        while fecha_actual < fecha_fin:
            es_feriado = fecha_actual in feriados
            es_fin_semana = fecha_actual.weekday() >= 4  # Viernes=4, Sábado=5, Domingo=6
            
            if es_feriado or es_fin_semana:
                precio_total += domo.precio_fin_semana
            else:
                precio_total += domo.precio_semana
            
            fecha_actual += timedelta(days=1)
        
        # Aplicar descuento si aplica
        if cantidad_noches >= 7:
            porcentaje_descuento = 0.15  # 15% por 7+ noches
        elif cantidad_noches >= 3:
            porcentaje_descuento = 0.10  # 10% por 3+ noches
        else:
            porcentaje_descuento = 0
        
        descuento = precio_total * porcentaje_descuento
        precio_con_descuento = precio_total - descuento
        
        # Insertar reserva usando SQL raw para compatibilidad
        sql_insert = text("""
            INSERT INTO reservas (
                domo_id, nombre_cliente, email_cliente, telefono_cliente,
                fecha_inicio, fecha_fin, estado, fecha_creacion
            ) VALUES (
                :domo_id, :nombre_cliente, :email, :telefono,
                :fecha_inicio, :fecha_fin, 'confirmada', :fecha_creacion
            )
        """)
        
        db.session.execute(sql_insert, {
            'domo_id': data['domo_id'],
            'nombre_cliente': data['nombre_cliente'],
            'email': email,
            'telefono': telefono,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'fecha_creacion': datetime.utcnow()
        })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Reserva creada exitosamente'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear reserva: {str(e)}'}), 500

# ==================== RUTAS ADMIN ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login del administrador"""
    if request.method == 'POST':
        contrasenia = request.form.get('password')
        if contrasenia == Config.ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Contraseña incorrecta'), 401
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Logout del administrador"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Panel de control del administrador"""
    return render_template('admin_dashboard.html')

@app.route('/api/admin/reservas')
@admin_required
def get_reservas_admin():
    """Obtiene todas las reservas (solo admin)"""
    reservas = Reserva.query.all()
    return jsonify([
        {
            **r.to_dict(),
            'domo_nombre': r.domo.nombre if r.domo else None
        }
        for r in reservas
    ]), 200

@app.route('/api/admin/domos')
@admin_required
def get_domos_admin():
    """Obtiene todos los domos (solo admin)"""
    domos = Domo.query.all()
    return jsonify([d.to_dict() for d in domos]), 200

@app.route('/api/admin/domo/<int:domo_id>', methods=['PUT'])
@admin_required
def actualizar_domo(domo_id):
    """Actualiza los precios de un domo"""
    data = request.json
    domo = Domo.query.get(domo_id)
    
    if not domo:
        return jsonify({'error': 'Domo no encontrado'}), 404
    
    if 'precio_semana' in data:
        domo.precio_semana = data['precio_semana']
    if 'precio_fin_semana' in data:
        domo.precio_fin_semana = data['precio_fin_semana']
    if 'descripcion' in data:
        domo.descripcion = data['descripcion']
    
    db.session.commit()
    return jsonify({'mensaje': 'Domo actualizado', 'domo': domo.to_dict()}), 200

@app.route('/api/admin/reserva/<int:reserva_id>', methods=['DELETE'])
@admin_required
def cancelar_reserva(reserva_id):
    """Cancela una reserva"""
    reserva = Reserva.query.get(reserva_id)
    
    if not reserva:
        return jsonify({'error': 'Reserva no encontrada'}), 404
    
    reserva.estado = 'cancelada'
    db.session.commit()
    
    return jsonify({'mensaje': 'Reserva cancelada'}), 200

@app.route('/api/admin/reserva/<int:reserva_id>/tipo_check', methods=['PUT'])
@admin_required
def actualizar_tipo_check(reserva_id):
    """Actualiza el tipo de check de una reserva"""
    reserva = Reserva.query.get(reserva_id)
    
    if not reserva:
        return jsonify({'error': 'Reserva no encontrada'}), 404
    
    data = request.get_json()
    tipo_check = data.get('tipo_check')
    
    if tipo_check not in ['normal', 'early_checkin', 'late_checkout']:
        return jsonify({'error': 'Tipo de check inválido'}), 400
    
    reserva.tipo_check = tipo_check
    db.session.commit()
    
    return jsonify({'mensaje': 'Tipo de check actualizado', 'tipo_check': tipo_check}), 200

@app.route('/api/admin/reserva/<int:reserva_id>/eliminar', methods=['DELETE'])
@admin_required
def eliminar_reserva_definitiva(reserva_id):
    """Elimina definitivamente una reserva"""
    reserva = Reserva.query.get(reserva_id)

    if not reserva:
        return jsonify({'error': 'Reserva no encontrada'}), 404

    db.session.delete(reserva)
    db.session.commit()

    return jsonify({'mensaje': 'Reserva eliminada'}), 200


# ==================== ADMIN GALERIA ====================

@app.route('/api/admin/galeria')
@admin_required
def admin_galeria():
    fotos = GaleriaFoto.query.order_by(GaleriaFoto.orden.asc(), GaleriaFoto.id.asc()).all()
    return jsonify([f.to_dict() for f in fotos]), 200


@app.route('/api/admin/galeria', methods=['POST'])
@admin_required
def admin_galeria_crear():
    data = request.json or {}
    url_foto = (data.get('url') or '').strip()
    titulo = (data.get('titulo') or '').strip() or None
    orden = data.get('orden') or 0

    if not url_foto:
        return jsonify({'error': 'URL requerida'}), 400

    try:
        foto = GaleriaFoto(url=url_foto, titulo=titulo, orden=int(orden))
        db.session.add(foto)
        db.session.commit()
        return jsonify(foto.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/galeria/upload', methods=['POST'])
@admin_required
def admin_galeria_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'Archivo requerido'}), 400
    archivo = request.files['file']
    url_foto = save_uploaded_file(archivo)
    if not url_foto:
        return jsonify({'error': 'Archivo inválido'}), 400
    return jsonify({'url': url_foto}), 201


@app.route('/api/admin/galeria/<int:foto_id>', methods=['DELETE'])
@admin_required
def admin_galeria_eliminar(foto_id):
    foto = GaleriaFoto.query.get(foto_id)
    if not foto:
        return jsonify({'error': 'Foto no encontrada'}), 404

    try:
        db.session.delete(foto)
        db.session.commit()
        return jsonify({'mensaje': 'Foto eliminada'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== ADMIN PROMOCIONES ====================

@app.route('/api/admin/promociones')
@admin_required
def admin_promociones():
    promos = Promocion.query.order_by(Promocion.orden.asc(), Promocion.id.asc()).all()
    return jsonify([p.to_dict() for p in promos]), 200


@app.route('/api/admin/promociones', methods=['POST'])
@admin_required
def admin_promociones_crear():
    data = request.json or {}
    titulo = (data.get('titulo') or '').strip()
    descripcion = (data.get('descripcion') or '').strip()
    detalle = (data.get('detalle') or '').strip() or None
    image_url = (data.get('image_url') or '').strip() or None
    orden = data.get('orden') or 0
    activo = bool(data.get('activo', True))

    if not titulo or not descripcion:
        return jsonify({'error': 'Título y descripción requeridos'}), 400

    try:
        promo = Promocion(
            titulo=titulo,
            descripcion=descripcion,
            detalle=detalle,
            image_url=image_url,
            orden=int(orden),
            activo=activo
        )
        db.session.add(promo)
        db.session.commit()
        return jsonify(promo.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/promociones/upload', methods=['POST'])
@admin_required
def admin_promociones_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'Archivo requerido'}), 400
    archivo = request.files['file']
    url_foto = save_uploaded_file(archivo)
    if not url_foto:
        return jsonify({'error': 'Archivo inválido'}), 400
    return jsonify({'url': url_foto}), 201


@app.route('/api/admin/promociones/<int:promo_id>', methods=['PUT'])
@admin_required
def admin_promociones_actualizar(promo_id):
    promo = Promocion.query.get(promo_id)
    if not promo:
        return jsonify({'error': 'Promoción no encontrada'}), 404

    data = request.json or {}
    promo.titulo = (data.get('titulo') or promo.titulo).strip()
    promo.descripcion = (data.get('descripcion') or promo.descripcion).strip()
    promo.detalle = (data.get('detalle') or promo.detalle)
    promo.image_url = (data.get('image_url') or promo.image_url)
    promo.orden = int(data.get('orden', promo.orden))
    promo.activo = bool(data.get('activo', promo.activo))

    try:
        db.session.commit()
        return jsonify(promo.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/promociones/<int:promo_id>', methods=['DELETE'])
@admin_required
def admin_promociones_eliminar(promo_id):
    promo = Promocion.query.get(promo_id)
    if not promo:
        return jsonify({'error': 'Promoción no encontrada'}), 404

    try:
        db.session.delete(promo)
        db.session.commit()
        return jsonify({'mensaje': 'Promoción eliminada'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== ADMIN PAGOS E INSTRUCCIONES ====================

def obtener_o_crear_pago(reserva):
    pago = ReservaPago.query.filter_by(reserva_id=reserva.id).first()
    if not pago:
        pago = ReservaPago(reserva_id=reserva.id)
        db.session.add(pago)
        db.session.flush()
    return pago


@app.route('/api/admin/documentos-instrucciones', methods=['GET'])
@admin_required
def admin_documentos_instrucciones_listar():
    documentos = DocumentoInstrucciones.query.order_by(DocumentoInstrucciones.fecha_creacion.desc()).all()
    return jsonify([d.to_dict() for d in documentos]), 200


@app.route('/api/admin/documentos-instrucciones', methods=['POST'])
@admin_required
def admin_documentos_instrucciones_crear():
    nombre = (request.form.get('nombre') or '').strip()
    descripcion = (request.form.get('descripcion') or '').strip() or None
    archivo = request.files.get('file')

    if not nombre:
        return jsonify({'error': 'Nombre requerido'}), 400
    if not archivo:
        return jsonify({'error': 'Archivo requerido'}), 400

    if not allowed_doc_file(archivo.filename or ''):
        return jsonify({'error': 'Archivo inválido. Solo PDF'}), 400

    contenido_pdf = archivo.read()
    if not contenido_pdf:
        return jsonify({'error': 'El PDF está vacío'}), 400

    filename = secure_filename(archivo.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    url_doc = f"/static/uploads/{unique_name}"
    ruta_archivo = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)

    # Mejor esfuerzo: guardar también en disco
    try:
        with open(ruta_archivo, 'wb') as f:
            f.write(contenido_pdf)
    except Exception:
        pass

    try:
        existe_activo = DocumentoInstrucciones.query.filter_by(activo=True).first() is not None
        doc = DocumentoInstrucciones(
            nombre=nombre,
            descripcion=descripcion,
            archivo_url=url_doc,
            archivo_blob=contenido_pdf,
            activo=not existe_activo
        )
        db.session.add(doc)
        db.session.commit()
        return jsonify(doc.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/documentos-instrucciones/<int:documento_id>/activar', methods=['PUT'])
@admin_required
def admin_documentos_instrucciones_activar(documento_id):
    doc = DocumentoInstrucciones.query.get(documento_id)
    if not doc:
        return jsonify({'error': 'Documento no encontrado'}), 404

    try:
        DocumentoInstrucciones.query.update({'activo': False})
        doc.activo = True
        db.session.commit()
        return jsonify({'mensaje': 'Documento activo actualizado'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/documentos-instrucciones/<int:documento_id>', methods=['DELETE'])
@admin_required
def admin_documentos_instrucciones_eliminar(documento_id):
    doc = DocumentoInstrucciones.query.get(documento_id)
    if not doc:
        return jsonify({'error': 'Documento no encontrado'}), 404

    try:
        ruta_archivo = resolver_ruta_documento(doc.archivo_url)
        if ruta_archivo and os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)

        db.session.delete(doc)
        db.session.commit()
        return jsonify({'mensaje': 'Documento eliminado'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/documentos-instrucciones/<int:documento_id>/archivo')
def ver_documento_instrucciones(documento_id):
    doc = DocumentoInstrucciones.query.get(documento_id)
    if not doc:
        return jsonify({'error': 'Documento no encontrado'}), 404

    ruta_archivo = resolver_ruta_documento(doc.archivo_url)
    if ruta_archivo:
        return send_file(ruta_archivo, mimetype='application/pdf')

    if doc.archivo_blob:
        return send_file(
            io.BytesIO(doc.archivo_blob),
            mimetype='application/pdf',
            download_name=f"{secure_filename(doc.nombre or 'instrucciones')}.pdf"
        )

    return jsonify({'error': 'Archivo no encontrado'}), 404


@app.route('/api/admin/pagos', methods=['GET'])
@admin_required
def admin_pagos_listar():
    reservas = Reserva.query.order_by(Reserva.fecha_inicio.desc()).all()
    resultado = []

    for reserva in reservas:
        pago = ReservaPago.query.filter_by(reserva_id=reserva.id).first()
        resultado.append({
            'reserva_id': reserva.id,
            'domo_nombre': reserva.domo.nombre if reserva.domo else 'Domo',
            'nombre_cliente': reserva.nombre_cliente,
            'email_cliente': reserva.email_cliente,
            'telefono_cliente': reserva.telefono_cliente,
            'fecha_inicio': reserva.fecha_inicio.isoformat(),
            'fecha_fin': reserva.fecha_fin.isoformat(),
            'estado_reserva': reserva.estado,
            'monto_a_pagar': pago.monto_a_pagar if pago else 0,
            'monto_pagado': pago.monto_pagado if pago else 0,
            'estado_pago': pago.estado_pago if pago else 'pendiente',
            'nota_pago': pago.nota_pago if pago else None,
            'instrucciones_enviadas': pago.instrucciones_enviadas if pago else False
        })

    return jsonify(resultado), 200


@app.route('/api/admin/pagos/<int:reserva_id>', methods=['PUT'])
@admin_required
def admin_pagos_actualizar(reserva_id):
    reserva = Reserva.query.get(reserva_id)
    if not reserva:
        return jsonify({'error': 'Reserva no encontrada'}), 404

    data = request.json or {}

    try:
        pago = obtener_o_crear_pago(reserva)

        monto_a_pagar = float(data.get('monto_a_pagar', pago.monto_a_pagar or 0))
        monto_pagado = float(data.get('monto_pagado', pago.monto_pagado or 0))

        if monto_pagado <= 0:
            estado_pago = 'pendiente'
        elif monto_pagado < monto_a_pagar:
            estado_pago = 'parcial'
        else:
            estado_pago = 'pagado'

        pago.monto_a_pagar = monto_a_pagar
        pago.monto_pagado = monto_pagado
        pago.estado_pago = estado_pago
        pago.nota_pago = (data.get('nota_pago') or '').strip() or None

        db.session.commit()
        return jsonify({'mensaje': 'Pago actualizado', 'pago': pago.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/instrucciones/enviar/<int:reserva_id>', methods=['POST'])
@admin_required
def admin_enviar_instrucciones(reserva_id):
    reserva = Reserva.query.get(reserva_id)
    if not reserva:
        return jsonify({'error': 'Reserva no encontrada'}), 404

    data = request.json or {}
    canal = (data.get('canal') or 'whatsapp').strip().lower()
    mensaje_extra = (data.get('mensaje') or '').strip()

    documento = DocumentoInstrucciones.query.filter_by(activo=True).first()
    if not documento:
        documento = DocumentoInstrucciones.query.order_by(DocumentoInstrucciones.fecha_creacion.desc()).first()
    if not documento:
        return jsonify({'error': 'No hay PDFs de instrucciones cargados'}), 400

    base_url = request.host_url.rstrip('/')
    pdf_url = f"{base_url}/api/documentos-instrucciones/{documento.id}/archivo"

    mensaje_whatsapp = (
        f"Hola {reserva.nombre_cliente}!\n"
        f"Te compartimos las instrucciones de ingreso para tu estadía en {reserva.domo.nombre if reserva.domo else 'el domo'}.\n"
        f"PDF: {pdf_url}\n"
    )
    if mensaje_extra:
        mensaje_whatsapp += f"{mensaje_extra}\n"

    try:
        pago = obtener_o_crear_pago(reserva)
        pago.instrucciones_enviadas = True
        db.session.commit()
    except Exception:
        db.session.rollback()

    if canal == 'email':
        asunto = quote_plus('Instrucciones de ingreso - Reserva de domo')
        cuerpo = quote_plus(
            f"Hola {reserva.nombre_cliente},\n\n"
            f"Te compartimos las instrucciones de ingreso:\n{pdf_url}\n\n"
            f"Gracias."
        )
        mailto = f"mailto:{reserva.email_cliente or ''}?subject={asunto}&body={cuerpo}"
        return jsonify({'canal': 'email', 'url': mailto}), 200

    telefono = (reserva.telefono_cliente or '').replace(' ', '').replace('+', '').replace('-', '')
    whatsapp_url = f"https://wa.me/{telefono}?text={quote_plus(mensaje_whatsapp)}"
    return jsonify({'canal': 'whatsapp', 'url': whatsapp_url}), 200

@app.route('/api/admin/feriados', methods=['GET', 'POST'])
@admin_required
def gestionar_feriados():
    """Gestiona los feriados"""
    if request.method == 'GET':
        feriados = Feriado.query.all()
        return jsonify([f.to_dict() for f in feriados]), 200
    
    if request.method == 'POST':
        data = request.json
        try:
            fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        except:
            return jsonify({'error': 'Formato de fecha inválido'}), 400
        
        feriado = Feriado(fecha=fecha, nombre=data['nombre'])
        db.session.add(feriado)
        db.session.commit()
        
        return jsonify({'mensaje': 'Feriado agregado', 'feriado': feriado.to_dict()}), 201

@app.route('/api/admin/feriado/<int:feriado_id>', methods=['DELETE'])
@admin_required
def eliminar_feriado(feriado_id):
    """Elimina un feriado"""
    feriado = Feriado.query.get(feriado_id)
    
    if not feriado:
        return jsonify({'error': 'Feriado no encontrado'}), 404
    
    db.session.delete(feriado)
    db.session.commit()
    
    return jsonify({'mensaje': 'Feriado eliminado'}), 200

@app.route('/api/admin/descuentos', methods=['GET', 'PUT'])
@admin_required
def gestionar_descuentos():
    """Gestiona los descuentos por cantidad de días"""
    if request.method == 'GET':
        config = Configuracion.query.filter_by(clave='descuentos').first()
        if config:
            return jsonify(json.loads(config.valor)), 200
        return jsonify({}), 200
    
    if request.method == 'PUT':
        data = request.json
        config = Configuracion.query.filter_by(clave='descuentos').first()
        
        if not config:
            config = Configuracion(clave='descuentos', valor=json.dumps(data), tipo='json')
            db.session.add(config)
        else:
            config.valor = json.dumps(data)
        
        db.session.commit()
        return jsonify({'mensaje': 'Descuentos actualizados'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
