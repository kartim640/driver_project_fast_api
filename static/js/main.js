// File upload handling
const dropZone = document.querySelector('.drop-zone');
const fileInput = dropZone.querySelector('input[type="file"]');

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-active');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-active');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-active');
    fileInput.files = e.dataTransfer.files;
});

// File deletion
async function deleteFile(fileId) {
    if (!confirm('Are you sure you want to delete this file?')) {
        return;
    }

    try {
        const response = await fetch(`/file/${fileId}`, {
            method: 'DELETE',
        });

        if (response.ok) {
            // Reload the page to update the file list
            window.location.reload();
        } else {
            const data = await response.json();
            alert(data.message || 'Error deleting file');
        }
    } catch (error) {
        alert('Error deleting file');
    }
}