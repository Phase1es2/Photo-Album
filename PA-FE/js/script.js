// ----------------------------------------------------
// Initialize API Gateway Client
// ----------------------------------------------------
var apigClient = apigClientFactory.newClient();

// ----------------------------------------------------
// Upload UI logic
// ----------------------------------------------------
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const preview = document.getElementById('file-preview');
const placeholder = document.getElementById('upload-placeholder');

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelect();
    }
});
fileInput.addEventListener('change', handleFileSelect);

function handleFileSelect() {
    const file = fileInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
        preview.src = e.target.result;
        preview.style.display = 'inline-block';
        placeholder.style.display = 'none';
    };
    reader.readAsDataURL(file);
}

// ----------------------------------------------------
// Toast helper
// ----------------------------------------------------
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.className = `show ${type}`;
    toast.innerText = message;
    setTimeout(() => { toast.className = toast.className.replace('show', ''); }, 3000);
}

// ----------------------------------------------------
// Upload Photo API
// ----------------------------------------------------
function uploadPhoto() {
    const file = fileInput.files[0];
    const btn = document.getElementById('upload-btn');

    if (!file) {
        showToast('Please select an image first.', 'error');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spinner"></i> PROCESSING...';

    var params = {};
    var body = file;
    var additionalParams = { headers: { 'Content-Type': file.type } };

    apigClient.uploadPhotoPut(params, body, additionalParams)
        .then(result => {
            showToast('Photo successfully archived.');
            fileInput.value = '';
            preview.style.display = 'none';
            placeholder.style.display = 'block';
        })
        .catch(error => {
            console.error(error);
            showToast('Upload failed.', 'error');
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerText = 'PUBLISH PHOTO';
        });
}

// ----------------------------------------------------
// Search Photos API
// ----------------------------------------------------
function searchPhotos() {
    const query = document.getElementById('search-query').value;
    const resultsArea = document.getElementById('results-area');
    const searchBtn = document.querySelector('.search-btn');

    if (!query) {
        showToast('Please enter criteria.', 'error');
        return;
    }

    searchBtn.innerHTML = '<i class="fas fa-circle-notch fa-spinner"></i>';
    resultsArea.innerHTML = '';

    apigClient.searchPhotosGet({ q: query }, {}, {})
        .then(result => {
            const data = result.data;
            if (data.results && data.results.length > 0) {
                data.results.forEach(photo => {
                    const div = document.createElement('div');
                    div.className = 'photo-frame';
                    div.innerHTML = `<img src="${photo.url}" alt="Gallery Print">`;
                    resultsArea.appendChild(div);
                });
                showToast(`${data.results.length} prints found.`);
            } else {
                showToast('No photos matched.', 'error');
            }
        })
        .catch(error => {
            console.error(error);
            showToast('Search failed.', 'error');
        })
        .finally(() => {
            searchBtn.innerHTML = '<i class="fas fa-arrow-right"></i>';
        });
}

document.getElementById('search-query').addEventListener('keypress', e => {
    if (e.key === 'Enter') searchPhotos();
});