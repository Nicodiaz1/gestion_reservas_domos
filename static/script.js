// ==================== VARIABLES GLOBALES ====================
let domos = [];
let selectedDomo = null;
let fechasOcupadas = [];        // Fechas completamente ocupadas (rojo)
let fechasCheckout = [];        // Fechas de salida (disponibles como entrada siguiente)
let fechasInicioReserva = [];   // Fechas de inicio de reservas (disponibles como fecha_fin)
let calendarioMes = new Date();
let fechaInicioTemp = null;
let fechaFinTemp = null;

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
    
    // URLs de las imágenes de los domos desde Imgur
    const imagenes = [
        'https://i.imgur.com/cfLIaDz.jpg',  // Domo 1 - Aguaribay
        'https://i.imgur.com/ZeWzC9v.jpg',  // Domo 2 - Espinillo
        'https://i.imgur.com/lUI8A1z.jpg'   // Domo 3 - Eucalipto
    ];
    const imagenUrl = imagenes[(domo.id - 1) % 3];
    
    div.innerHTML = `
        <div class="domo-image">
            <img src="${imagenUrl}" alt="${domo.nombre}" style="width: 100%; height: 100%; object-fit: cover;">
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
    
    // Cargar fechas ocupadas y checkouts
    try {
        const res = await fetch(`/api/disponibilidad/${domoId}`);
        const data = await res.json();
        fechasOcupadas = data.ocupadas || [];
        fechasCheckout = data.checkouts || [];
        fechasInicioReserva = data.inicios || [];
    } catch (error) {
        console.error('Error cargando disponibilidad:', error);
        fechasOcupadas = [];
        fechasCheckout = [];
        fechasInicioReserva = [];
    }
    
    // Inicializar calendario único
    calendarioMes = new Date();
    fechaInicioTemp = null;
    fechaFinTemp = null;
    
    construirCalendario();
    
    document.getElementById('reservaModal').style.display = 'block';
}

// ==================== CONSTRUIR CALENDARIO ====================
function construirCalendario() {
    const mes = calendarioMes;
    const container = document.getElementById('calendario');
    
    container.innerHTML = `
        <div class="calendario-header">
            <button type="button" onclick="cambiarMes(-1)">← Anterior</button>
            <h3>${mes.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' })}</h3>
            <button type="button" onclick="cambiarMes(1)">Siguiente →</button>
        </div>
        <div class="calendario-weekdays">
            <div>L</div><div>M</div><div>X</div><div>J</div><div>V</div><div>S</div><div>D</div>
        </div>
        <div class="calendario-days" id="dias"></div>
    `;
    
    // Llenar días
    const primerDia = new Date(mes.getFullYear(), mes.getMonth(), 1);
    const ultimoDia = new Date(mes.getFullYear(), mes.getMonth() + 1, 0);
    const diasContainer = document.getElementById('dias');
    
    // Días del mes anterior
    const inicioDia = primerDia.getDay() === 0 ? 6 : primerDia.getDay() - 1;
    for (let i = inicioDia - 1; i >= 0; i--) {
        const fecha = new Date(primerDia);
        fecha.setDate(fecha.getDate() - i - 1);
        const btn = document.createElement('button');
        btn.className = 'calendario-day otro-mes';
        btn.textContent = fecha.getDate();
        btn.type = 'button';
        btn.disabled = true;
        diasContainer.appendChild(btn);
    }
    
    // Días del mes actual
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    
    for (let d = 1; d <= ultimoDia.getDate(); d++) {
        const fecha = new Date(mes.getFullYear(), mes.getMonth(), d);
        const fechaStr = fecha.toISOString().split('T')[0];
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = d;
        btn.className = 'calendario-day';
        
        const esPasada = fecha < hoy;
        const estaOcupada = fechasOcupadas.includes(fechaStr);
        const esCheckout = fechasCheckout.includes(fechaStr);
        const esInicioReserva = fechasInicioReserva.includes(fechaStr);
        
        if (esPasada) {
            btn.classList.add('pasada');
            btn.disabled = true;
        } else if (esInicioReserva && esCheckout) {
            // Día con checkout y checkin: no hay medio día libre
            btn.classList.add('reserved');
            btn.disabled = false;
            btn.onclick = () => seleccionarFechaRango(fechaStr);
        } else if (esInicioReserva) {
            // Día de inicio: mitad verde/rojo (se puede terminar otra reserva ese día)
            btn.classList.add('checkin');
            btn.disabled = false;
            btn.onclick = () => seleccionarFechaRango(fechaStr);
        } else if (esCheckout) {
            // Día de checkout: mitad verde/rojo (se puede iniciar otra reserva ese día)
            btn.classList.add('checkout');
            btn.disabled = false;
            btn.onclick = () => seleccionarFechaRango(fechaStr);
        } else if (estaOcupada) {
            // Noche ocupada completa
            btn.classList.add('reserved');
            btn.disabled = false;
            btn.onclick = () => seleccionarFechaRango(fechaStr);
        } else {
            btn.disabled = false;
            btn.onclick = () => seleccionarFechaRango(fechaStr);
        }
        
        // Marcar si está en el rango seleccionado
        if (fechaInicioTemp && fechaFinTemp) {
            const inicio = new Date(fechaInicioTemp);
            const fin = new Date(fechaFinTemp);
            if (fecha > inicio && fecha < fin) {
                btn.classList.add('rango');
            } else if (fechaStr === fechaInicioTemp) {
                btn.classList.add('rango-inicio');
            } else if (fechaStr === fechaFinTemp) {
                btn.classList.add('rango-fin');
            }
        }
        
        diasContainer.appendChild(btn);
    }
    
    // Días del mes siguiente
    const diasRestantes = 7 - ((inicioDia + ultimoDia.getDate()) % 7);
    if (diasRestantes < 7) {
        for (let i = 1; i <= diasRestantes; i++) {
            const btn = document.createElement('button');
            btn.className = 'calendario-day otro-mes';
            btn.textContent = i;
            btn.type = 'button';
            btn.disabled = true;
            diasContainer.appendChild(btn);
        }
    }
}

// ==================== CAMBIAR MES ====================
function cambiarMes(incremento) {
    calendarioMes.setMonth(calendarioMes.getMonth() + incremento);
    construirCalendario();
}

// ==================== SELECCIONAR RANGO DE FECHAS ====================
function seleccionarFechaRango(fechaStr) {
    // Si hace clic en la misma fecha seleccionada, desselecciona
    if (fechaStr === fechaInicioTemp && !fechaFinTemp) {
        fechaInicioTemp = null;
        document.getElementById('fechaInicio-display').textContent = 'Seleccionar';
        document.getElementById('fechaInicio').value = '';
        construirCalendario();
        return;
    }
    
    if (fechaStr === fechaFinTemp) {
        fechaFinTemp = null;
        document.getElementById('fechaFin-display').textContent = 'Seleccionar';
        document.getElementById('fechaFin').value = '';
        construirCalendario();
        return;
    }
    
    if (!fechaInicioTemp) {
        // Primera selección: fecha de inicio
        // Validar que no esté completamente ocupada (no es la fecha final de otra reserva)
        // Pero SÍ permite si es la fecha final de otra (checkout/checkin mismo día)
        fechaInicioTemp = fechaStr;
        fechaFinTemp = null;
        
        document.getElementById('fechaInicio').value = fechaStr;
        const [year, month, day] = fechaStr.split('-');
        const fecha = new Date(year, month - 1, day);
        const fechaFormato = fecha.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
        document.getElementById('fechaInicio-display').textContent = fechaFormato;
        
    } else if (!fechaFinTemp) {
        // Segunda selección: fecha de fin
        const inicio = new Date(fechaInicioTemp);
        const fin = new Date(fechaStr);
        
        if (fin <= inicio) {
            // Si selecciona una fecha anterior, es la nueva fecha de inicio
            fechaInicioTemp = fechaStr;
            fechaFinTemp = null;
            
            document.getElementById('fechaInicio').value = fechaStr;
            const [year, month, day] = fechaStr.split('-');
            const fecha = new Date(year, month - 1, day);
            const fechaFormato = fecha.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
            document.getElementById('fechaInicio-display').textContent = fechaFormato;
            document.getElementById('fechaFin-display').textContent = 'Seleccionar';
        } else {
            fechaFinTemp = fechaStr;
            
            document.getElementById('fechaFin').value = fechaStr;
            const [year, month, day] = fechaStr.split('-');
            const fecha = new Date(year, month - 1, day);
            const fechaFormato = fecha.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
            document.getElementById('fechaFin-display').textContent = fechaFormato;
        }
    }
    
    construirCalendario();
    validarFechasReservadas();
    calcularPrecio();
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
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;
    
    if (!fechaInicio || !fechaFin) return;
    
    const inicio = new Date(fechaInicio);
    const fin = new Date(fechaFin);
    
    let fechaActual = new Date(inicio);
    let hayConflicto = false;
    
    // Validar que NO haya conflicto en las fechas de estadía
    // Permite que fecha_fin sea igual a fecha_inicio de otra reserva (checkout/checkin mismo día)
    while (fechaActual < fin) {
        const fechaStr = fechaActual.toISOString().split('T')[0];
        if (fechasOcupadas.includes(fechaStr)) {
            hayConflicto = true;
            break;
        }
        fechaActual.setDate(fechaActual.getDate() + 1);
    }
    
    if (hayConflicto) {
        mostrarError('Algunas fechas seleccionadas ya están reservadas (se muestran en rojo)');
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
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;
    
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
    
    // Verificar que las fechas estén completas
    if (!fechaInicio || !fechaFin) {
        mostrarError('Debes seleccionar ambas fechas');
        return;
    }
    
    const datos = {
        domo_id: parseInt(document.getElementById('domoId').value),
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
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
    const mensajeWhatsapp = `Hola quiero confirmar mi reserva para ${nombreCliente} en las fechas ${fechaInicio} al ${fechaFin}`;
    const whatsappLink = `https://wa.me/5493513433116?text=${encodeURIComponent(mensajeWhatsapp)}`;
    
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
