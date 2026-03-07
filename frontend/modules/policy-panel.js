// Policy Panel — displays project/parcel information and policy data

// Mock Toronto policy data
const MOCK_POLICIES = [
    { name: 'Toronto Official Plan (Land Use Designations)', extracts: 23, icon: 'doc' },
    { name: 'Toronto Zoning Volume 2', extracts: 5, icon: 'doc' },
    { name: 'Mid-Rise Design Guidelines', extracts: 0, icon: 'doc' },
    { name: 'Official Plan Chapter 2', extracts: 0, icon: 'doc' },
    { name: 'Official Plan Chapter 3', extracts: 0, icon: 'doc' },
    { name: 'Toronto Zoning Volume 3', extracts: 0, icon: 'doc' },
];

const MOCK_DATASETS = [
    {
        name: 'Official Plan Land Use Designations',
        description: 'General boundaries supporting the 2023 OP Consolidation; available in localized schedules',
        source: 'City of Toronto',
        values: 1,
    },
    {
        name: 'UrbanToronto',
        description: 'Founded in 2022 as an open database of applications, conversation, and building details across Toronto.',
        source: 'City of Vaughan',
        values: 14,
    },
    {
        name: 'Toronto Application Information Centre',
        description: 'The Application Information Centre (AIC) provides information on all active Community Planning applications.',
        source: 'City of Toronto',
        values: 40,
    },
    {
        name: 'Inclusionary Zoning Overlay',
        description: 'Boundaries surrounding the 2021 Inclusionary Zoning Mandate market areas.',
        source: 'City of Toronto',
        values: 1,
    },
];

// Mock project info for different zoning types
const MOCK_INFO = {
    R: { units: '2 dwelling units', typology: 'Detached', height: '10 m', fsi: '0.6', uses: ['Dwelling Unit', 'Home Occupation'] },
    RD: { units: '2 dwelling units', typology: 'Semi-Detached', height: '10 m', fsi: '0.6', uses: ['Dwelling Unit', 'Home Occupation'] },
    RS: { units: '4 dwelling units', typology: 'Fourplex', height: '10 m', fsi: '1.0', uses: ['Dwelling Unit', 'Home Occupation'] },
    RT: { units: '6 dwelling units', typology: 'Townhouse', height: '12 m', fsi: '1.5', uses: ['Dwelling Unit', 'Home Occupation', 'Live-Work'] },
    RM: { units: '60 dwelling units', typology: 'Mid-Rise', height: '20 m', fsi: '2.5', uses: ['Dwelling Unit', 'Home Occupation', 'Retail'] },
    RA: { units: '120 dwelling units', typology: 'Apartment', height: '36 m', fsi: '3.5', uses: ['Dwelling Unit', 'Retail', 'Office'] },
    CR: { units: '80 dwelling units', typology: 'Mixed-Use', height: '30 m', fsi: '3.0', uses: ['Dwelling Unit', 'Retail', 'Office', 'Restaurant'] },
    CRE: { units: '100 dwelling units', typology: 'Mixed-Use', height: '45 m', fsi: '4.0', uses: ['Dwelling Unit', 'Retail', 'Office'] },
    I: { units: 'N/A', typology: 'Industrial', height: '15 m', fsi: '1.0', uses: ['Manufacturing', 'Warehouse', 'Office'] },
};

/**
 * Initialize the policy panel
 */
export function initPolicyPanel() {
    const panel = document.getElementById('policy-panel');
    const closeBtn = document.getElementById('policy-panel-close');

    closeBtn.addEventListener('click', () => {
        hidePanel();
    });

    // Listen for parcel selection events
    window.addEventListener('parcel-selected', (e) => {
        showParcelInfo(e.detail);
    });
}

/**
 * Show the policy panel with data for a specific parcel
 */
export function showParcelInfo(parcel) {
    const panel = document.getElementById('policy-panel');
    const addressEl = document.getElementById('policy-address-text');
    const infoSection = document.getElementById('project-info-section');
    const policiesSection = document.getElementById('policies-list-section');
    const datasetsSection = document.getElementById('datasets-list-section');

    // Set address
    addressEl.textContent = parcel.address || 'Unknown Address';

    // Set project info based on zoning
    const info = MOCK_INFO[parcel.zoning] || MOCK_INFO['R'];
    document.getElementById('info-units').textContent = info.units;
    document.getElementById('info-typology').textContent = info.typology;
    document.getElementById('info-zoning').textContent = `${parcel.zoning} (Bylaw 569-2013)`;
    document.getElementById('info-height').textContent = info.height;
    document.getElementById('info-fsi').textContent = info.fsi;

    // Fill use tags
    const usesEl = document.getElementById('info-uses');
    usesEl.innerHTML = '';
    info.uses.forEach((u) => {
        const tag = document.createElement('span');
        tag.className = 'tag';
        tag.textContent = u;
        usesEl.appendChild(tag);
    });

    // Fill policies list
    const policiesList = document.getElementById('policies-list');
    policiesList.innerHTML = '';
    MOCK_POLICIES.forEach((p) => {
        const item = document.createElement('div');
        item.className = 'policy-item';
        item.innerHTML = `
      <div class="item-left">
        <svg class="item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        <div>
          <div class="item-name">${p.name}</div>
        </div>
      </div>
      <div class="item-meta">${p.extracts} Extracts</div>
    `;
        policiesList.appendChild(item);
    });

    // Fill datasets list
    const datasetsList = document.getElementById('datasets-list');
    datasetsList.innerHTML = '';
    MOCK_DATASETS.forEach((d) => {
        const item = document.createElement('div');
        item.className = 'dataset-item';
        item.innerHTML = `
      <div class="item-left">
        <svg class="item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <ellipse cx="12" cy="5" rx="9" ry="3"/>
          <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
        </svg>
        <div>
          <div class="item-name">${d.name}</div>
          <div class="item-description">${d.description}</div>
        </div>
      </div>
      <div class="item-meta">${d.values} Values</div>
    `;
        datasetsList.appendChild(item);
    });

    // Show all sections
    infoSection.classList.remove('hidden');
    policiesSection.classList.remove('hidden');
    datasetsSection.classList.remove('hidden');

    // Open panel
    showPanel();
}

/**
 * Show panel for a searched address (without parcel data)
 */
export function showAddressInfo(location) {
    const defaultZoning = ['R', 'RD', 'RS', 'RT', 'RM', 'RA', 'CR'][Math.floor(Math.random() * 7)];
    showParcelInfo({
        address: location.shortAddress || location.address,
        zoning: defaultZoning,
        lotArea: 300 + Math.floor(Math.random() * 500),
    });
}

function showPanel() {
    const panel = document.getElementById('policy-panel');
    panel.classList.remove('panel-hidden');
    document.body.classList.add('panel-open');
}

export function hidePanel() {
    const panel = document.getElementById('policy-panel');
    panel.classList.add('panel-hidden');
    document.body.classList.remove('panel-open');
}
