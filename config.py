import os
from datetime import datetime

class Config:
    """Configuración general de la aplicación"""
    SECRET_KEY = 'domos2025_secret_key'
    _database_url = os.environ.get('DATABASE_URL', 'sqlite:///domos_reservas.db')
    if _database_url.startswith('postgresql://'):
        _database_url = _database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    SQLALCHEMY_DATABASE_URI = _database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_PASSWORD = 'domos2025'
    
    # Configuración de precios por defecto
    PRECIOS_DEFAULT = {
        'domo1': {'semana': 100, 'fin_semana': 150},
        'domo2': {'semana': 100, 'fin_semana': 150},
        'domo3': {'semana': 100, 'fin_semana': 150}
    }
    
    # Descuentos por cantidad de días
    DESCUENTOS = {
        2: 0.05,   # 5% para 2+ días
        3: 0.10,   # 10% para 3+ días
        5: 0.15,   # 15% para 5+ días
        7: 0.20    # 20% para 7+ días
    }
