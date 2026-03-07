// Search module — handles geocoding and address autocomplete

let debounceTimer = null;

/**
 * Initialize the search bar with geocoding
 */
export function initSearch(onLocationSelected) {
    const input = document.getElementById('search-input');
    const suggestions = document.getElementById('search-suggestions');

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        const query = input.value.trim();
        if (query.length < 3) {
            hideSuggestions();
            return;
        }
        debounceTimer = setTimeout(() => geocode(query), 350);
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideSuggestions();
            input.blur();
        }
        if (e.key === 'Enter') {
            const first = suggestions.querySelector('.suggestion-item');
            if (first) first.click();
        }
    });

    // Close suggestions on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('#search-bar')) {
            hideSuggestions();
        }
    });

    /**
     * Geocode an address using Nominatim (OpenStreetMap)
     */
    async function geocode(query) {
        try {
            const url = `https://nominatim.openstreetmap.org/search?` +
                `q=${encodeURIComponent(query + ' Toronto Canada')}&` +
                `format=json&addressdetails=1&limit=6&countrycodes=ca`;

            const res = await fetch(url, {
                headers: { 'Accept-Language': 'en' },
            });
            const results = await res.json();

            if (results.length === 0) {
                showNoResults();
                return;
            }

            showSuggestions(results, onLocationSelected);
        } catch (err) {
            console.error('Geocoding error:', err);
        }
    }

    function showSuggestions(results, callback) {
        suggestions.innerHTML = '';

        results.forEach((result) => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            item.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
          <circle cx="12" cy="10" r="3"/>
        </svg>
        <div class="suggestion-text">
          <div class="suggestion-main">${formatAddress(result)}</div>
          <div class="suggestion-sub">${result.display_name}</div>
        </div>
      `;
            item.addEventListener('click', () => {
                input.value = formatAddress(result);
                hideSuggestions();
                callback({
                    lng: parseFloat(result.lon),
                    lat: parseFloat(result.lat),
                    address: result.display_name,
                    shortAddress: formatAddress(result),
                });
            });
            suggestions.appendChild(item);
        });

        suggestions.classList.add('visible');
    }

    function showNoResults() {
        suggestions.innerHTML = `
      <div class="suggestion-item" style="pointer-events:none; opacity:0.5;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <div class="suggestion-text">
          <div class="suggestion-main">No results found</div>
          <div class="suggestion-sub">Try a different address or location</div>
        </div>
      </div>
    `;
        suggestions.classList.add('visible');
    }
}

function hideSuggestions() {
    const suggestions = document.getElementById('search-suggestions');
    suggestions.classList.remove('visible');
}

function formatAddress(result) {
    const addr = result.address || {};
    const parts = [];
    if (addr.house_number) parts.push(addr.house_number);
    if (addr.road) parts.push(addr.road);
    if (parts.length === 0) return result.display_name.split(',')[0];
    const city = addr.city || addr.town || addr.village || '';
    const province = addr.state || '';
    const postal = addr.postcode || '';
    let formatted = parts.join(' ');
    if (city) formatted += `, ${city}`;
    if (province) formatted += `, ${province}`;
    if (postal) formatted += ` ${postal}`;
    return formatted;
}
