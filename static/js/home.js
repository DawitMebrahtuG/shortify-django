document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('shortenForm');
    if (!form) return;
    
    form.addEventListener('submit', handleShortenSubmit);
});

async function handleShortenSubmit(e) {
    e.preventDefault();
    
    const originalUrl = document.getElementById('original_url').value;
    const expiresAt = document.getElementById('expires_at').value;
    const errorDiv = document.getElementById('error');
    const resultDiv = document.getElementById('result');
    
    errorDiv.textContent = '';
    resultDiv.classList.remove('show');
    
    try {
        const response = await apiRequest('/api/shorten/', {
            method: 'POST',
            body: JSON.stringify({
                original_url: originalUrl,
                expires_at: expiresAt || null
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('shortUrlInput').value = data.short_url;
            resultDiv.classList.add('show');
        } else {
            errorDiv.textContent = data.errors?.original_url ? 
                data.errors.original_url[0] : 
                'Error creating short URL';
        }
    } catch (error) {
        errorDiv.textContent = 'Network error. Please try again.';
    }
}

function copyToClipboard() {
    const input = document.getElementById('shortUrlInput');
    input.select();
    
    navigator.clipboard.writeText(input.value).then(() => {
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✓ Copied!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    });
}