document.addEventListener('DOMContentLoaded', function() {
    initCustomSelect();
    initQRForm();
});

function initCustomSelect() {
    const customSelect = document.getElementById('linkSelect');
    if (!customSelect) return;
    
    const trigger = customSelect.querySelector('.custom-select-trigger');
    const options = customSelect.querySelectorAll('.custom-select-option[data-value]');
    const hiddenInput = document.getElementById('qr_url');
    const placeholder = trigger.querySelector('.custom-select-placeholder');
    
    // Toggle dropdown on trigger click
    trigger.addEventListener('click', () => {
        customSelect.classList.toggle('open');
    });
    
    // Handle option selection
    options.forEach(option => {
        option.addEventListener('click', () => {
            // Remove selected from all
            options.forEach(opt => opt.classList.remove('selected'));
            // Add selected to clicked
            option.classList.add('selected');
            // Update trigger text
            const code = option.querySelector('.option-code').textContent;
            placeholder.textContent = code;
            placeholder.classList.remove('custom-select-placeholder');
            // Set hidden input value
            hiddenInput.value = option.dataset.value;
            // Close dropdown
            customSelect.classList.remove('open');
        });
    });
    
    // Close on click outside
    document.addEventListener('click', (e) => {
        if (!customSelect.contains(e.target)) {
            customSelect.classList.remove('open');
        }
    });
}

function initQRForm() {
    const form = document.getElementById('createQrForm');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const shortCode = document.getElementById('qr_url').value;
        const name = document.getElementById('qr_name').value;
        const errorDiv = document.getElementById('createError');
        
        if (!shortCode) {
            errorDiv.textContent = 'Please select a link';
            return;
        }
        
        errorDiv.textContent = '';
        
        try {
            const response = await apiRequest('/api/qrcode/create/', {
                method: 'POST',
                body: JSON.stringify({
                    url_short_code: shortCode,
                    name: name || ''
                })
            });
            
            if (response.ok) {
                window.location.reload();
            } else {
                const data = await response.json();
                errorDiv.textContent = data.detail || 'Error creating QR code';
            }
        } catch (err) {
            window.location.reload();
        }
    });
}