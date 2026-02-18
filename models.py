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
    email = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    
    # Fechas de la reserva
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    
    # Información de precio
    cantidad_noches = db.Column(db.Integer, nullable=False)
    precio_total = db.Column(db.Float, nullable=False)
    descuento_aplicado = db.Column(db.Float, default=0.0)
    
    # Estado
    estado = db.Column(db.String(20), default='confirmada')  # confirmada, cancelada
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'domo_id': self.domo_id,
            'nombre_cliente': self.nombre_cliente,
            'email': self.email,
            'telefono': self.telefono,
            'fecha_inicio': self.fecha_inicio.isoformat(),
            'fecha_fin': self.fecha_fin.isoformat(),
            'cantidad_noches': self.cantidad_noches,
            'precio_total': self.precio_total,
            'descuento_aplicado': self.descuento_aplicado,
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
    nombre = db.Column(db.String(100), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.isoformat(),
            'nombre': self.nombre
        }
