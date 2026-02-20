from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Domo(db.Model):
    """Modelo para los domos disponibles"""
    __tablename__ = 'domos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(255))
    capacidad = db.Column(db.Integer, default=4)
    
    # Precios
    precio_semana = db.Column(db.Float, default=100.0)
    precio_fin_semana = db.Column(db.Float, default=150.0)
    
    # Relaciones
    reservas = db.relationship('Reserva', backref='domo', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'capacidad': self.capacidad,
            'precio_semana': self.precio_semana,
            'precio_fin_semana': self.precio_fin_semana
        }

class Reserva(db.Model):
    """Modelo para las reservas"""
    __tablename__ = 'reservas'
    
    id = db.Column(db.Integer, primary_key=True)
    domo_id = db.Column(db.Integer, db.ForeignKey('domos.id'), nullable=False)
    
    # Información del cliente
    nombre_cliente = db.Column(db.String(100), nullable=False)
    email_cliente = db.Column(db.String(100))
    telefono_cliente = db.Column(db.String(20))
    
    # Fechas de la reserva
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    
    # Estado
    estado = db.Column(db.String(20), default='confirmada')  # confirmada, cancelada
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'domo_id': self.domo_id,
            'nombre_cliente': self.nombre_cliente,
            'email_cliente': self.email_cliente,
            'telefono_cliente': self.telefono_cliente,
            'fecha_inicio': self.fecha_inicio.isoformat(),
            'fecha_fin': self.fecha_fin.isoformat(),
            'estado': self.estado
        }

class Configuracion(db.Model):
    """Modelo para guardar configuraciones del sistema"""
    __tablename__ = 'configuracion'
    
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.String(500), nullable=False)
    tipo = db.Column(db.String(20))  # string, number, json
    
    def to_dict(self):
        return {
            'clave': self.clave,
            'valor': self.valor,
            'tipo': self.tipo
        }

class Feriado(db.Model):
    """Modelo para guardar los feriados"""
    __tablename__ = 'feriados'
    
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, unique=True, nullable=False)
    nombre = db.Column(db.String(100))
    descripcion = db.Column(db.String(200))
    
    def to_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.isoformat(),
            'nombre': self.nombre or self.descripcion,
            'descripcion': self.descripcion
        }


class GaleriaFoto(db.Model):
    """Fotos de la galería administradas desde el panel"""
    __tablename__ = 'galeria_fotos'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    titulo = db.Column(db.String(120))
    orden = db.Column(db.Integer, default=0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'titulo': self.titulo,
            'orden': self.orden
        }


class Promocion(db.Model):
    """Promociones visibles en la página principal"""
    __tablename__ = 'promociones'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.String(500), nullable=False)
    detalle = db.Column(db.String(200))
    activo = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(500))
    orden = db.Column(db.Integer, default=0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'detalle': self.detalle,
            'activo': self.activo,
            'image_url': self.image_url,
            'orden': self.orden
        }
