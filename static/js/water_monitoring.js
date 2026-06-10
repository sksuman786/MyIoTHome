/* Water Monitoring Dashboard JavaScript */

let waterChart = null;
let historicalChart = null;
let selectedDeviceId = null;
let timerCountdownInterval = null;
let timerEndTime = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeGauge();
    loadDevices();
});

function initializeGauge() {
    const ctx = document.getElementById('waterGauge');
    if (!ctx) return;

    waterChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [0, 100],
                backgroundColor: [
                    'rgba(13, 110, 253, 0.8)',
                    'rgba(200, 200, 200, 0.2)'
                ],
                borderColor: [
                    'rgb(13, 110, 253)',
                    'rgba(200, 200, 200, 0.5)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: '75%',
            plugins: {
                tooltip: { enabled: false }
            }
        }
    });
}

function loadDevices() {
    const deviceSelect = document.getElementById('deviceSelect');
    if (!deviceSelect) return;

    selectedDeviceId = deviceSelect.value;
    if (selectedDeviceId) {
        loadWaterData();
    }
}

function loadWaterData() {
    const deviceSelect = document.getElementById('deviceSelect');
    if (!deviceSelect) {
        alert('No water monitoring device configured');
        return;
    }

    selectedDeviceId = deviceSelect.value;
    if (!selectedDeviceId) {
        alert('Please select a device to view water data');
        return;
    }

    // Fetch latest water data
    fetch(`/api/device/water/data/get/?device_id=${selectedDeviceId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            displayWaterData(data.data);
            updateChart(data.data);
        } else {
            alert('Error loading water data: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to load water data');
    });

    // Load pump and timer status
    loadPumpAndTimerStatus();
}

function displayWaterData(data) {
    if (!data || data.length === 0) {
        document.getElementById('waterPercentage').textContent = '0';
        document.getElementById('tdsValue').textContent = '-- ppm';
        document.getElementById('phValue').textContent = '-- pH';
        document.getElementById('tempValue').textContent = '-- °C';
        return;
    }

    const latest = data[0];

    // Update gauge
    const percentage = latest.water_percentage || 0;
    document.getElementById('waterPercentage').textContent = percentage.toFixed(1);
    updateGaugeValue(percentage);

    // Update metrics
    document.getElementById('tdsValue').textContent = (latest.tds || 0).toFixed(1) + ' ppm';
    document.getElementById('phValue').textContent = (latest.ph || 0).toFixed(2) + ' pH';
    document.getElementById('tempValue').textContent = (latest.temperature || 0).toFixed(1) + ' °C';

    // Update table
    updateDataTable(data);
}

function updateGaugeValue(value) {
    if (waterChart) {
        waterChart.data.datasets[0].data = [value, 100 - value];
        waterChart.update();
    }
}

function updateDataTable(data) {
    const tbody = document.getElementById('dataTableBody');
    tbody.innerHTML = '';

    data.forEach(record => {
        const row = document.createElement('tr');
        const timestamp = new Date(record.timestamp).toLocaleString();
        row.innerHTML = `
            <td>${timestamp}</td>
            <td>${parseFloat(record.water_percentage).toFixed(1)}%</td>
            <td>${parseFloat(record.tds).toFixed(1)}</td>
            <td>${parseFloat(record.ph).toFixed(2)}</td>
            <td>${parseFloat(record.temperature).toFixed(1)}</td>
        `;
        tbody.appendChild(row);
    });
}

function updateChart(data) {
    const labels = data.map(d => new Date(d.timestamp).toLocaleTimeString()).reverse();
    const waterLevels = data.map(d => d.water_percentage).reverse();
    const tdsValues = data.map(d => d.tds).reverse();
    const phValues = data.map(d => d.ph).reverse();
    const temps = data.map(d => d.temperature).reverse();

    const ctx = document.getElementById('historicalChart');
    if (!ctx) return;

    if (historicalChart) {
        historicalChart.destroy();
    }

    historicalChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Water Level (%)',
                    data: waterLevels,
                    borderColor: 'rgb(13, 110, 253)',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.3,
                    yAxisID: 'y'
                },
                {
                    label: 'TDS (ppm)',
                    data: tdsValues,
                    borderColor: 'rgb(102, 51, 153)',
                    backgroundColor: 'rgba(102, 51, 153, 0.1)',
                    tension: 0.3,
                    yAxisID: 'y1'
                },
                {
                    label: 'pH Level',
                    data: phValues,
                    borderColor: 'rgb(255, 159, 64)',
                    backgroundColor: 'rgba(255, 159, 64, 0.1)',
                    tension: 0.3,
                    yAxisID: 'y3'
                },
                {
                    label: 'Temperature (°C)',
                    data: temps,
                    borderColor: 'rgb(220, 53, 69)',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    tension: 0.3,
                    yAxisID: 'y2'
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Water Level (%)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'TDS (ppm)'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                },
                y2: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Temperature (°C)'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                },
                y3: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'pH Level'
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    min: 0,
                    max: 14
                }
            }
        }
    });
}

function saveTimer(event) {
    event.preventDefault();

    const hours = parseInt(document.getElementById('timerHours').value);
    const minutes = parseInt(document.getElementById('timerMinutes').value);
    const seconds = parseInt(document.getElementById('timerSeconds').value);
    const isActive = document.getElementById('timerActive').checked;

    if (!selectedDeviceId) {
        alert('Please select a device');
        return;
    }
    
    // Confirmation before saving timer
    if (!confirm(`Save timer for ${hours}h ${minutes}m ${seconds}s?`)) {
        return;
    }

    console.log('Saving timer:', {hours, minutes, seconds, isActive, selectedDeviceId});

    fetch('/api/water/pump/timer/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            device_id: selectedDeviceId,
            hours: hours,
            minutes: minutes,
            seconds: seconds,
            is_active: isActive
        })
    })
    .then(response => {
        console.log('Save timer response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Save timer response:', data);
        if (data.status === 'success') {
            showNotification('Timer saved successfully', 'success');
            loadPumpAndTimerStatus();
        } else {
            showNotification('Error saving timer: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving timer:', error);
        showNotification('Failed to save timer: ' + error.message, 'danger');
    });
}

function loadPumpAndTimerStatus() {
    if (!selectedDeviceId) return;

    fetch(`/dashboard/api/water/pump/status/?device_id=${selectedDeviceId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            setPumpStatus(data.pump_state);
            const timer = data.timer;
            document.getElementById('timerHours').value = timer.hours;
            document.getElementById('timerMinutes').value = timer.minutes;
            document.getElementById('timerSeconds').value = timer.seconds;
            document.getElementById('timerActive').checked = timer.is_active;
            
            // Check if timer is running
            if (timer.is_running && timer.remaining_seconds > 0) {
                // Timer is running, show countdown display
                showTimerDisplay();
                timerEndTime = Date.now() + (timer.remaining_seconds * 1000);
                startCountdown();
            } else {
                // Timer is not running, hide countdown display
                hideTimerDisplay();
                if (timerCountdownInterval) {
                    clearInterval(timerCountdownInterval);
                    timerCountdownInterval = null;
                }
                timerEndTime = null;
            }
        }
    })
    .catch(error => console.error('Error:', error));
}

function setPumpStatus(state) {
    const badge = document.getElementById('pumpStatus');
    const isOn = state === 1;
    badge.textContent = isOn ? 'ON' : 'OFF';
    badge.className = `badge bg-${isOn ? 'success' : 'secondary'}`;
}

function deactivateTimer() {
    if (!selectedDeviceId) return;

    const hours = parseInt(document.getElementById('timerHours').value);
    const minutes = parseInt(document.getElementById('timerMinutes').value);
    const seconds = parseInt(document.getElementById('timerSeconds').value);

    fetch('/api/water/pump/timer/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            device_id: selectedDeviceId,
            hours: hours,
            minutes: minutes,
            seconds: seconds,
            is_active: false
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('timerActive').checked = false;
        }
    })
    .catch(error => console.error('Error deactivating timer:', error));
}

function startTimer() {
    if (!selectedDeviceId) {
        alert('Please select a device');
        return;
    }

    const pumpStatusText = document.getElementById('pumpStatus').textContent.trim();
    if (pumpStatusText === 'ON') {
        showNotification('Stop the pump before starting the timer', 'warning');
        return;
    }

    // Confirm starting the timer
    if (!confirm('Start the timer now?')) return;

    console.log('Starting timer for device:', selectedDeviceId);

    fetch('/dashboard/api/water/pump/start/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            device_id: selectedDeviceId
        })
    })
    .then(response => {
        console.log('Timer start response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Timer start response:', data);
        
        if (data.status === 'success') {
            showNotification('Timer started - ' + data.message, 'success');
            
            // Calculate end time based on response data
            const totalSeconds = (data.total_seconds || 0);
            console.log('Total seconds:', totalSeconds);
            timerEndTime = Date.now() + (totalSeconds * 1000);
            console.log('Timer end time set to:', timerEndTime);
            
            // Show countdown display
            showTimerDisplay();
            startCountdown();
        } else {
            showNotification('Error: ' + data.message, 'danger');
            console.error('Timer start error:', data);
        }
    })
    .catch(error => {
        console.error('Error starting timer:', error);
        showNotification('Failed to start timer: ' + error.message, 'danger');
    });
}

function showTimerDisplay() {
    document.getElementById('timerDisplaySection').style.display = 'block';
    document.getElementById('timerForm').style.display = 'none';
}

function hideTimerDisplay() {
    document.getElementById('timerDisplaySection').style.display = 'none';
    document.getElementById('timerForm').style.display = 'block';
}

function startCountdown() {
    // Clear any existing countdown
    if (timerCountdownInterval) {
        clearInterval(timerCountdownInterval);
    }

    // Update immediately
    updateCountdownDisplay();

    // Update every second
    timerCountdownInterval = setInterval(updateCountdownDisplay, 1000);
}

function updateCountdownDisplay() {
    if (!timerEndTime) {
        if (timerCountdownInterval) {
            clearInterval(timerCountdownInterval);
        }
        return;
    }

    const now = Date.now();
    const remainingMs = timerEndTime - now;
    
    if (remainingMs <= 0) {
        // Timer finished
        document.getElementById('timerCountdown').textContent = '00:00:00';
        if (timerCountdownInterval) {
            clearInterval(timerCountdownInterval);
            timerCountdownInterval = null;
        }
        showNotification('Timer completed!', 'success');
        timerEndTime = null;
        hideTimerDisplay();
        loadPumpAndTimerStatus();
        return;
    }

    const totalSeconds = Math.floor(remainingMs / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    const display = String(hours).padStart(2, '0') + ':' + 
                    String(minutes).padStart(2, '0') + ':' + 
                    String(seconds).padStart(2, '0');
    
    document.getElementById('timerCountdown').textContent = display;
}

function stopTimer() {
    if (!selectedDeviceId) return;

    if (!confirm('Stop the running timer?')) return;

    console.log('Stopping timer for device:', selectedDeviceId);

    fetch('/dashboard/api/water/pump/stop/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            device_id: selectedDeviceId
        })
    })
    .then(response => {
        console.log('Stop timer response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Stop timer response:', data);
        console.log('Timer is_running status:', data.is_running);
        
        if (data.status === 'success') {
            showNotification('Timer stopped', 'success');
            if (timerCountdownInterval) {
                clearInterval(timerCountdownInterval);
                timerCountdownInterval = null;
            }
            timerEndTime = null;
            hideTimerDisplay();
            loadPumpAndTimerStatus();
        } else {
            showNotification('Error: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error stopping timer:', error);
        showNotification('Failed to stop timer: ' + error.message, 'danger');
    });
}

function turnOnPump() {
    sendPumpToggle(1);
}

function turnOffPump() {
    sendPumpToggle(0);
}

function sendPumpToggle(state) {
    if (!selectedDeviceId) {
        alert('Please select a device first');
        return;
    }

    // Confirm pump action
    const actionText = state === 1 ? 'Turn ON the pump?' : 'Turn OFF the pump?';
    if (!confirm(actionText)) return;

    fetch('/dashboard/api/water/pump/toggle/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            device_id: selectedDeviceId,
            state: state
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('timerActive').checked = false;
            deactivateTimer();
            showNotification(data.message, 'success');
            console.log('Pump toggle response:', data);
            // Refresh pump and timer status from server to ensure UI is in sync
            setTimeout(() => loadPumpAndTimerStatus(), 500);
        } else {
            showNotification('Error: ' + data.message, 'danger');
            console.error('Pump toggle error:', data);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Failed to update pump state', 'danger');
    });
}

function showNotification(message, type = 'info', duration = 3000) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    const wrapper = document.createElement('div');
    wrapper.className = 'container-fluid mt-3';
    wrapper.innerHTML = alertHtml;
    document.body.insertBefore(wrapper, document.body.firstChild);

    setTimeout(() => wrapper.remove(), duration);
}

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

// Auto-refresh data every 30 seconds
setInterval(() => {
    if (selectedDeviceId) {
        loadWaterData();
    }
}, 30000);
