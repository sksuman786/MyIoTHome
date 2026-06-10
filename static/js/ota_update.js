/* OTA Update Dashboard JavaScript */

document.addEventListener('DOMContentLoaded', function() {
    loadUpdates();
});

function uploadFirmware(event) {
    event.preventDefault();

    const deviceId = document.getElementById('deviceSelect').value;
    const version = document.getElementById('firmwareVersion').value;
    const binFile = document.getElementById('binFile').files[0];
    const releaseNotes = document.getElementById('releaseNotes').value;

    if (!deviceId || !version || !binFile) {
        alert('Please fill all required fields (Device, Version, and Binary File)');
        return;
    }

    // Check file size (max 2MB)
    if (binFile.size > 2 * 1024 * 1024) {
        alert('File size exceeds 2MB limit');
        return;
    }

    const formData = new FormData();
    formData.append('device_id', deviceId);
    formData.append('version', version);
    formData.append('bin_file', binFile);
    formData.append('notes', releaseNotes);

    // Show progress
    document.getElementById('uploadProgress').style.display = 'block';
    document.getElementById('uploadForm').style.display = 'none';

    // Simulate upload with XMLHttpRequest for progress tracking
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            const progressBar = document.getElementById('progressBar');
            progressBar.style.width = percentComplete + '%';
            progressBar.textContent = Math.round(percentComplete) + '%';
            document.getElementById('uploadStatus').textContent = `Uploading ${binFile.name}...`;
        }
    });

    xhr.addEventListener('load', () => {
        if (xhr.status === 200 || xhr.status === 201) {
            const response = JSON.parse(xhr.responseText);
            if (response.status === 'success') {
                showNotification('Firmware uploaded successfully!', 'success');
                document.getElementById('uploadForm').reset();
                document.getElementById('uploadProgress').style.display = 'none';
                document.getElementById('uploadForm').style.display = 'block';
                loadUpdates();
            }
        } else {
            const response = JSON.parse(xhr.responseText);
            showNotification('Upload failed: ' + response.message, 'danger');
            document.getElementById('uploadProgress').style.display = 'none';
            document.getElementById('uploadForm').style.display = 'block';
        }
    });

    xhr.addEventListener('error', () => {
        showNotification('Upload error. Please try again.', 'danger');
        document.getElementById('uploadProgress').style.display = 'none';
        document.getElementById('uploadForm').style.display = 'block';
    });

    xhr.open('POST', '/api/ota/upload/');
    xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
    xhr.send(formData);
}

function loadUpdates() {
    fetch('/dashboard/api/ota/updates/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        displayUpdates(data.updates || []);
    })
    .catch(error => {
        console.error('Error loading updates:', error);
        document.getElementById('updatesList').innerHTML = '<p class="text-muted">Failed to load updates</p>';
    });
}

function displayUpdates(updates) {
    const container = document.getElementById('updatesList');
    
    if (updates.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No firmware updates available</p>';
        return;
    }

    let html = '<div class="row">';
    
    updates.forEach(update => {
        const statusClass = `update-card ${update.status}`;
        const statusBadgeClass = `status-badge status-${update.status}`;
        const fileSize = formatFileSize(update.file_size);
        const createdDate = new Date(update.created_at).toLocaleString();
        
        html += `
            <div class="col-md-6 mb-3">
                <div class="card ${statusClass}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div>
                                <h6 class="mb-1">
                                    <i class="fas fa-cloud-upload-alt"></i>
                                    Version ${update.version}
                                </h6>
                                <small class="text-muted">${update.device_name}</small>
                            </div>
                            <span class="${statusBadgeClass}">${update.status.toUpperCase()}</span>
                        </div>
                        
                        <div class="mb-2">
                            <small class="text-muted">
                                <i class="fas fa-calendar"></i> ${createdDate}
                            </small>
                        </div>
                        
                        <div class="mb-2">
                            <small class="text-muted">
                                <i class="fas fa-file"></i> ${fileSize}
                            </small>
                        </div>
        `;

        if (update.status === 'downloading' || update.status === 'pending') {
            html += `
                        <div class="progress mb-2" style="height: 20px;">
                            <div class="progress-bar" role="progressbar" 
                                 style="width: ${update.download_progress}%;" 
                                 aria-valuenow="${update.download_progress}" 
                                 aria-valuemin="0" aria-valuemax="100">
                                ${update.download_progress}%
                            </div>
                        </div>
            `;
        }

        html += `
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Details and deploy actions removed — UI shows only firmware cards. 

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Download action removed from UI; function deleted.

function showNotification(message, type = 'info', duration = 5000) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert" style="margin: 20px;">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    const wrapper = document.createElement('div');
    wrapper.style.position = 'fixed';
    wrapper.style.top = '0';
    wrapper.style.right = '0';
    wrapper.style.zIndex = '9999';
    wrapper.style.maxWidth = '500px';
    wrapper.innerHTML = alertHtml;
    document.body.appendChild(wrapper);

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

// Auto-refresh updates every 60 seconds
setInterval(() => {
    loadUpdates();
}, 60000);
