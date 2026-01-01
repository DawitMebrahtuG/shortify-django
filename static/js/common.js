// Get CSRF token from meta tag or cookie
function getCSRFToken() {
    // First try meta tag
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        return metaTag.content;
    }
    
    // Fallback to cookie
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === 'csrftoken=') {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

// Copy URL with visual feedback
function copyUrl(button, url) {
    navigator.clipboard.writeText(url).then(() => {
        const originalText = button.innerHTML;
        const originalBg = button.style.background;
        
        button.innerHTML = '✓ Copied';
        button.classList.add('copied');
        button.style.background = 'var(--success)';
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.classList.remove('copied');
            button.style.background = originalBg;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Make API request with CSRF
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        credentials: 'same-origin'
    };
    
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    return fetch(url, mergedOptions);
}