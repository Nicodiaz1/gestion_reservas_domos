from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from functools import wraps
import os
import json
from config import Config
from models import db, Domo, Reserva, Configuracion, Feriado

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

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
            print("✓ Base de datos inicializada")
        except Exception as e:
            print(f"✗ Error: {e}")

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

@app.route('/api/disponibilidad/<int:domo_id>')
def get_disponibilidad(domo_id):
    """Retorna las fechas ocupadas de un domo (para mostrar en rojo en el calendario)"""
    reservas = Reserva.query.filter_by(domo_id=domo_id, estado='confirmada').all()
    
    ocupadas = []
    for reserva in reservas:
        # Mostrar TODAS las noches ocupadas: desde fecha_inicio hasta fecha_fin (inclusive)
        # Para que el usuario vea claramente qué días están ocupados
        fecha_actual = reserva.fecha_inicio
        while fecha_actual <= reserva.fecha_fin:
            ocupadas.append(fecha_actual.isoformat())
            fecha_actual += timedelta(days=1)
    
    return jsonify({'ocupadas': ocupadas}), 200

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
            AND fecha_inicio <= :fecha_fin 
            AND fecha_fin >= :fecha_inicio
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
