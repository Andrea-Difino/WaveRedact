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


async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("level", getActiveSecurityLevel());
    formData.append("censor_mode", getActiveCensorMode());

    try {
        const response = await fetch("http://127.0.0.1:8000/api/v1/audio/process", {
            method: "POST",
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            console.log("Processing completed:", data);


        } else {
            console.error("Error in server elaboration.");
        }
    } catch (error) {
        console.error("Network or offline server error:", error);
    } finally {
        event.target.value = "";
    }
}