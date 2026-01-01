document.addEventListener('DOMContentLoaded', function() {
    // Setup modal close on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.classList.remove('active');
            }
        });
    });
    
    // Setup add link form
    const addLinkForm = document.getElementById('addLinkForm');
    if (addLinkForm) {
        addLinkForm.addEventListener('submit', handleAddLink);
    }
});

function openAddModal() {
    document.getElementById('addModal').classList.add('active');
}

function closeAddModal() {
    document.getElementById('addModal').classList.remove('active');
}

function closeDetailModal() {
    document.getElementById('detailModal').classList.remove('active');
}

// Fetch and show detailed analytics
async function showDetail(shortCode) {
    const modal = document.getElementById('detailModal');
    const content = document.getElementById('detailContent');
    
    // Show modal with loading state
    content.innerHTML = `
        <div class="detail-loading">
            <div class="spinner"></div>
            <p>Loading analytics...</p>
        </div>
    `;
    modal.classList.add('active');
    
    try {
        const response = await apiRequest(`/api/urls/${shortCode}/analytics/`);
        
        if (!response.ok) throw new Error('Failed to load');
        
        const data = await response.json();
        
        content.innerHTML = `
            <div class="detail-grid">
                <div class="detail-item" style="grid-column: span 2;">
                    <div class="label">Short URL</div>
                    <div class="value" style="color: var(--primary-light); display: flex; align-items: center; gap: 12px;">
                        <span>${window.location.origin}/${shortCode}/</span>
                        <button class="btn btn-sm copy-btn" style="width: auto; padding: 6px 12px; flex-shrink: 0;"
                                onclick="copyUrl(this, '${window.location.origin}/${shortCode}/')">📋 Copy</button>
                    </div>
                </div>
            </div>
            
            <!-- Stats Overview -->
            <div class="stats-row" style="margin-top: 20px;">
                <div class="stat-box">
                    <div class="number">${data.total_clicks}</div>
                    <div class="label">Total Clicks</div>
                </div>
                <div class="stat-box">
                    <div class="number">${data.unique_ips}</div>
                    <div class="label">Unique Visitors</div>
                </div>
                <div class="stat-box">
                    <div class="number">${Object.keys(data.browsers || {}).length}</div>
                    <div class="label">Browsers</div>
                </div>
                <div class="stat-box">
                    <div class="number">${Object.keys(data.devices || {}).length}</div>
                    <div class="label">Devices</div>
                </div>
            </div>
            
            <!-- Breakdowns -->
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
                <!-- Browsers -->
                <div>
                    <h4 style="font-size: 12px; color: var(--text-secondary); margin-bottom: 12px;">🌐 BROWSERS</h4>
                    <div class="breakdown-list">
                        ${Object.entries(data.browsers || {}).slice(0, 5).map(([name, count]) => `
                            <div class="breakdown-item">
                                <span>${name || 'Unknown'}</span>
                                <span class="count">${count}</span>
                            </div>
                        `).join('') || '<div style="color: var(--text-secondary); font-size: 13px;">No data</div>'}
                    </div>
                </div>
                
                <!-- Devices -->
                <div>
                    <h4 style="font-size: 12px; color: var(--text-secondary); margin-bottom: 12px;">📱 DEVICES</h4>
                    <div class="breakdown-list">
                        ${Object.entries(data.devices || {}).slice(0, 5).map(([name, count]) => `
                            <div class="breakdown-item">
                                <span>${name || 'Unknown'}</span>
                                <span class="count">${count}</span>
                            </div>
                        `).join('') || '<div style="color: var(--text-secondary); font-size: 13px;">No data</div>'}
                    </div>
                </div>
                
                <!-- OS -->
                <div>
                    <h4 style="font-size: 12px; color: var(--text-secondary); margin-bottom: 12px;">💻 OPERATING SYSTEMS</h4>
                    <div class="breakdown-list">
                        ${Object.entries(data.operating_systems || {}).slice(0, 5).map(([name, count]) => `
                            <div class="breakdown-item">
                                <span>${name || 'Unknown'}</span>
                                <span class="count">${count}</span>
                            </div>
                        `).join('') || '<div style="color: var(--text-secondary); font-size: 13px;">No data</div>'}
                    </div>
                </div>
            </div>
            
            <!-- Top Referrers -->
            <div class="detail-section">
                <h4>🔗 TOP REFERRERS</h4>
                <div class="breakdown-list">
                    ${(data.top_referrers || []).slice(0, 5).map(ref => `
                        <div class="breakdown-item">
                            <span style="max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" 
                                  title="${ref.referrer}">${ref.referrer}</span>
                            <span class="count">${ref.count}</span>
                        </div>
                    `).join('') || '<div style="color: var(--text-secondary); font-size: 13px;">No referrer data yet</div>'}
                </div>
            </div>
            
            <!-- Recent Clicks -->
            <div class="detail-section">
                <h4>⚡ RECENT CLICKS</h4>
                <div class="breakdown-list">
                    ${(data.recent_clicks || []).slice(0, 5).map(click => `
                        <div class="breakdown-item">
                            <span>${click.browser || 'Unknown'} • ${click.device || 'Unknown'}</span>
                            <span style="color: var(--text-secondary); font-size: 11px;">${new Date(click.timestamp).toLocaleString()}</span>
                        </div>
                    `).join('') || '<div style="color: var(--text-secondary); font-size: 13px;">No clicks yet</div>'}
                </div>
            </div>
            
            <!-- Actions -->
            <div style="margin-top: 24px; display: flex; gap: 8px;">
                <a href="/api/urls/${shortCode}/qrcode/" target="_blank" class="btn btn-secondary btn-sm">📱 Download QR</a>
            </div>
        `;
    } catch (err) {
        content.innerHTML = `
            <div style="text-align: center; padding: 40px; color: var(--danger);">
                <p>Failed to load analytics. Please try again.</p>
            </div>
        `;
    }
}

// Handle add link form submission
async function handleAddLink(e) {
    e.preventDefault();
    
    const url = document.getElementById('add_url').value;
    const expires = document.getElementById('add_expires').value;
    const errorDiv = document.getElementById('addError');
    
    try {
        const response = await apiRequest('/api/shorten/', {
            method: 'POST',
            body: JSON.stringify({
                original_url: url,
                expires_at: expires || null
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.location.reload();
        } else {
            errorDiv.textContent = data.errors?.original_url?.[0] || 'Error creating link';
        }
    } catch (err) {
        errorDiv.textContent = 'Network error';
    }
}