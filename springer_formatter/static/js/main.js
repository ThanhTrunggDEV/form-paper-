/**
 * Springer LNCS Auto-Formatter
 * Main JavaScript
 */

// State
let currentSession = {
    id: null,
    document: null,
    images: [],
    template: null,
    status: 'ready'
};

let settings = {
    font_family: 'Times New Roman',
    section_numbers: true,
    image_width: 80,
    auto_detect: true,
    auto_caption: true,
    template: 'springer_lncs',
    margins: { top: 2.5, bottom: 2.5, left: 2.5, right: 2.5 },
    line_spacing: 1.0
};

// DOM Elements
const docDropzone = document.getElementById('doc-dropzone');
const imgDropzone = document.getElementById('img-dropzone');
const templateDropzone = document.getElementById('template-dropzone');
const docInput = document.getElementById('doc-input');
const imgInput = document.getElementById('img-input');
const templateInput = document.getElementById('template-input');
const processBtn = document.getElementById('process-btn');
const statusBadge = document.getElementById('status-badge');

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initDropzones();
    initSettings();
    loadSettings();
});

function initDropzones() {
    // Document dropzone
    setupDropzone(docDropzone, docInput, handleDocumentUpload);

    // Images dropzone
    setupDropzone(imgDropzone, imgInput, handleImagesUpload);

    // Template dropzone
    setupDropzone(templateDropzone, templateInput, handleTemplateUpload);
}

function setupDropzone(dropzone, input, handler) {
    // Click to open file dialog
    dropzone.addEventListener('click', () => input.click());

    // Drag events
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handler(files);
        }
    });

    // File input change
    input.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handler(e.target.files);
        }
    });
}

function initSettings() {
    // Image width slider
    const imgWidthSlider = document.getElementById('img-width');
    const imgWidthValue = document.getElementById('img-width-value');

    imgWidthSlider.addEventListener('input', (e) => {
        settings.image_width = parseInt(e.target.value);
        imgWidthValue.textContent = `${e.target.value}%`;
    });

    // Template select
    document.getElementById('template-select')?.addEventListener('change', (e) => {
        settings.template = e.target.value;
    });

    // Font select
    document.getElementById('font-select')?.addEventListener('change', (e) => {
        settings.font_family = e.target.value;
    });

    // Checkboxes
    document.getElementById('section-numbers')?.addEventListener('change', (e) => {
        settings.section_numbers = e.target.checked;
    });

    document.getElementById('auto-detect')?.addEventListener('change', (e) => {
        settings.auto_detect = e.target.checked;
    });

    document.getElementById('auto-caption')?.addEventListener('change', (e) => {
        settings.auto_caption = e.target.checked;
    });

    // Line spacing
    document.getElementById('line-spacing')?.addEventListener('change', (e) => {
        settings.line_spacing = parseFloat(e.target.value);
    });

    // Margins
    ['top', 'bottom', 'left', 'right'].forEach(side => {
        const input = document.getElementById(`margin-${side}`);
        if (input) {
            input.addEventListener('change', (e) => {
                settings.margins[side] = parseFloat(e.target.value);
            });
        }
    });
}

async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        if (response.ok) {
            const data = await response.json();
            settings = { ...settings, ...data };
            applySettingsToUI();
        }
    } catch (error) {
        console.log('Using default settings');
    }
}

function applySettingsToUI() {
    document.getElementById('font-select').value = settings.font_family;
    document.getElementById('template-select').value = settings.template;
    document.getElementById('section-numbers').checked = settings.section_numbers;
    document.getElementById('auto-detect').checked = settings.auto_detect;
    document.getElementById('img-width').value = settings.image_width;
    document.getElementById('img-width-value').textContent = `${settings.image_width}%`;
    document.getElementById('line-spacing').value = settings.line_spacing.toString();

    if (settings.margins) {
        Object.keys(settings.margins).forEach(side => {
            const input = document.getElementById(`margin-${side}`);
            if (input) input.value = settings.margins[side];
        });
    }
}

// ============================================
// File Handlers
// ============================================

function handleDocumentUpload(files) {
    const file = files[0];
    const allowedTypes = ['.docx', '.doc', '.txt'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedTypes.includes(ext)) {
        showToast('Please upload a .docx, .doc, or .txt file', 'error');
        return;
    }

    currentSession.document = file;
    updateDocumentInfo(file);
    updateProcessButton();
}

function handleImagesUpload(files) {
    const allowedTypes = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp'];

    for (const file of files) {
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (allowedTypes.includes(ext)) {
            currentSession.images.push(file);
        }
    }

    updateImagesInfo();
    updateProcessButton();
}

function handleTemplateUpload(files) {
    const file = files[0];
    const allowedTypes = ['.docx', '.docm'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedTypes.includes(ext)) {
        showToast('Please upload a .docx or .docm template', 'error');
        return;
    }

    currentSession.template = file;
    updateTemplateInfo(file);
}

function updateDocumentInfo(file) {
    const docInfo = document.getElementById('doc-info');
    const docName = document.getElementById('doc-name');
    const dropzone = document.getElementById('doc-dropzone');

    docName.textContent = file.name;
    docInfo.style.display = 'flex';
    dropzone.style.display = 'none';
}

function updateImagesInfo() {
    const imagesList = document.getElementById('images-list');
    imagesList.innerHTML = '';

    currentSession.images.forEach((file, index) => {
        const thumb = document.createElement('div');
        thumb.className = 'image-thumb';

        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.alt = file.name;

        const removeBtn = document.createElement('button');
        removeBtn.className = 'btn-remove';
        removeBtn.textContent = '×';
        removeBtn.onclick = () => removeImage(index);

        thumb.appendChild(img);
        thumb.appendChild(removeBtn);
        imagesList.appendChild(thumb);
    });
}

function updateTemplateInfo(file) {
    const templateInfo = document.getElementById('template-info');
    const templateName = document.getElementById('template-name');
    const dropzone = document.getElementById('template-dropzone');

    templateName.textContent = file.name;
    templateInfo.style.display = 'flex';
    dropzone.style.display = 'none';
}

function updateProcessButton() {
    processBtn.disabled = !currentSession.document;
}

// ============================================
// Remove Functions
// ============================================

function removeDocument() {
    currentSession.document = null;

    const docInfo = document.getElementById('doc-info');
    const dropzone = document.getElementById('doc-dropzone');

    docInfo.style.display = 'none';
    dropzone.style.display = 'block';
    docInput.value = '';

    updateProcessButton();
}

function removeImage(index) {
    currentSession.images.splice(index, 1);
    updateImagesInfo();
}

function removeTemplate() {
    currentSession.template = null;

    const templateInfo = document.getElementById('template-info');
    const dropzone = document.getElementById('template-dropzone');

    templateInfo.style.display = 'none';
    dropzone.style.display = 'block';
    templateInput.value = '';
}

// ============================================
// Process Document
// ============================================

async function processDocument() {
    if (!currentSession.document) {
        showToast('Please upload a document first', 'warning');
        return;
    }

    // Show processing section
    showSection('processing');
    updateStatus('Processing', 'processing');

    try {
        // Step 1: Upload files
        updateProcessingStatus('Uploading files...', 20);
        const uploadResult = await uploadFiles();

        if (!uploadResult.success) {
            throw new Error(uploadResult.message || 'Upload failed');
        }

        currentSession.id = uploadResult.session_id;

        // Step 2: Process document
        updateProcessingStatus('Analyzing document structure...', 40);
        await sleep(500);

        updateProcessingStatus('Applying Springer LNCS styles...', 60);
        const processResult = await processFiles();

        if (processResult.status !== 'success') {
            throw new Error(processResult.message || 'Processing failed');
        }

        // Step 3: Get preview
        updateProcessingStatus('Generating preview...', 80);
        await sleep(300);

        const previewResult = await getPreview();

        // Step 4: Show results
        updateProcessingStatus('Complete!', 100);
        await sleep(500);

        showResults(processResult, previewResult);
        updateStatus('Completed', 'success');
        showToast('Document formatted successfully!', 'success');

    } catch (error) {
        console.error('Processing error:', error);
        showToast(error.message || 'An error occurred during processing', 'error');
        updateStatus('Error', 'error');
        showSection('upload');
    }
}

async function uploadFiles() {
    const formData = new FormData();

    if (currentSession.document) {
        formData.append('document', currentSession.document);
    }

    currentSession.images.forEach(img => {
        formData.append('images', img);
    });

    if (currentSession.template) {
        formData.append('template', currentSession.template);
    }

    const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
    });

    const data = await response.json();
    data.success = data.status === 'success';

    return data;
}

async function processFiles() {
    const response = await fetch('/api/process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: currentSession.id,
            settings: settings
        })
    });

    return await response.json();
}

async function getPreview() {
    const response = await fetch(`/api/preview/${currentSession.id}`);
    return await response.json();
}

function updateProcessingStatus(text, progress) {
    document.getElementById('processing-status').textContent = text;
    document.getElementById('progress-fill').style.width = `${progress}%`;
}

// ============================================
// Show Results
// ============================================

function showResults(processResult, previewResult) {
    showSection('preview');

    // Update preview content
    const previewContainer = document.getElementById('document-preview');
    previewContainer.innerHTML = previewResult.html || '<p>Preview not available</p>';

    // Update changes list
    const changesList = document.getElementById('changes-list');
    changesList.innerHTML = '';

    const changes = processResult.changes || [];
    changes.forEach(change => {
        const item = document.createElement('div');
        item.className = 'change-item';
        item.innerHTML = `
            <span class="change-icon">✅</span>
            <span class="change-text">${change}</span>
        `;
        changesList.appendChild(item);
    });

    // Update summary
    const stats = processResult.stats || {};
    const summaryContainer = document.getElementById('download-summary');
    summaryContainer.innerHTML = `
        <div class="summary-item">
            <div class="summary-value">${stats.estimated_pages || '-'}</div>
            <div class="summary-label">Pages</div>
        </div>
        <div class="summary-item">
            <div class="summary-value">${stats.word_count || '-'}</div>
            <div class="summary-label">Words</div>
        </div>
        <div class="summary-item">
            <div class="summary-value">${processResult.figure_count || 0}</div>
            <div class="summary-label">Figures</div>
        </div>
        <div class="summary-item">
            <div class="summary-value">${changes.length}</div>
            <div class="summary-label">Changes</div>
        </div>
    `;

    // Update comparison panels
    updateComparisonPanels(previewResult);
}

function updateComparisonPanels(previewResult) {
    const originalContent = document.getElementById('original-content');
    const formattedContent = document.getElementById('formatted-content');

    // Original - show placeholder or raw content
    originalContent.innerHTML = `
        <p style="color: #666; font-style: italic;">
            Original document content would be displayed here.
        </p>
    `;

    // Formatted
    formattedContent.innerHTML = previewResult.html || '';
}

// ============================================
// Tab Switching
// ============================================

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update panels
    document.querySelectorAll('.preview-panel').forEach(panel => {
        panel.style.display = 'none';
    });

    document.getElementById(`${tabName}-panel`).style.display = 'block';
}

// ============================================
// Download
// ============================================

async function downloadFile(format) {
    if (!currentSession.id) {
        showToast('No processed document available', 'error');
        return;
    }

    try {
        showToast(`Preparing ${format.toUpperCase()} download...`, 'info');

        const response = await fetch(`/api/download/${currentSession.id}/${format}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || `Download failed`);
        }

        // Get filename from Content-Disposition header or use default
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `formatted_paper.${format}`;
        if (contentDisposition) {
            const match = contentDisposition.match(/filename="?([^"]+)"?/);
            if (match) filename = match[1];
        }

        // Download file
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showToast(`${format.toUpperCase()} downloaded successfully!`, 'success');

    } catch (error) {
        console.error('Download error:', error);
        showToast(error.message || 'Download failed', 'error');
    }
}

// ============================================
// Settings
// ============================================

async function applySettings() {
    // Collect settings from UI
    settings = {
        font_family: document.getElementById('font-select').value,
        section_numbers: document.getElementById('section-numbers').checked,
        image_width: parseInt(document.getElementById('img-width').value),
        auto_detect: document.getElementById('auto-detect').checked,
        auto_caption: document.getElementById('auto-caption').checked,
        template: document.getElementById('template-select').value,
        line_spacing: parseFloat(document.getElementById('line-spacing').value),
        margins: {
            top: parseFloat(document.getElementById('margin-top').value),
            bottom: parseFloat(document.getElementById('margin-bottom').value),
            left: parseFloat(document.getElementById('margin-left').value),
            right: parseFloat(document.getElementById('margin-right').value)
        }
    };

    showToast('Settings applied!', 'success');

    // If we have a session, re-process with new settings
    if (currentSession.id && document.getElementById('preview-section').style.display !== 'none') {
        showToast('Re-processing with new settings...', 'info');
        await processDocument();
    }
}

// ============================================
// Reset
// ============================================

function resetProcess() {
    // Clear session
    if (currentSession.id) {
        // Cleanup server-side files (optional)
        fetch(`/api/cleanup/${currentSession.id}`, { method: 'DELETE' }).catch(() => { });
    }

    currentSession = {
        id: null,
        document: null,
        images: [],
        template: null,
        status: 'ready'
    };

    // Reset UI
    removeDocument();
    document.getElementById('images-list').innerHTML = '';

    // Show upload section
    showSection('upload');
    updateStatus('Ready', 'ready');
}

// ============================================
// Utility Functions
// ============================================

function showSection(sectionName) {
    const sections = ['upload', 'processing', 'preview'];

    sections.forEach(s => {
        const section = document.getElementById(`${s}-section`);
        if (section) {
            section.style.display = s === sectionName ? 'block' : 'none';
        }
    });
}

function updateStatus(text, type) {
    statusBadge.innerHTML = `<span class="status-dot"></span>${text}`;
    statusBadge.className = `status-badge ${type}`;
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <span class="toast-message">${message}</span>
    `;

    container.appendChild(toast);

    // Auto-remove after 4 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
