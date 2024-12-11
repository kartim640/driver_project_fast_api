// File upload handling
const dropZone = document.querySelector('.drop-zone');
const fileInput = document.getElementById('file-input');
const uploadForm = document.querySelector('.upload-form');

// Drag and drop functionality
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drop-zone-drag');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drop-zone-drag');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drop-zone-drag');

    const files = e.dataTransfer.files;
    if (files.length) {
        fileInput.files = files;
        handleFileUpload(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleFileUpload(e.target.files[0]);
    }
});

async function handleFileUpload(file) {
    if (file.size > 100 * 1024 * 1024) {
        alert('File size exceeds 100MB limit');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        const result = await response.json();
        alert(result.message);
        window.location.reload();
    } catch (error) {
        alert(error.message);
    }
}

// File deletion
async function deleteFile(fileId) {
    if (!confirm('Are you sure you want to delete this file?')) {
        return;
    }

    try {
        const response = await fetch(`/file/${fileId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Delete failed');
        }

        window.location.reload();
    } catch (error) {
        alert(error.message);
    }
}