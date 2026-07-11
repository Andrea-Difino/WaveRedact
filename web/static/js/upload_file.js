let socket = null;

function startProcess() {
    document.getElementById('audioInput').click();
}

function getActiveSecurityLevel() {
    const activeLevelButton = document.querySelector('.security-tabs button.active');
    return activeLevelButton?.value || 'total';
}

function getActiveCensorMode() {
    const activeModeButton = document.querySelector('.mode-tabs button.active');
    return activeModeButton?.value || 'muted';
}

const levelLabels = {
    base: [
        "password", "api_key", "secret", "access_token", "recovery_code",
        "iban", "bank_account", "account_number", "routing_number",
        "payment_card", "card_number", "card_expiry", "card_cvv"
    ],
    medium: [
        "person", "full_name", "first_name", "middle_name", "last_name",
        "username", "email", "phone_number", "ip_address", "account_id",
        "sensitive_account_id", "government_id", "national_id_number",
        "passport_number", "drivers_license_number", "tax_id", "tax_number",
        "date_of_birth"
    ],
    total: [
        "address", "street_address", "city", "state_or_region", "postal_code",
        "country", "sensitive_date", "document_date", "expiration_date",
        "transaction_date", "license_number"
    ]
};

function refreshLabels() {
    setTimeout(() => {
        const level = getActiveSecurityLevel();
        const container = document.getElementById('labelsContainer');
        if (!container) return;

        let html = '';

        // Base group
        const isBaseHighlight = level === 'base';
        html += `<div class="label-group">
            <h5>${isBaseHighlight ? 'Base Level Labels' : '✓ Base Level (Included)'}</h5>
            <div class="labels-content">
                ${levelLabels.base.map(l => `<span class="label-badge ${isBaseHighlight ? 'highlight' : 'muted'}">${l}</span>`).join('')}
            </div>
        </div>`;

        // Medium group
        if (level === 'medium' || level === 'total') {
            const isMediumHighlight = level === 'medium';
            html += `<div class="label-group">
                <h5>${isMediumHighlight ? '+ Deep Level Additions' : '✓ Deep Level (Included)'}</h5>
                <div class="labels-content">
                    ${levelLabels.medium.map(l => `<span class="label-badge ${isMediumHighlight ? 'highlight' : 'muted'}">${l}</span>`).join('')}
                </div>
            </div>`;
        }

        // Total group
        if (level === 'total') {
            html += `<div class="label-group">
                <h5>+ Tsunami Level Additions</h5>
                <div class="labels-content">
                    ${levelLabels.total.map(l => `<span class="label-badge highlight">${l}</span>`).join('')}
                </div>
            </div>`;
        }

        container.innerHTML = html;
    }, 50);
}

function toggleInfoPanel() {
    const panel = document.getElementById('sideInfoPanel');
    if (panel) {
        if (panel.classList.contains('open')) {
            panel.classList.remove('open');
        } else {
            refreshLabels();
            panel.classList.add('open');
        }
    }
}

function updateProgress(msg, percent) {
    const statusEl = document.getElementById('processingStatus');
    if (statusEl) {
        statusEl.innerHTML = msg;
    }
    if (percent !== undefined && percent !== null) {
        const barEl = document.getElementById('progressBar');
        if (barEl) {
            barEl.style.width = percent + '%';
        }
    }
}

function showProcessingPanel() {
    document.getElementById('setupPanel').style.display = 'none';
    document.getElementById('processingPanel').style.display = 'flex';
    const barContainer = document.querySelector('.progress-bar-container');
    if (barContainer) barContainer.style.display = 'block';
    const barEl = document.getElementById('progressBar');
    if (barEl) barEl.style.width = '0%';
}

function hideProcessingPanel() {
    document.getElementById('setupPanel').style.display = 'flex';
    document.getElementById('processingPanel').style.display = 'none';
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const clientId = Math.random().toString(36).substring(2, 15);

    const wsUrl = `ws://${window.location.host}/api/v1/ws/${clientId}`;
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        showProcessingPanel();
        updateProgress("Starting upload...");
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.status === 'progress' && data.message) {
                updateProgress(data.message, data.percent);
            }
        } catch (e) { }
    };

    const formData = new FormData();
    formData.append("file", file);
    formData.append("level", getActiveSecurityLevel());
    formData.append("censor_mode", getActiveCensorMode());
    formData.append("client_id", clientId);

    try {
        const response = await fetch("/api/v1/audio/process", {
            method: "POST",
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            const wordsCount = data.sensitive_words ? data.sensitive_words.length : 0;
            updateProgress(`Processing completed!<br>Removed ${wordsCount} sensitive words.`, 100);

            const barContainer = document.querySelector('.progress-bar-container');
            if (barContainer) {
                barContainer.style.display = 'none';
            }

            const actionContainer = document.getElementById('actionContainer');
            if (actionContainer) {
                actionContainer.style.display = 'flex';
                actionContainer.style.gap = '16px';
                actionContainer.innerHTML = '';

                if (data.download_url) {
                    const downloadBtn = document.createElement('button');
                    downloadBtn.className = 'dl-btn';
                    downloadBtn.innerHTML = 'Download Audio';
                    downloadBtn.onclick = () => window.location.href = data.download_url;
                    actionContainer.appendChild(downloadBtn);
                }

                const backBtn = document.createElement('button');
                backBtn.className = 'dl-btn';
                backBtn.innerHTML = 'Process Another';
                backBtn.onclick = () => {
                    hideProcessingPanel();
                    actionContainer.style.display = 'none';
                    actionContainer.innerHTML = '';
                    const pulse = document.querySelector('.pulse-ring');
                    if (pulse) pulse.style.display = 'block';
                };
                actionContainer.appendChild(backBtn);
            }

            const pulse = document.querySelector('.pulse-ring');
            if (pulse) pulse.style.display = 'none';

        } else {
            console.error("Error in server elaboration.");
            updateProgress("Error during processing on server.");
            showBackButton();
        }
    } catch (error) {
        console.error("Network or offline server error:", error);
        updateProgress("Network or server offline error.");
        showBackButton();
    } finally {
        event.target.value = "";
        if (socket) {
            socket.close();
        }
    }
}

function showBackButton() {
    const actionContainer = document.getElementById('actionContainer');
    if (actionContainer) {
        actionContainer.style.display = 'flex';
        actionContainer.innerHTML = '';
        const backBtn = document.createElement('button');
        backBtn.className = 'dl-btn';
        backBtn.innerHTML = 'Go Back';
        backBtn.onclick = () => {
            hideProcessingPanel();
            actionContainer.style.display = 'none';
            actionContainer.innerHTML = '';
        };
        actionContainer.appendChild(backBtn);
    }
    const pulse = document.querySelector('.pulse-ring');
    if (pulse) pulse.style.display = 'none';
}