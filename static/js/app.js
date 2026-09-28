/* ─── App JavaScript ──────────────────────────────────────────────
   Page Analytics Dashboard - Client-side functionality
   ─────────────────────────────────────────────────────────────── */

// ─── Sidebar Toggle ────────────────────────────────────────────
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function(e) {
    const sidebar = document.getElementById('sidebar');
    const menuBtn = document.querySelector('.mobile-menu-btn');
    
    if (sidebar && sidebar.classList.contains('open') && 
        !sidebar.contains(e.target) && 
        menuBtn && !menuBtn.contains(e.target)) {
        sidebar.classList.remove('open');
    }
});

// ─── Page Selector ─────────────────────────────────────────────
function switchPage(pageId) {
    const url = new URL(window.location.href);
    url.searchParams.set('page_id', pageId);
    window.location.href = url.toString();
}

// ─── Date Period Selector ──────────────────────────────────────
function changePeriod(period) {
    const url = new URL(window.location.href);
    url.searchParams.set('period', period);
    window.location.href = url.toString();
}

// ─── Theme Toggle ──────────────────────────────────────────────
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    
    // Save preference via API
    fetch('/settings/theme', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `theme=${next}`,
    }).catch(() => {
        // Silently fail - theme still applied client-side
    });
    
    // Update theme toggle icon
    const btn = document.getElementById('themeToggle');
    if (btn) {
        btn.textContent = next === 'dark' ? '🌙' : '☀️';
    }
    
    // Store in localStorage as fallback
    localStorage.setItem('theme', next);
}

// ─── Table Sorting ─────────────────────────────────────────────
let sortDirections = {};

function sortTable(columnIndex) {
    const table = document.querySelector('.data-table');
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Toggle direction
    const dir = sortDirections[columnIndex] === 'asc' ? 'desc' : 'asc';
    sortDirections[columnIndex] = dir;
    
    rows.sort((a, b) => {
        let aVal = a.cells[columnIndex]?.textContent.trim() || '';
        let bVal = b.cells[columnIndex]?.textContent.trim() || '';
        
        // Try numeric comparison (strip commas, %, etc.)
        const aNum = parseFloat(aVal.replace(/[,%+▲▼]/g, ''));
        const bNum = parseFloat(bVal.replace(/[,%+▲▼]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return dir === 'asc' ? aNum - bNum : bNum - aNum;
        }
        
        // String comparison
        return dir === 'asc' 
            ? aVal.localeCompare(bVal)
            : bVal.localeCompare(aVal);
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

// ─── Number Formatting ─────────────────────────────────────────
function formatNumber(n) {
    if (n === null || n === undefined) return '—';
    return n.toLocaleString();
}

// ─── Smooth Scroll for Anchor Links ────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// ─── Auto-refresh Countdown ────────────────────────────────────
function startAutoRefresh(minutes) {
    if (minutes <= 0) return;
    
    const ms = minutes * 60 * 1000;
    setTimeout(() => {
        window.location.reload();
    }, ms);
}

// ─── Initialize Theme on Load ──────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
    // Set theme toggle icon
    const theme = document.documentElement.getAttribute('data-theme');
    const btn = document.getElementById('themeToggle');
    if (btn) {
        btn.textContent = theme === 'dark' ? '🌙' : '☀️';
    }
    
    // Animate KPI values (count up effect)
    document.querySelectorAll('.kpi-value').forEach(el => {
        const text = el.textContent.trim();
        const num = parseInt(text.replace(/[^0-9]/g, ''));
        
        if (!isNaN(num) && num > 100) {
            const duration = 800;
            const startTime = performance.now();
            const startVal = 0;
            
            function animate(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                // Ease out cubic
                const eased = 1 - Math.pow(1 - progress, 3);
                const current = Math.round(startVal + (num - startVal) * eased);
                
                // Preserve formatting (keep % and /100 etc.)
                el.textContent = text.replace(
                    num.toLocaleString() || num.toString(),
                    current.toLocaleString()
                );
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    el.textContent = text; // Reset to original
                }
            }
            
            requestAnimationFrame(animate);
        }
    });
});
