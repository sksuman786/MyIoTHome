/* MyHome IoT - Main JavaScript */

// Theme Management
function initTheme() {
    const theme = localStorage.getItem('theme') || 'light';
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
        updateThemeToggle();
    }
}

function toggleTheme() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    updateThemeToggle();
}

function updateThemeToggle() {
    const btn = document.getElementById('themeToggle');
    if (btn) {
        if (document.body.classList.contains('dark-mode')) {
            btn.innerHTML = '<i class="fas fa-sun"></i>';
            btn.title = 'Switch to Light Mode';
        } else {
            btn.innerHTML = '<i class="fas fa-moon"></i>';
            btn.title = 'Switch to Dark Mode';
        }
    }
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    setupThemeToggle();
    loadInitialData();

    // Attach toggle handlers to any appliance checkboxes on static pages like Rooms
    if (document.querySelector('.appliance-toggle')) {
        setupApplianceToggles();
    }
});

function setupThemeToggle() {
    const btn = document.getElementById('themeToggle');
    if (btn) {
        btn.addEventListener('click', toggleTheme);
    }
}

// WebSocket support is disabled for this deployment because Channels/ASGI is not configured.
// The dashboard loads appliance data via normal HTTP requests.

// Data Loading
function loadInitialData() {
    // Load dashboard data
    if (document.getElementById('appliancesContainer')) {
        loadDashboardData();
    }
}

function loadDashboardData() {
    fetch('/dashboard/api/data/')
        .then(response => response.json())
        .then(data => {
            renderAppliances(data.rooms);
            setupApplianceToggles();
        })
        .catch(error => console.error('Error loading data:', error));
}

function renderAppliances(rooms) {
    const container = document.getElementById('appliancesContainer');
    if (!container) return;
    
    container.innerHTML = '';
    let totalAppliances = 0;
    
    for (const [room, appliances] of Object.entries(rooms)) {
        // Add room header
        const roomHeader = document.createElement('div');
        roomHeader.className = 'col-12 mb-3 mt-4';
        roomHeader.innerHTML = `<h5 class="text-muted border-bottom pb-2"><i class="fas fa-door-open me-2"></i>${room}</h5>`;
        container.appendChild(roomHeader);
        
        // Add appliance cards
        const row = document.createElement('div');
        row.className = 'row';
        
        appliances.forEach(appliance => {
            totalAppliances++;
            const card = document.createElement('div');
            card.className = 'col-md-6 col-lg-4 mb-3';
            
            // Determine appliance type and render accordingly
            let controlHtml = '';
            let statusHtml = '';
            
            if (appliance.appliance_type === 'slider') {
                // Slider control (0-255)
                const value = appliance.value !== null ? appliance.value : 0;
                controlHtml = `
                    <div class="slider-container">
                        <input type="range" class="form-range appliance-slider" 
                               min="0" max="255" value="${value}" 
                               data-appliance-id="${appliance.id}">
                        <div class="slider-value mt-2 text-center">
                            <span class="badge bg-info slider-value-display">${value}</span>
                        </div>
                    </div>
                `;
                statusHtml = '';
            } else if (appliance.appliance_type === 'display') {
                // Display (read-only)
                const value = appliance.value !== null ? appliance.value : appliance.state;
                controlHtml = `
                    <div class="text-center display-container">
                        <h3 class="badge bg-info" style="font-size: 1.5rem;">${value}</h3>
                    </div>
                `;
                statusHtml = '';
            } else {
                // Standard toggle switch
                const statusText = appliance.state === 1 ? 'ON' : 'OFF';
                const statusBadge = appliance.state === 1 ? 'bg-success' : 'bg-secondary';
                
                controlHtml = `
                    <div class="form-check form-switch">
                        <input class="form-check-input appliance-toggle" type="checkbox" 
                               ${appliance.state === 1 ? 'checked' : ''} 
                               data-appliance-id="${appliance.id}">
                    </div>
                `;
                statusHtml = `<span class="badge ${statusBadge}">${statusText}</span>`;
            }
            
            card.innerHTML = `
                <div class="card appliance-card shadow-sm border-0" data-appliance-id="${appliance.id}">
                    <div class="card-body">
                        <div class="d-flex align-items-center justify-content-between mb-3">
                            <div>
                                <h6 class="card-title mb-1">${appliance.name}</h6>
                                <p class="text-muted small mb-0">${room} · ${appliance.device_name}</p>
                            </div>
                            <div class="appliance-icon">
                                <i class="fas ${appliance.icon}"></i>
                            </div>
                        </div>
                        
                        <div class="d-flex align-items-center justify-content-between">
                            ${controlHtml}
                            ${statusHtml}
                        </div>
                        
                        <small class="text-muted d-block mt-3">
                            Last: ${new Date(appliance.last_updated).toLocaleTimeString()}
                        </small>
                    </div>
                </div>
            `;
            row.appendChild(card);
        });
        
        container.appendChild(row);
    }
    
    if (totalAppliances === 0) {
        container.innerHTML = '<div class="col-12"><div class="alert alert-info text-center"><i class="fas fa-info-circle"></i> No appliances configured.</div></div>';
    }
    
    document.getElementById('totalAppliances').textContent = totalAppliances;
}

function setupApplianceToggles() {
    // Setup toggle switches
    const toggles = document.querySelectorAll('.appliance-toggle');
    toggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const applianceId = this.dataset.applianceId;
            const state = this.checked ? 1 : 0;
            toggleAppliance(applianceId, state, null);
        });
    });
    
    // Setup sliders
    const sliders = document.querySelectorAll('.appliance-slider');
    sliders.forEach(slider => {
        // Update display value on input
        slider.addEventListener('input', function() {
            const valueDisplay = this.closest('.slider-container').querySelector('.slider-value-display');
            if (valueDisplay) {
                valueDisplay.textContent = this.value;
            }
        });
        
        // Send value on change
        slider.addEventListener('change', function() {
            const applianceId = this.dataset.applianceId;
            const value = parseInt(this.value);
            toggleAppliance(applianceId, null, value);
        });
    });
}

function toggleAppliance(applianceId, state, value) {
    if (!applianceId) {
        showNotification('Unable to toggle appliance: missing appliance ID', 'danger');
        return;
    }

    const url = `/devices/appliances/${encodeURIComponent(applianceId)}/set_state/`;
    const payload = JSON.stringify(value !== null ? {value: value} : {state: state});
    console.log('Updating appliance', applianceId, 'state', state, 'value', value, 'url', url);

    fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: payload
    })
    .then(async response => {
        if (response.status === 404) {
            return retryToggle(applianceId, state, value);
        }
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || data.message || 'Failed to update appliance');
        }
        return data;
    })
    .then(data => {
        let message;
        if (value !== null) {
            message = data.message || `Appliance ${data.name || applianceId} set to ${value}`;
        } else {
            message = data.message || `Appliance ${data.name || applianceId} turned ${state === 1 ? 'ON' : 'OFF'}`;
        }
        showNotification(message, 'success');
        refreshApplianceControl(applianceId, state, value);
    })
    .catch(error => {
        showNotification('Error updating appliance: ' + error.message, 'danger');
        console.error('Error:', error);
        // Revert UI on error
        const slider = document.querySelector(`.appliance-slider[data-appliance-id="${applianceId}"]`);
        const toggle = document.querySelector(`.appliance-toggle[data-appliance-id="${applianceId}"]`);
        if (slider) {
            // Reload to get original value
            loadDashboardData();
        }
        if (toggle) {
            toggle.checked = !state;
        }
    });
}

function retryToggle(applianceId, state, value) {
    const url = `/devices/appliances/${encodeURIComponent(applianceId)}/toggle/`;
    return fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || data.message || 'Failed to toggle appliance');
        }
        return data;
    })
    .then(data => {
        const successState = data.state === 1 ? 1 : 0;
        refreshApplianceControl(applianceId, successState, value);
        return data;
    });
}

function refreshApplianceControl(applianceId, state, value) {
    const slider = document.querySelector(`.appliance-slider[data-appliance-id="${applianceId}"]`);
    const toggle = document.querySelector(`.appliance-toggle[data-appliance-id="${applianceId}"]`);
    
    if (slider) {
        // Update slider value
        if (value !== null) {
            slider.value = value;
            const valueDisplay = slider.closest('.slider-container').querySelector('.slider-value-display');
            if (valueDisplay) {
                valueDisplay.textContent = value;
            }
        }
    }
    
    if (toggle) {
        // Update toggle
        if (state !== null) {
            toggle.checked = state === 1;
        }
        const card = toggle.closest('.card');
        if (card) {
            const badge = card.querySelector('.badge');
            if (badge && state !== null) {
                badge.textContent = state === 1 ? 'ON' : 'OFF';
                badge.classList.toggle('bg-success', state === 1);
                badge.classList.toggle('bg-secondary', state === 0);
            }
        }
    }
}

function refreshApplianceToggle(applianceId, state) {
    const checkbox = document.querySelector(`.appliance-toggle[data-appliance-id="${applianceId}"]`);
    if (checkbox) {
        checkbox.checked = state === 1;
        const card = checkbox.closest('.card');
        if (card) {
            const badge = card.querySelector('.badge');
            if (badge) {
                badge.textContent = state === 1 ? 'ON' : 'OFF';
                badge.classList.toggle('bg-success', state === 1);
                badge.classList.toggle('bg-secondary', state === 0);
            }
        }
    }
}

// Notifications
function showNotification(message, type = 'info', duration = 3000) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const container = document.querySelector('.main-content');
    if (container) {
        const wrapper = document.createElement('div');
        wrapper.className = 'container-fluid mt-3';
        wrapper.innerHTML = alertHtml;
        container.insertBefore(wrapper, container.firstChild);
        
        setTimeout(() => wrapper.remove(), duration);
    }
}

// Device Status Update
function updateDeviceStatus(data) {
    // Update device status on the page
    console.log('Device status updated:', data);
}

function updateApplianceState(data) {
    // Update appliance state on the page
    console.log('Appliance state updated:', data);
}

// Utility Functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString();
}

// Auto-refresh every 30 seconds is disabled because WebSocket support is not configured.
// If needed later, replace this with a normal HTTP polling implementation.
