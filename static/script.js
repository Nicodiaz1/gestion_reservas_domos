// ==================== VARIABLES GLOBALES ====================
let domos = [];
let selectedDomo = null;
let selectedStartDate = null;
let selectedEndDate = null;

// ==================== INICIALIZACIÓN ====================
document.addEventListener('DOMContentLoaded', () => {
    cargarDomos();
    setupModals();
    setupFormListeners();
});

// ==================== CARGAR DOMOS ====================
async function cargarDomos() {
    try {
        const response = await fetch('/api/domos');
        domos = await response.json();
        
        const container = document.getElementById('domosContainer');
        container.innerHTML = '';
        
        for (const domo of domos) {
            const card = crearTarjetaDomo(domo);
            container.appendChild(card);
        }
    } catch (error) {
        console.error('Error cargando domos:', error);
        mostrarError('Error al cargar los domos');
    }
}

// ==================== CREAR TARJETA DOMO ====================
function crearTarjetaDomo(domo) {
    const card = document.createElement('div');
    card.className = 'domo-card';
    
    const emojis = ['🏕️', '🏞️', '🌲'];
    const emoji = emojis[domo.id % 3];
    
    card.innerHTML = `
        <div class="domo-image">
            <div style="font-size: 100px;">${emoji}</div>
            <div class="domo-badge">Capacidad: ${domo.capacidad} personas</div>
        </div>
        <div class="domo-content">
            <h2>${domo.nombre}</h2>
            <p class="domo-description">${domo.descripcion}</p>
            
            <div class="domo-features">
                <div class="feature">Hasta ${domo.capacidad} huéspedes</div>
                <div class="feature">Baño privado</div>
                <div class="feature">WiFi gratis</div>
            </div>
            
            <div class="price-section">
                <div class="price-row">
                    <span class="price-label">Lun-Vie:</span>
                    <span class="price-value">$${domo.precio_semana}/noche</span>
                </div>
                <div class="price-row">
                    <span class="price-label">Sáb-Dom (y feriados):</span>
                    <span class="price-value">$${domo.precio_fin_semana}/noche</span>
                </div>
            </div>
            
            <button class="btn" onclick="abrirReserva(${domo.id})">Reservar Ahora</button>
        </div>
    `;
    
    return card;
}

// ==================== MODAL DE RESERVA ====================
function abrirReserva(domoId) {
    selectedDomo = domos.find(d => d.id === domoId);
    selectedStartDate = null;
    selectedEndDate = null;
    
    document.getElementById('domoId').value = domoId;
    document.getElementById('domoNombre').value = selectedDomo.nombre;
    document.getElementById('fechaInicio').value = '';
    document.getElementById('fechaFin').value = '';
    document.getElementById('precioSection').style.display = 'none';
    document.getElementById('nombreCliente').value = '';
    document.getElementById('emailCliente').value = '';
    document.getElementById('telefonoCliente').value = '';
    
    document.getElementById('reservaModal').style.display = 'block';
}

function setupModals() {
    const modal = document.getElementById('reservaModal');
    const successModal = document.getElementById('successModal');
    const closeBtn = document.querySelector('.close');
    
    closeBtn.onclick = () => modal.style.display = 'none';
    
    window.onclick = (event) => {
        if (event.target === modal) modal.style.display = 'none';
        if (event.target === successModal) successModal.style.display = 'none';
    };
}

function setupFormListeners() {
    const form = document.getElementById('reservaForm');
    const fechaInicio = document.getElementById('fechaInicio');
    const fechaFin = document.getElementById('fechaFin');
    
    fechaInicio.addEventListener('change', calcularPrecio);
    fechaFin.addEventListener('change', calcularPrecio);
    
    form.addEventListener('submit', enviarReserva);
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
            return;
        }
        
        document.getElementById('noches').textContent = data.noches;
        document.getElementById('precioBase').textContent = `$${data.precio_base}`;
        document.getElementById('precioTotal').textContent = `$${data.precio_total}`;
        
        const descuentoRow = document.getElementById('descuentoRow');
        if (data.descuento > 0) {
            descuentoRow.style.display = 'flex';
            document.getElementById('descuento').textContent = `-$${data.descuento}`;
        } else {
            descuentoRow.style.display = 'none';
        }
        
        document.getElementById('precioSection').style.display = 'block';
        
    } catch (error) {
        console.error('Error calculando precio:', error);
    }
}

// ==================== ENVIAR RESERVA ====================
async function enviarReserva(e) {
    e.preventDefault();
    
    const datos = {
        domo_id: document.getElementById('domoId').value,
        fecha_inicio: document.getElementById('fechaInicio').value,
        fecha_fin: document.getElementById('fechaFin').value,
        nombre_cliente: document.getElementById('nombreCliente').value,
        email_cliente: document.getElementById('emailCliente').value,
        telefono_cliente: document.getElementById('telefonoCliente').value
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
        mostrarError('Error al crear la reserva');
    }
}

// ==================== MENSAJES ====================
function mostrarError(mensaje) {
    alert('❌ ' + mensaje);
}

function mostrarExito(data) {
    const modal = document.getElementById('reservaModal');
    const successModal = document.getElementById('successModal');
    const mensaje = document.getElementById('successMessage');
    
    mensaje.innerHTML = `
        <p><strong>${selectedDomo.nombre}</strong></p>
        <p>Entrada: ${document.getElementById('fechaInicio').value}</p>
        <p>Salida: ${document.getElementById('fechaFin').value}</p>
        <p style="margin-top: 15px; font-size: 18px; color: var(--color-primary);"><strong>Total: $${document.getElementById('precioTotal').textContent.replace('$', '')}</strong></p>
        <p style="margin-top: 15px; font-size: 13px;">Te enviaremos un email de confirmación a ${document.getElementById('emailCliente').value}</p>
    `;
    
    modal.style.display = 'none';
    successModal.style.display = 'block';
}
