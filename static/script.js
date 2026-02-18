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
            
            <div class="price-section" style="display: none;">
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
async function abrirReserva(domoId) {
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
    
    // Cargar fechas ocupadas
    try {
        const res = await fetch(`/api/disponibilidad/${domoId}`);
        const data = await res.json();
        const fechasOcupadas = data.ocupadas || [];
        
        // Deshabilitar fechas ocupadas en inputs
        const fechaInicioInput = document.getElementById('fechaInicio');
        const fechaFinInput = document.getElementById('fechaFin');
        
        // Aplicar atributo de fechas deshabilitadas
        const ocupadasStr = fechasOcupadas.join(',');
        fechaInicioInput.setAttribute('data-unavailable', ocupadasStr);
        fechaFinInput.setAttribute('data-unavailable', ocupadasStr);
    } catch (error) {
        console.error('Error cargando disponibilidad:', error);
    }
    
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
    
    fechaInicio.addEventListener('change', () => {
        validarFechasReservadas();
        calcularPrecio();
    });
    fechaFin.addEventListener('change', () => {
        validarFechasReservadas();
        calcularPrecio();
    });
    form.addEventListener('submit', enviarReserva);
    
    // Cerrar modal al hacer clic fuera
    window.onclick = (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    };
}

// ==================== VALIDAR FECHAS RESERVADAS ====================
function validarFechasReservadas() {
    const fechaInicio = document.getElementById('fechaInicio');
    const fechaFin = document.getElementById('fechaFin');
    const ocupadasStr = fechaInicio.getAttribute('data-unavailable') || '';
    const ocupadas = ocupadasStr ? ocupadasStr.split(',') : [];
    
    if (!fechaInicio.value || !fechaFin.value) return;
    
    const inicio = new Date(fechaInicio.value);
    const fin = new Date(fechaFin.value);
    
    let fechaActual = new Date(inicio);
    let hayConflicto = false;
    
    while (fechaActual <= fin) {
        const fechaStr = fechaActual.toISOString().split('T')[0];
        if (ocupadas.includes(fechaStr)) {
            hayConflicto = true;
            break;
        }
        fechaActual.setDate(fechaActual.getDate() + 1);
    }
    
    if (hayConflicto) {
        fechaInicio.style.borderColor = '#f44336';
        fechaFin.style.borderColor = '#f44336';
        mostrarError('Algunas fechas seleccionadas ya están reservadas (se muestran en rojo)');
    } else {
        fechaInicio.style.borderColor = '';
        fechaFin.style.borderColor = '';
    }
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
        
        // Ocultar precios pero guardar en memoria para después
        document.getElementById('precioSection').style.display = 'none';
        
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
    const fechaInicio = document.getElementById('fechaInicio');
    const fechaFin = document.getElementById('fechaFin');
    
    // Validar teléfono
    if (!telefono) {
        mostrarError('Debes proporcionar un Teléfono');
        return;
    }
    
    // Validar email si se proporciona
    if (email && !email.includes('@')) {
        mostrarError('El email no es válido');
        return;
    }
    
    // Verificar que no haya fechas en rojo (reservadas)
    if (fechaInicio.style.borderColor === 'rgb(244, 67, 54)' || fechaFin.style.borderColor === 'rgb(244, 67, 54)') {
        mostrarError('No puedes reservar fechas que ya están ocupadas');
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
    const whatsappLink = 'https://wa.me/5493513433116?text=Hola%20quiero%20confirmar%20mi%20reserva%20para%20' + nombreCliente;
    
    mensaje.innerHTML = `
        <p><strong>${selectedDomo.nombre}</strong></p>
        <p style="margin: 12px 0; font-size: 14px;">Nombre: ${nombreCliente}</p>
        <p style="margin: 12px 0; font-size: 14px;">Entrada: <strong>${fechaInicio}</strong></p>
        <p style="margin: 12px 0; font-size: 14px;">Salida: <strong>${fechaFin}</strong></p>
        <p style="margin: 20px 0; font-size: 14px; color: #666;">Completá tu reserva por WhatsApp:</p>
        <a href="${whatsappLink}" target="_blank" class="btn btn-primary" style="display: inline-block; margin-top: 12px; text-decoration: none; color: white;">💬 Confirmar por WhatsApp</a>
    `;
    
    reservaModal.style.display = 'none';
    successModal.style.display = 'block';
}
