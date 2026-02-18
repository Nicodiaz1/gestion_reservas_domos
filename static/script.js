// ==================== VARIABLES GLOBALES ====================
let domos = [];
let selectedDomo = null;

// ==================== INICIALIZACIÓN ====================
document.addEventListener('DOMContentLoaded', () => {
    cargarDomos();
    setupFormListeners();
});

// ==================== CARGAR DOMOS ====================
async function cargarDomos() {
    try {
        const response = await fetch('/api/domos');
        domos = await response.json();
        
        const container = document.getElementById('domosContainer');
        container.innerHTML = '';
        
        if (domos.length === 0) {
            container.innerHTML = '<p class="loading">No hay domos disponibles</p>';
            return;
        }
        
        for (const domo of domos) {
            const card = crearTarjetaDomo(domo);
            container.appendChild(card);
        }
    } catch (error) {
        console.error('Error cargando domos:', error);
        document.getElementById('domosContainer').innerHTML = '<p class="loading">Error al cargar los domos</p>';
    }
}

// ==================== CREAR TARJETA DOMO ====================
function crearTarjetaDomo(domo) {
    const div = document.createElement('div');
    div.className = 'domo-card';
    
    const emojis = ['🏕️', '🏞️', '🌲'];
    const emoji = emojis[(domo.id - 1) % 3];
    
    div.innerHTML = `
        <div class="domo-image">
            <div style="font-size: 100px;">${emoji}</div>
            <div class="domo-badge">👥 ${domo.capacidad} personas</div>
        </div>
        <div class="domo-content">
            <h2>${domo.nombre}</h2>
            <p class="domo-description">${domo.descripcion}</p>
            
            <div class="domo-features">
                <div class="feature">Hasta ${domo.capacidad} huéspedes</div>
                <div class="feature">Baño privado</div>
                <div class="feature">WiFi gratis</div>
                <div class="feature">Desayuno</div>
            </div>
            
            <div class="price-section">
                <div class="price-row">
                    <span class="price-label">Lun-Jue:</span>
                    <span class="price-value">$${domo.precio_semana.toLocaleString()}/noche</span>
                </div>
                <div class="price-row">
                    <span class="price-label">Vie-Dom:</span>
                    <span class="price-value">$${domo.precio_fin_semana.toLocaleString()}/noche</span>
                </div>
            </div>
            
            <button class="btn btn-primary" style="width: 100%;" onclick="abrirReserva(${domo.id})">Reservar Ahora</button>
        </div>
    `;
    
    return div;
}

// ==================== ABRIR MODAL DE RESERVA ====================
function abrirReserva(domoId) {
    selectedDomo = domos.find(d => d.id === domoId);
    if (!selectedDomo) return;
    
    document.getElementById('domoId').value = domoId;
    document.getElementById('domoNombre').value = selectedDomo.nombre;
    document.getElementById('fechaInicio').value = '';
    document.getElementById('fechaFin').value = '';
    document.getElementById('nombreCliente').value = '';
    document.getElementById('emailCliente').value = '';
    document.getElementById('telefonoCliente').value = '';
    document.getElementById('precioSection').style.display = 'none';
    
    document.getElementById('reservaModal').style.display = 'block';
}

// ==================== CERRAR MODAL ====================
function cerrarModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// ==================== SETUP FORM LISTENERS ====================
function setupFormListeners() {
    const fechaInicio = document.getElementById('fechaInicio');
    const fechaFin = document.getElementById('fechaFin');
    const form = document.getElementById('reservaForm');
    
    fechaInicio.addEventListener('change', calcularPrecio);
    fechaFin.addEventListener('change', calcularPrecio);
    form.addEventListener('submit', enviarReserva);
    
    // Cerrar modal al hacer clic fuera
    window.onclick = (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    };
}

// ==================== CALCULAR PRECIO ====================
async function calcularPrecio() {
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;
    
    if (!fechaInicio || !fechaFin || !selectedDomo) return;
    
    try {
        const response = await fetch('/api/calcular-precio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                domo_id: selectedDomo.id,
                fecha_inicio: fechaInicio,
                fecha_fin: fechaFin
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            mostrarError(data.error);
            document.getElementById('precioSection').style.display = 'none';
            return;
        }
        
        // Actualizar UI con precios
        document.getElementById('noches').textContent = data.noches;
        document.getElementById('precioBase').textContent = `$${data.precio_base}`;
        document.getElementById('precioTotal').textContent = `$${data.precio_total}`;
        
        const descuentoRow = document.getElementById('descuentoRow');
        if (data.descuento && data.descuento > 0) {
            descuentoRow.style.display = 'flex';
            document.getElementById('descuento').textContent = `-$${data.descuento}`;
        } else {
            descuentoRow.style.display = 'none';
        }
        
        document.getElementById('precioSection').style.display = 'block';
        
    } catch (error) {
        console.error('Error calculando precio:', error);
        mostrarError('Error al calcular el precio');
    }
}

// ==================== ENVIAR RESERVA ====================
async function enviarReserva(e) {
    e.preventDefault();
    
    const email = document.getElementById('emailCliente').value.trim();
    const telefono = document.getElementById('telefonoCliente').value.trim();
    
    // Validar que al menos uno de email o teléfono esté completo
    if (!email && !telefono) {
        mostrarError('Debes proporcionar al menos Email o Teléfono');
        return;
    }
    
    if (email && !email.includes('@')) {
        mostrarError('El email no es válido');
        return;
    }
    
    const datos = {
        domo_id: parseInt(document.getElementById('domoId').value),
        fecha_inicio: document.getElementById('fechaInicio').value,
        fecha_fin: document.getElementById('fechaFin').value,
        nombre_cliente: document.getElementById('nombreCliente').value,
        email_cliente: email,
        telefono_cliente: telefono
    };
    
    try {
        const response = await fetch('/api/crear-reserva', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos)
        });
        
        const result = await response.json();
        
        if (result.error) {
            mostrarError(result.error);
        } else {
            mostrarExito(result);
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarError('Error al crear la reserva. Intenta de nuevo.');
    }
}

// ==================== MOSTRAR ERROR ====================
function mostrarError(mensaje) {
    const modal = document.getElementById('errorModal');
    document.getElementById('errorMessage').textContent = mensaje;
    modal.style.display = 'block';
}

// ==================== MOSTRAR ÉXITO ====================
function mostrarExito(data) {
    const reservaModal = document.getElementById('reservaModal');
    const successModal = document.getElementById('successModal');
    const mensaje = document.getElementById('successMessage');
    
    const nombreCliente = document.getElementById('nombreCliente').value;
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;
    const emailCliente = document.getElementById('emailCliente').value;
    const precioTotal = document.getElementById('precioTotal').textContent;
    
    mensaje.innerHTML = `
        <p><strong>${selectedDomo.nombre}</strong></p>
        <p style="margin: 12px 0; font-size: 14px;">Nombre: ${nombreCliente}</p>
        <p style="margin: 12px 0; font-size: 14px;">Entrada: <strong>${fechaInicio}</strong></p>
        <p style="margin: 12px 0; font-size: 14px;">Salida: <strong>${fechaFin}</strong></p>
        <p style="margin: 20px 0; font-size: 18px; color: #4caf50;"><strong>${precioTotal}</strong></p>
        <p style="margin-top: 15px; font-size: 13px; color: #666;">Se envió confirmación a ${emailCliente}</p>
    `;
    
    reservaModal.style.display = 'none';
    successModal.style.display = 'block';
}
