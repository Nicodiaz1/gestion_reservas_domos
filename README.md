# Sistema de Reservas Online para Domos

Sistema completo de reservas online con gestión de precios dinámicos, calendario interactivo y panel administrativo.

## Características

✅ **Página Principal**
- Calendario interactivo para cada domo
- Visualización de fechas disponibles y ocupadas
- Cálculo automático de precios en tiempo real
- Formulario de reserva amigable

✅ **Panel Administrativo** (Contraseña: `domos2025`)
- Gestión de precios (semana / fin de semana)
- Gestión de descuentos por cantidad de días
- Gestión de feriados (precios especiales)
- Visualización de todas las reservas
- Cancelación de reservas

✅ **Base de Datos**
- SQLite integrada
- Sincronización en tiempo real
- Cálculo automático de precios según el tipo de día

## Instalación

### 1. Clonar/Descargar el Proyecto

```bash
cd sistema_reservas_domos
```

### 2. Crear un Ambiente Virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar la Aplicación

```bash
python app.py
```

La aplicación estará disponible en: **http://localhost:5000**

### 5. Inicializar la Base de Datos (Opcional)

Si necesitas resetear los datos:

```bash
curl -X POST http://localhost:5000/init-db
```

## Estructura de Carpetas

```
sistema_reservas_domos/
├── app.py                 # Backend principal (Flask)
├── config.py             # Configuración
├── models.py             # Modelos de base de datos
├── requirements.txt      # Dependencias Python
├── templates/
│   ├── index.html        # Página principal
│   ├── admin_login.html  # Login admin
│   └── admin_dashboard.html # Panel admin
└── static/
    ├── style.css         # Estilos
    └── script.js         # JavaScript
```

## Uso

### Para Clientes

1. Ir a **http://localhost:5000**
2. Seleccionar un domo
3. Hacer click en el calendario para elegir fechas (primera fecha = inicio, segunda fecha = fin)
4. El precio se calcula automáticamente
5. Completar datos (nombre, email, teléfono)
6. Hacer click en "Reservar"

### Para Administrador

1. Ir a **http://localhost:5000/admin/login**
2. Ingresar contraseña: `domos2025`
3. Acceder al panel de control

#### Opciones del Admin

- **Domos**: Modificar precios de semana y fin de semana para cada domo
- **Descuentos**: Definir descuentos por cantidad de días
  - Ej: 5% si alquilan 2+ días, 10% si alquilan 3+ días
- **Feriados**: Agregar fechas especiales con precio de fin de semana
- **Reservas**: Ver todas las reservas y cancelar si es necesario

## Precios Dinámicos

El sistema calcula los precios así:

1. **Por tipo de día:**
   - Lunes a Viernes: Precio semana (configurable)
   - Sábado, Domingo y Feriados: Precio fin de semana (configurable)

2. **Descuentos por cantidad de días:**
   - Configurable desde el admin
   - Ejemplo: -10% por 3+ días, -20% por 7+ días

## Base de Datos

Las tablas se crean automáticamente la primera vez. Incluyen:

- `domos`: Información de los 3 domos
- `reservas`: Todas las reservas
- `feriados`: Fechas especiales
- `configuracion`: Descuentos y configuraciones
- `precios`: Precios por domo y tipo de día

## API Endpoints

### Públicos

- `GET /` - Página principal
- `GET /api/disponibilidad/<domo_id>` - Fechas ocupadas de un domo
- `POST /api/calcular-precio` - Calcula el precio de una reserva
- `POST /api/crear-reserva` - Crea una nueva reserva

### Admin (Requieren contraseña)

- `POST /admin/login` - Login
- `GET /admin/dashboard` - Panel de control
- `GET /api/admin/reservas` - Todas las reservas
- `GET /api/admin/domos` - Información de domos
- `PUT /api/admin/domo/<domo_id>` - Actualizar precios
- `DELETE /api/admin/reserva/<reserva_id>` - Cancelar reserva
- `GET/POST /api/admin/feriados` - Gestionar feriados
- `GET/PUT /api/admin/descuentos` - Gestionar descuentos

## Personalización

### Cambiar la Contraseña del Admin

Editar `config.py`:
```python
ADMIN_PASSWORD = 'tu_nueva_contrasena'
```

### Cambiar Precios por Defecto

Editar `config.py`:
```python
'domo1': {'semana': 120, 'fin_semana': 180},
```

### Agregar Más Domos

Editar la ruta `/init-db` en `app.py` y agregar:
```python
Domo(nombre='Domo 4', descripcion='...', capacidad=4, ...)
```

## Requisitos

- Python 3.7+
- Flask 2.3.2
- Flask-SQLAlchemy 3.0.5
- SQLite (incluido en Python)

## Soporte

Para errores o problemas, revisar la consola del navegador (F12) para mensajes de error.

---

**Sistema listo para producción. Personaliza los precios y contraseña según necesites.**
