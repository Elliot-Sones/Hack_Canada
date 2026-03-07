// Arterial Frontend — Main Entry Point

import { initMap, flyTo, setMarker } from './modules/map.js';
import { initSearch } from './modules/search.js';
import { initPolicyPanel, showAddressInfo } from './modules/policy-panel.js';
import { initChatPanel } from './modules/chat-panel.js';

// ── Bootstrap ──────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Map
    initMap();

    // 2. Initialize Search with location callback
    initSearch((location) => {
        flyTo(location.lng, location.lat, 16);
        setMarker(location.lng, location.lat);
        showAddressInfo(location);
    });

    // 3. Initialize Policy Panel
    initPolicyPanel();

    // 4. Initialize Chat Panel
    initChatPanel();

    // 5. Initialize Sidebar
    initSidebar();
});

// ── Sidebar Navigation ─────────────────────────────

function initSidebar() {
    const navItems = document.querySelectorAll('.nav-item[data-panel]');
    const collapseBtn = document.getElementById('collapse-btn');

    navItems.forEach((item) => {
        item.addEventListener('click', () => {
            navItems.forEach((n) => n.classList.remove('active'));
            item.classList.add('active');
        });
    });

    collapseBtn.addEventListener('click', () => {
        document.body.classList.toggle('sidebar-collapsed');

        // Update icon direction
        const svg = collapseBtn.querySelector('svg');
        if (document.body.classList.contains('sidebar-collapsed')) {
            svg.innerHTML = '<polyline points="9 18 15 12 9 6"/>';
            collapseBtn.querySelector('span').textContent = 'Expand';
        } else {
            svg.innerHTML = '<polyline points="15 18 9 12 15 6"/>';
            collapseBtn.querySelector('span').textContent = 'Collapse';
        }
    });
}
