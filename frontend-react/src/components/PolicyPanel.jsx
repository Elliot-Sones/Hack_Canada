import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { getParcelOverlays, getParcelZoningAnalysis, getPolicyStack, getNearbyApplications, getParcelFinancialSummary, uploadDocument, getUpload, getPlanDocuments, regeneratePlanDocument } from '../api.js';
import { isResolvedParcel, isUnresolvedParcel } from '../lib/parcelState.js';
import useResizable from '../hooks/useResizable.js';

// ─── Pipeline engineering decision panel ──────────────────────────────────────

const MATERIAL_LABELS = {
    CI: 'Cast Iron', CICL: 'Cast Iron Lined', DIP: 'Ductile Iron', DICL: 'Ductile Iron Lined',
    PVC: 'PVC (Polyvinyl Chloride)', CPP: 'Corrugated Plastic', AC: 'Asbestos Cement',
    COP: 'Copper', UNK: 'Unknown',
};
const MATERIAL_COLORS = {
    CI: '#e67e22', CICL: '#e67e22', DIP: '#2277bb', DICL: '#2277bb',
    PVC: '#27ae60', CPP: '#27ae60', AC: '#e74c3c', COP: '#f1c40f', UNK: '#888',
};

// ── Engineering computations ──────────────────────────────────────────────────

/** Hazen-Williams C-factor adjusted for material age */
function hwCFactor(mat, age) {
    const a = age || 0;
    switch (mat) {
        case 'CI':   return Math.max(40,  130 - a * 0.55);
        case 'CICL': return Math.max(80,  130 - a * 0.35);
        case 'DIP':  return Math.max(100, 140 - a * 0.20);
        case 'DICL': return Math.max(110, 140 - a * 0.15);
        case 'PVC':  return 150;
        case 'CPP':  return 140;
        case 'AC':   return Math.max(80,  140 - a * 0.30);
        case 'COP':  return 130;
        default:     return 100;
    }
}

/** Hazen-Williams: flow rate (L/s) for a full pipe at given slope S (m/m) */
function hwFlow(diamMm, C, S = 0.002) {
    const D = diamMm / 1000;
    const R = D / 4;
    const V = 0.8492 * C * Math.pow(R, 0.63) * Math.pow(S, 0.54);
    const A = Math.PI * Math.pow(D / 2, 2);
    return V * A * 1000; // L/s
}

/** Pressure drop kPa per 100 m */
function hwPressureDrop(diamMm, C, flowLs) {
    const D = diamMm / 1000;
    const A = Math.PI * Math.pow(D / 2, 2);
    const V = (flowLs / 1000) / A;
    const R = D / 4;
    const S = Math.pow(V / (0.8492 * C * Math.pow(R, 0.63)), 1 / 0.54);
    return S * 9.81 * 1000 * 100; // kPa/100m
}

/** Break probability breaks/km/year */
function breakProb(mat, age) {
    const a = age || 0;
    if (mat === 'AC')                   return 0.8;
    if (mat === 'CI' || mat === 'CICL') {
        if (a > 100) return 1.8;
        if (a > 75)  return 0.9;
        if (a > 50)  return 0.45;
        return 0.18;
    }
    if (mat === 'DIP' || mat === 'DICL') {
        if (a > 60)  return 0.22;
        if (a > 30)  return 0.10;
        return 0.05;
    }
    if (mat === 'PVC' || mat === 'CPP') {
        if (a > 40)  return 0.08;
        return 0.02;
    }
    return 0.3;
}

/** Expected remaining service life (years) */
function remainingLife(mat, age) {
    const a = age || 0;
    const typicalLife = { CI: 100, CICL: 110, DIP: 100, DICL: 120, PVC: 80, CPP: 70, AC: 50, COP: 80, UNK: 70 };
    const life = typicalLife[mat] || 70;
    return Math.max(0, life - a);
}

/** Replacement cost estimate (CAD) */
function replacementCost(diamMm, lengthM) {
    if (!lengthM) return null;
    const d = diamMm || 150;
    // Open-cut cost $/m: scales roughly with diameter
    const costPerM = d <= 150 ? 1200 : d <= 300 ? 1800 : d <= 600 ? 2600 : 3500;
    return costPerM * lengthM;
}

/** Condition severity */
function pipeCondition(mat, installYear) {
    const age = installYear ? (2026 - installYear) : null;
    if (mat === 'AC') return { label: 'Critical — Hazardous Material', color: '#e74c3c', risk: 'critical' };
    if (!age) return { label: 'Unknown', color: '#888', risk: 'unknown' };
    const bp = breakProb(mat, age);
    if (bp >= 1.0)  return { label: 'Critical — End of Service Life', color: '#e74c3c', risk: 'critical' };
    if (bp >= 0.45) return { label: 'High Risk', color: '#e67e22', risk: 'high' };
    if (bp >= 0.15) return { label: 'Moderate Risk', color: '#f1c40f', risk: 'moderate' };
    return { label: 'Good Condition', color: '#27ae60', risk: 'good' };
}

// ── Sub-components ────────────────────────────────────────────────────────────

function Section({ title, icon, children, defaultOpen = true, accent }) {
    const [open, setOpen] = React.useState(defaultOpen);
    return (
        <div style={{ marginBottom: 12, border: '1px solid #2a2a2a', borderRadius: 8, overflow: 'hidden' }}>
            <button
                onClick={() => setOpen(o => !o)}
                style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                    padding: '9px 14px', background: '#1e1e1e', border: 'none', cursor: 'pointer',
                    color: '#f0ece4', fontSize: 12, fontWeight: 600, textAlign: 'left',
                    borderBottom: open ? '1px solid #2a2a2a' : 'none',
                }}
            >
                <span style={{ fontSize: 14 }}>{icon}</span>
                <span style={{ flex: 1, letterSpacing: 0.3 }}>{title}</span>
                {accent && <span style={{ fontSize: 11, color: accent.color, fontWeight: 700 }}>{accent.text}</span>}
                <span style={{ color: '#555', fontSize: 10 }}>{open ? '▲' : '▼'}</span>
            </button>
            {open && <div style={{ background: '#161616', padding: '12px 14px' }}>{children}</div>}
        </div>
    );
}

function Row({ label, value, highlight, mono }) {
    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '5px 0', borderBottom: '1px solid #222' }}>
            <span style={{ color: '#888', fontSize: 12 }}>{label}</span>
            <span style={{ color: highlight || '#f0ece4', fontSize: 12, fontFamily: mono ? 'monospace' : undefined, textAlign: 'right', maxWidth: '60%' }}>{value}</span>
        </div>
    );
}

function Bar({ value, max, color }) {
    const pct = Math.min(100, Math.round((value / max) * 100));
    return (
        <div style={{ background: '#2a2a2a', borderRadius: 4, height: 6, width: '100%', overflow: 'hidden' }}>
            <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 4, transition: 'width 0.4s' }} />
        </div>
    );
}

function Pill({ text, color }) {
    return (
        <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 5, padding: '2px 8px',
            background: `${color}22`, border: `1px solid ${color}55`, borderRadius: 4,
            fontSize: 11, color, fontWeight: 600,
        }}>{text}</span>
    );
}

function Checklist({ items }) {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {items.map(({ done, text, sub, urgent }) => (
                <div key={text} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    <span style={{ fontSize: 13, marginTop: 1, color: urgent ? '#e74c3c' : done ? '#27ae60' : '#888', flexShrink: 0 }}>
                        {urgent ? '⚠' : done ? '✓' : '○'}
                    </span>
                    <div>
                        <div style={{ fontSize: 12, color: urgent ? '#e74c3c' : done ? '#ccc' : '#f0ece4' }}>{text}</div>
                        {sub && <div style={{ fontSize: 11, color: '#666', marginTop: 2 }}>{sub}</div>}
                    </div>
                </div>
            ))}
        </div>
    );
}

function PipelineAssetPanel({ asset }) {
    const mat  = asset.material || 'UNK';
    const color = MATERIAL_COLORS[mat] || '#888';
    const matLabel = MATERIAL_LABELS[mat] || mat;
    const age  = asset.install_year ? (2026 - asset.install_year) : null;
    const diam = asset.diameter_mm || 150;
    const cond = pipeCondition(mat, asset.install_year);

    // Hydraulic
    const C      = hwCFactor(mat, age);
    const C_new  = hwCFactor(mat, 0);
    const flowNow = hwFlow(diam, C);
    const flowNew = hwFlow(diam, C_new);
    const flowPct = Math.round((flowNow / flowNew) * 100);
    const dpNow  = hwPressureDrop(diam, C, flowNow * 0.6);

    // Risk
    const bp   = breakProb(mat, age);
    const rl   = remainingLife(mat, age);
    const cost = replacementCost(diam, asset.length_m);

    // Material replacement recommendation
    const replaceMat = mat === 'AC' ? 'HDPE (mandatory — asbestos protocol applies)' :
        (mat === 'CI' || mat === 'CICL') ? 'HDPE (trenchless CIPP lining) or DIP (open-cut)' :
        mat === 'PVC' ? 'HDPE or DICL for higher pressure classes' :
        'DIP or HDPE';

    const permitItems = [
        { done: false, text: 'Toronto Water — Watermain Construction Approval', sub: 'Submit CCTV, hydraulic model, and design drawings' },
        { done: false, text: 'ROW Permit — Transportation Services', sub: 'Required for any excavation in road allowance; notify TTC/Metrolinx' },
        { done: false, text: 'Ontario Reg. 170/03 — Drinking Water System Permit to Take Water', sub: 'If service area or demand changes' },
        ...(mat === 'AC' ? [{ done: false, urgent: true, text: 'Ontario Reg. 278/05 — Designated Substance (Asbestos)', sub: 'Asbestos abatement plan required before any disturbance' }] : []),
        { done: false, text: 'Building Permit — City of Toronto', sub: 'For appurtenances, chambers, or connections' },
        { done: false, text: 'TRCA Permit — if within 30 m of watercourse or regulated area', sub: 'Check Toronto Greenspace Map before design' },
        { done: false, text: 'Class Environmental Assessment', sub: 'Required if capital cost > $2M or if new trunk main (Municipal Class EA)' },
    ];

    const geoItems = [
        { done: true,  text: `Min burial depth: 1.8 m to top of pipe (Toronto frost line)`, sub: 'OPSD 802.010 — deeper in areas with heavy traffic loading' },
        { done: false, text: 'Bedding Class B required (granular material, compacted to 95% proctor)', sub: 'OPSD 802.030 — haunching to spring line minimum' },
        { done: false, text: 'Ground Penetrating Radar (GPR) survey before excavation', sub: 'Identify fibre, power, gas and sewer conflicts within 3 m corridor' },
        { done: false, text: 'Geotechnical borehole — 1 per 100 m for urban route', sub: 'Assess bearing capacity, groundwater depth, and corrosivity index' },
        { done: false, text: 'Trench stability analysis if depth > 1.2 m', sub: 'Ontario Reg. 213/91 (Construction Projects) — shoring required' },
        ...(mat === 'CI' || mat === 'AC' ? [{ done: false, urgent: true, text: 'Soil corrosivity assessment', sub: 'Resistivity < 2,000 Ω·cm = highly corrosive — cathodic protection required for metal pipe' }] : []),
    ];

    return (
        <div style={{ padding: '14px 16px', fontFamily: 'Inter, sans-serif', fontSize: 13, color: '#f0ece4', overflowY: 'auto' }}>

            {/* Header */}
            <div style={{ marginBottom: 14, paddingBottom: 12, borderBottom: '1px solid #2a2a2a' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{ width: 10, height: 10, borderRadius: '50%', background: color, display: 'inline-block', flexShrink: 0 }} />
                    <span style={{ fontSize: 11, color: '#888', textTransform: 'uppercase', letterSpacing: 1 }}>Water Main · {mat}</span>
                </div>
                <div style={{ fontSize: 16, fontWeight: 700 }}>{asset.location || 'Unnamed Segment'}</div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
                    {diam && <Pill text={`⌀ ${diam} mm`} color="#2277bb" />}
                    {asset.install_year && <Pill text={`${asset.install_year} · ${age} yrs`} color={cond.color} />}
                    <Pill text={cond.label} color={cond.color} />
                </div>
            </div>

            {/* 1. Asset Identity */}
            <Section title="Asset Identity" icon="🆔" defaultOpen={false}>
                <Row label="Asset ID"    value={asset.asset_id || '—'} mono />
                <Row label="Type"        value="Water Main — Transmission/Distribution" />
                <Row label="Material"    value={`${matLabel} (${mat})`} highlight={color} />
                <Row label="Diameter"    value={diam ? `${diam} mm (${(diam/25.4).toFixed(1)}")` : '—'} />
                <Row label="Length"      value={asset.length_m ? `${asset.length_m} m` : '—'} />
                <Row label="Installed"   value={asset.install_year ? `${asset.install_year} (${age} years in service)` : '—'} />
                <Row label="Location"    value={asset.location || '—'} />
                <Row label="Remaining Life" value={rl > 0 ? `~${rl} years` : 'Past design life'} highlight={rl > 20 ? '#27ae60' : rl > 5 ? '#f1c40f' : '#e74c3c'} />
            </Section>

            {/* 2. Hydraulic Performance */}
            <Section title="Hydraulic Performance" icon="💧" accent={{ text: `C=${Math.round(C)}`, color: flowPct > 75 ? '#27ae60' : flowPct > 50 ? '#f1c40f' : '#e74c3c' }}>
                <div style={{ marginBottom: 10 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span style={{ fontSize: 12, color: '#888' }}>Hazen-Williams C-factor (current vs new)</span>
                        <span style={{ fontSize: 12, color: flowPct > 75 ? '#27ae60' : '#f1c40f' }}>{Math.round(C)} / {Math.round(C_new)}</span>
                    </div>
                    <Bar value={C} max={C_new} color={flowPct > 75 ? '#27ae60' : flowPct > 50 ? '#f1c40f' : '#e74c3c'} />
                    <div style={{ fontSize: 11, color: '#666', marginTop: 3 }}>Tuberculation and scaling reduce carrying capacity over time</div>
                </div>
                <Row label="Est. flow capacity"    value={`${flowNow.toFixed(1)} L/s (${flowPct}% of design)`} highlight={flowPct > 75 ? '#27ae60' : '#f1c40f'} />
                <Row label="Design flow (new pipe)" value={`${flowNew.toFixed(1)} L/s`} />
                <Row label="Pressure drop"          value={`~${dpNow.toFixed(0)} kPa / 100 m at 60% flow`} />
                <Row label="Velocity at design flow" value={`${(flowNow / 1000 / (Math.PI * Math.pow(diam/2000, 2))).toFixed(2)} m/s`} />
                <div style={{ marginTop: 10, padding: '8px 10px', background: '#1a1a1a', borderRadius: 6, fontSize: 11, color: '#888', lineHeight: 1.7 }}>
                    <div style={{ fontWeight: 600, color: '#aaa', marginBottom: 3 }}>Modification impacts to model:</div>
                    <div>• Diameter increase → recalculate downstream pressures (risk of low velocity / sediment deposit)</div>
                    <div>• Rerouting → update hydraulic model node elevations</div>
                    <div>• Lining → C-factor improves to ~{Math.round(C_new * 0.85)}, flow capacity partially restored</div>
                </div>
            </Section>

            {/* 3. Structural Risk */}
            <Section title="Structural Risk" icon="⚠️" accent={{ text: `${bp.toFixed(2)} breaks/km/yr`, color: cond.color }}>
                <div style={{ marginBottom: 10 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span style={{ fontSize: 12, color: '#888' }}>Break probability (vs 1.5 = critical threshold)</span>
                        <span style={{ fontSize: 12, color: cond.color }}>{bp.toFixed(2)}</span>
                    </div>
                    <Bar value={bp} max={1.5} color={cond.color} />
                </div>
                <Row label="Condition rating"        value={cond.label} highlight={cond.color} />
                <Row label="Break rate"              value={`${bp.toFixed(2)} breaks/km/year`} />
                <Row label="Expected breaks/yr (this segment)" value={asset.length_m ? `${(bp * asset.length_m / 1000).toFixed(2)}` : '—'} />
                <Row label="Remaining service life"  value={rl > 0 ? `~${rl} years` : 'Past design life — replacement warranted'} highlight={rl > 20 ? '#27ae60' : '#e74c3c'} />
                {cost && <Row label="Est. replacement cost"  value={`$${(cost/1000).toFixed(0)}K–$${(cost*1.8/1000).toFixed(0)}K CAD`} highlight="#c8a55c" />}
                <div style={{ marginTop: 10, padding: '8px 10px', background: '#1a1a1a', borderRadius: 6, fontSize: 11, color: '#888', lineHeight: 1.7 }}>
                    {mat === 'AC' && <div style={{ color: '#e74c3c', fontWeight: 600, marginBottom: 4 }}>⚠ Asbestos Cement: ANY disturbance triggers Reg. 278/05. Designated Substance Report required before design.</div>}
                    {(mat === 'CI' || mat === 'CICL') && age > 80 && <div style={{ color: '#e67e22', marginBottom: 4 }}>⚠ CI pipe &gt;80 yrs: CIRC Bulletin recommends replacement assessment. High tuberculation risk.</div>}
                    <div>• Material fatigue accumulates under cyclic pressure (water hammer events)</div>
                    <div>• Consider acoustic leak detection survey before design to identify existing failures</div>
                </div>
            </Section>

            {/* 4. Geotechnical */}
            <Section title="Geotechnical Requirements" icon="🏗️" defaultOpen={false}>
                <Checklist items={geoItems} />
                <div style={{ marginTop: 10, padding: '8px 10px', background: '#1a1a1a', borderRadius: 6, fontSize: 11, color: '#888', lineHeight: 1.7 }}>
                    <div style={{ fontWeight: 600, color: '#aaa', marginBottom: 3 }}>Toronto-specific soil notes:</div>
                    <div>• Lakebed clays common below ~3 m — low bearing, high corrosivity</div>
                    <div>• Till and glaciofluvial sands near surface — generally stable</div>
                    <div>• Former watercourse corridors: soft/organic fill possible — probe before routing</div>
                    <div>• Groundwater at 1–2 m in lakefront wards — dewatering plan required</div>
                </div>
            </Section>

            {/* 5. Permitting Pathway */}
            <Section title="Permitting Pathway" icon="📋" defaultOpen={false}>
                <Checklist items={permitItems} />
                <div style={{ marginTop: 10, padding: '8px 10px', background: '#1a1a1a', borderRadius: 6, fontSize: 11, color: '#888', lineHeight: 1.7 }}>
                    <div style={{ fontWeight: 600, color: '#aaa', marginBottom: 3 }}>Typical timeline (Toronto):</div>
                    <div>• Toronto Water design approval: 3–6 months</div>
                    <div>• ROW permit: 4–8 weeks</div>
                    <div>• Class EA (if required): 12–18 months</div>
                    <div>• TRCA permit: 2–4 months</div>
                </div>
            </Section>

            {/* 6. Material Selection */}
            <Section title="Material Selection" icon="🔩" defaultOpen={false}>
                <div style={{ marginBottom: 8 }}>
                    <div style={{ fontSize: 11, color: '#888', marginBottom: 6 }}>Recommended replacement:</div>
                    <div style={{ padding: '8px 10px', background: '#1a2a1a', border: '1px solid #27ae6044', borderRadius: 6, fontSize: 12, color: '#27ae60' }}>
                        {replaceMat}
                    </div>
                </div>
                {[
                    { mat: 'HDPE', c: 150, life: 100, cost: '$900–1,400/m', note: 'Trenchless capable (CIPP/pipe bursting). Flexible, corrosion-free. Preferred for rehab.' },
                    { mat: 'DIP',  c: 140, life: 100, cost: '$1,100–1,800/m', note: 'High strength, joints allow deflection. Standard open-cut replacement.' },
                    { mat: 'DICL', c: 140, life: 120, cost: '$1,200–2,000/m', note: 'Cement-mortar lined. Best for aggressive soils or high-corrosivity zones.' },
                    { mat: 'PVC',  c: 150, life: 80,  cost: '$700–1,100/m', note: 'Lower pressure classes only. Lightweight, good for small-dia service connections.' },
                ].map(({ mat: m, c, life, cost: co, note }) => (
                    <div key={m} style={{ marginBottom: 8, padding: '8px 10px', background: '#1a1a1a', borderRadius: 6, border: '1px solid #2a2a2a' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                            <span style={{ fontWeight: 600, fontSize: 12, color: MATERIAL_COLORS[m] || '#f0ece4' }}>{m}</span>
                            <span style={{ fontSize: 11, color: '#888' }}>C={c} · {life} yr life · {co}</span>
                        </div>
                        <div style={{ fontSize: 11, color: '#777', lineHeight: 1.5 }}>{note}</div>
                    </div>
                ))}
            </Section>

            {/* 7. Environmental */}
            <Section title="Environmental Flags" icon="🌿" defaultOpen={false}>
                <Checklist items={[
                    { done: false, text: 'Check TRCA Regulated Area mapping before routing', sub: 'toronto.ca/city-government/planning-development/official-plan-guidelines/greens' },
                    { done: false, text: 'Stage 1 Archaeological Assessment if greenspace route', sub: 'Ontario Heritage Act — required if disturbing undisturbed soil in sensitive areas' },
                    { done: false, text: 'Species at Risk screening (MNRF Natural Heritage Tool)', sub: 'Required for any EA project class' },
                    ...(mat === 'AC' ? [{ done: false, urgent: true, text: 'Asbestos Waste Disposal Plan', sub: 'Reg. 347 — designated waste, licensed hauler to licensed facility only' }] : []),
                    { done: false, text: 'Construction dewatering plan and discharge permit', sub: 'If groundwater encountered: Toronto & Region Conservation — permit to take water' },
                    { done: false, text: 'Spill Prevention and Response Plan', sub: 'Required during construction for all fuel/chemical storage on site' },
                ]} />
            </Section>

        </div>
    );
}

const UPLOAD_POLL_MS = 3000;
const UPLOAD_MAX_ATTEMPTS = 40;
const MAX_FILE_SIZE = 50 * 1024 * 1024;
const ACCEPTED_TYPES = '.pdf,.png,.jpg,.jpeg,.xlsx,.xls,.csv,.dwg,.dxf,.doc,.docx';

function FileUploadZone({ onUploadComplete }) {
    const [isDragOver, setIsDragOver] = useState(false);
    const [uploads, setUploads] = useState([]);
    const fileInputRef = useRef(null);
    const pollControllersRef = useRef({});

    useEffect(() => {
        return () => {
            Object.values(pollControllersRef.current).forEach((c) => c.abort());
        };
    }, []);

    const pollUpload = useCallback(async (uploadId, filename) => {
        const controller = new AbortController();
        pollControllersRef.current[uploadId] = controller;
        const { signal } = controller;

        try {
            for (let i = 0; i < UPLOAD_MAX_ATTEMPTS; i++) {
                await new Promise((resolve, reject) => {
                    const timer = setTimeout(resolve, UPLOAD_POLL_MS);
                    signal.addEventListener('abort', () => { clearTimeout(timer); reject(new DOMException('Aborted', 'AbortError')); }, { once: true });
                });
                const upload = await getUpload(uploadId, { signal });
                if (signal.aborted) return;

                if (upload.status === 'analyzed') {
                    const summary = [];
                    if (upload.doc_category) summary.push(upload.doc_category.replace(/_/g, ' '));
                    if (upload.page_count) summary.push(`${upload.page_count} pages`);
                    const extracted = upload.extracted_data?.building || {};
                    const items = [];
                    if (extracted.storeys) items.push(`${extracted.storeys} storeys`);
                    if (extracted.unit_count) items.push(`${extracted.unit_count} units`);
                    if (extracted.height_m) items.push(`${extracted.height_m}m`);
                    if (items.length) summary.push(items.join(', '));
                    const issueCount = upload.compliance_findings?.issues?.length || 0;

                    setUploads((prev) => prev.map((u) =>
                        u.id === uploadId ? { ...u, status: 'analyzed', summary: summary.join(' · '), issueCount, extractedData: upload.extracted_data } : u
                    ));
                    onUploadComplete?.({ id: uploadId, filename, extractedData: upload.extracted_data });
                    return;
                }
                if (upload.status === 'failed') {
                    setUploads((prev) => prev.map((u) =>
                        u.id === uploadId ? { ...u, status: 'failed', error: upload.error_message || 'Analysis failed' } : u
                    ));
                    return;
                }
            }
            setUploads((prev) => prev.map((u) =>
                u.id === uploadId ? { ...u, status: 'timeout' } : u
            ));
        } catch (error) {
            if (error?.name !== 'AbortError') {
                setUploads((prev) => prev.map((u) =>
                    u.id === uploadId ? { ...u, status: 'failed', error: error.message } : u
                ));
            }
        } finally {
            delete pollControllersRef.current[uploadId];
        }
    }, [onUploadComplete]);

    const handleFile = useCallback(async (file) => {
        if (!file) return;
        if (file.size > MAX_FILE_SIZE) {
            setUploads((prev) => [...prev, { id: `err-${Date.now()}`, filename: file.name, status: 'failed', error: 'File exceeds 50 MB limit' }]);
            return;
        }
        const tempId = `temp-${Date.now()}`;
        setUploads((prev) => [...prev, { id: tempId, filename: file.name, status: 'uploading' }]);

        try {
            const result = await uploadDocument(file);
            if (result.status === 'analyzed' && result.extracted_data) {
                // Immediate result (e.g. DXF parsed inline)
                setUploads((prev) => prev.map((u) =>
                    u.id === tempId ? { ...u, id: result.id, status: 'analyzed', summary: 'Parsed', extractedData: result.extracted_data } : u
                ));
                onUploadComplete?.({ id: result.id, filename: file.name, extractedData: result.extracted_data });
            } else {
                setUploads((prev) => prev.map((u) =>
                    u.id === tempId ? { ...u, id: result.id, status: 'processing' } : u
                ));
                pollUpload(result.id, file.name);
            }
        } catch (err) {
            setUploads((prev) => prev.map((u) =>
                u.id === tempId ? { ...u, status: 'failed', error: err.message } : u
            ));
        }
    }, [pollUpload]);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragOver(false);
        const files = Array.from(e.dataTransfer?.files || []);
        files.forEach(handleFile);
    }, [handleFile]);

    const handleRemove = useCallback((id) => {
        pollControllersRef.current[id]?.abort();
        setUploads((prev) => prev.filter((u) => u.id !== id));
    }, []);

    const statusLabel = (upload) => {
        if (upload.status === 'uploading') return 'Uploading...';
        if (upload.status === 'processing') return 'Analyzing...';
        if (upload.status === 'analyzed') return 'Analyzed';
        if (upload.status === 'failed') return upload.error || 'Failed';
        if (upload.status === 'timeout') return 'Still processing...';
        return upload.status;
    };

    const statusClass = (upload) => {
        if (upload.status === 'analyzed') return 'upload-status-ok';
        if (upload.status === 'failed') return 'upload-status-error';
        return 'upload-status-pending';
    };

    return (
        <div className="upload-zone-wrapper">
            <div className="dd-card-label" style={{ marginBottom: 8 }}>Project Files</div>
            <div
                className={`upload-dropzone ${isDragOver ? 'upload-dropzone-active' : ''}`}
                onDrop={handleDrop}
                onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
                onDragLeave={() => setIsDragOver(false)}
                onClick={() => fileInputRef.current?.click()}
                role="button"
                tabIndex={0}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept={ACCEPTED_TYPES}
                    style={{ display: 'none' }}
                    onChange={(e) => { Array.from(e.target.files).forEach(handleFile); e.target.value = ''; }}
                />
                <svg className="upload-dropzone-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                <span className="upload-dropzone-text">Drop files here or click to browse</span>
                <span className="upload-dropzone-hint">Blueprints, site plans, reports, drawings, spreadsheets</span>
            </div>

            {uploads.length > 0 && (
                <div className="upload-file-list">
                    {uploads.map((upload) => (
                        <div key={upload.id} className={`upload-file-row ${statusClass(upload)}`}>
                            <div className="upload-file-info">
                                <div className="upload-file-name">
                                    {(upload.status === 'uploading' || upload.status === 'processing') && (
                                        <span className="upload-file-spinner" />
                                    )}
                                    {upload.status === 'analyzed' && (
                                        <svg className="upload-file-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                                            <polyline points="20 6 9 17 4 12" />
                                        </svg>
                                    )}
                                    {upload.status === 'failed' && (
                                        <svg className="upload-file-x" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                                            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                                        </svg>
                                    )}
                                    <span>{upload.filename}</span>
                                </div>
                                <div className="upload-file-status">{statusLabel(upload)}</div>
                                {upload.summary && <div className="upload-file-summary">{upload.summary}</div>}
                                {upload.issueCount > 0 && (
                                    <div className="upload-file-issues">{upload.issueCount} compliance issue{upload.issueCount > 1 ? 's' : ''} found</div>
                                )}
                            </div>
                            <button className="upload-file-remove" onClick={(e) => { e.stopPropagation(); handleRemove(upload.id); }} title="Remove">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                                    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                                </svg>
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function formatMetric(value, suffix = '', fallback = 'Unavailable') {
    if (value === null || value === undefined || value === '') return fallback;
    return `${value}${suffix}`;
}

function isAbortError(error) {
    return error?.name === 'AbortError';
}

function zoneDisplay(parcel, zoning) {
    return zoning?.zoneString || parcel?.zoneCode || parcel?.zoning || 'Unknown';
}

function zoningNotes(zoning) {
    if (!zoning) return [];
    const overlayNotes = (zoning.overlayConstraints || [])
        .map((constraint) => constraint.impact)
        .filter(Boolean);
    return [...new Set([...(zoning.warnings || []), ...overlayNotes])];
}

function ReviewNotesCard({ zoning }) {
    const notes = zoningNotes(zoning);
    if (notes.length === 0) return null;

    return (
        <div className="dd-card">
            <div className="dd-card-label">Review Notes</div>
            <ul style={{ margin: '10px 0 0 18px', padding: 0 }}>
                {notes.map((note) => (
                    <li key={note} style={{ marginBottom: 8 }}>
                        {note}
                    </li>
                ))}
            </ul>
        </div>
    );
}

function LoadingZoningTab({ parcel }) {
    return (
        <div className="tab-section-header">
            <h3>Loading Zoning Analysis</h3>
            <p className="tab-section-desc">Fetching backend zoning analysis for {parcel.address}…</p>
        </div>
    );
}

function OverviewTab({ parcel, zoning, onUploadComplete }) {
    const zoneName = zoneDisplay(parcel, zoning);

    return (
        <>
            <FileUploadZone onUploadComplete={onUploadComplete} />

            <div className="dd-address-badge" style={{ marginTop: 16 }}>
                <span className="dd-zone-chip">{zoning.zoneCategory || parcel.zoning || '—'}</span>
                <span>{parcel.address}</span>
            </div>

            <div className="tab-section-header">
                <h3>Zoning Summary</h3>
                <p className="tab-section-desc">Backend zoning analysis for {zoneName}.</p>
            </div>

            <div className="dd-card">
                <div className="dd-card-label">Zone Classification</div>
                <div className="dd-card-value">{zoning.label}</div>
            </div>
            <div className="dd-card">
                <div className="dd-card-label">By-law Reference</div>
                <div className="dd-card-value">{formatMetric(zoning.bylawSection, '', 'Unavailable')}</div>
            </div>

            <div className="zoning-limits-grid">
                {[
                    { label: 'Max Height', value: formatMetric(zoning.maxHeight, ' m') },
                    { label: 'Max FSI', value: formatMetric(zoning.maxFsi) },
                    { label: 'Max Storeys', value: formatMetric(zoning.maxStoreys) },
                    { label: 'Lot Coverage', value: formatMetric(zoning.lotCoverage, '%') },
                ].map((item) => (
                    <div key={item.label} className="zoning-limit-card">
                        <div className="dd-card-label">{item.label}</div>
                        <div className="dd-card-value">{item.value}</div>
                    </div>
                ))}
            </div>

            <div className="dd-card">
                <div className="dd-card-label">Permitted Uses</div>
                <div className="tag-list">
                    {(zoning.uses || []).length > 0
                        ? zoning.uses.map((use) => <span key={use} className="tag">{use}</span>)
                        : <span className="tag">No uses surfaced</span>
                    }
                </div>
            </div>
            <ReviewNotesCard zoning={zoning} />
        </>
    );
}

function PoliciesTab({ policies, loading }) {
    const [expanded, setExpanded] = useState({});
    const toggle = (idx) => setExpanded((prev) => ({ ...prev, [idx]: !prev[idx] }));

    if (loading) {
        return (
            <div className="tab-section-header">
                <h3>Policy Extracts</h3>
                <p className="tab-section-desc">Loading applicable policies…</p>
            </div>
        );
    }

    if (!policies || policies.length === 0) {
        return (
            <div className="tab-section-header">
                <h3>Policy Extracts</h3>
                <p className="tab-section-desc">No policies found for this parcel.</p>
            </div>
        );
    }

    return (
        <>
            <div className="tab-section-header">
                <h3>Policy Extracts</h3>
                <p className="tab-section-desc">Relevant legislation and guidelines for this parcel.</p>
            </div>

            <div className="policy-accordion">
                {policies.map((doc, idx) => (
                    <div key={idx} className={`accordion-item ${expanded[idx] ? 'accordion-open' : ''}`}>
                        <button className="accordion-header" onClick={() => toggle(idx)}>
                            <div className="accordion-title">
                                <svg className="accordion-doc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                    <polyline points="14 2 14 8 20 8" />
                                </svg>
                                <span>{doc.name}</span>
                            </div>
                            <div className="accordion-meta">
                                <span className="accordion-count">{doc.extracts} extracts</span>
                                <svg className="accordion-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <polyline points="6 9 12 15 18 9" />
                                </svg>
                            </div>
                        </button>
                        {expanded[idx] && (
                            <div className="accordion-body">
                                {doc.sections.length > 0 ? doc.sections.map((section, sectionIndex) => (
                                    <div key={sectionIndex} className="extract-block">
                                        <div className="extract-title">{section.title}</div>
                                        <p className="extract-text">{section.text}</p>
                                    </div>
                                )) : (
                                    <p className="extract-text" style={{ opacity: 0.5 }}>No clause extracts available for this document.</p>
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </>
    );
}

function DatasetsTab({ overlays, loading }) {
    if (loading) {
        return (
            <div className="tab-section-header">
                <h3>Data Sources</h3>
                <p className="tab-section-desc">Loading overlays…</p>
            </div>
        );
    }

    if (!overlays || overlays.length === 0) {
        return (
            <div className="tab-section-header">
                <h3>Data Sources</h3>
                <p className="tab-section-desc">No overlay datasets found for this parcel.</p>
            </div>
        );
    }

    return (
        <>
            <div className="tab-section-header">
                <h3>Data Sources</h3>
                <p className="tab-section-desc">Municipally-verified datasets intersecting this parcel.</p>
            </div>
            <div className="datasets-list">
                {overlays.map((overlay, idx) => (
                    <div key={idx} className="dataset-row">
                        <div className="dataset-row-left">
                            <svg className="dataset-row-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <ellipse cx="12" cy="5" rx="9" ry="3" />
                                <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
                                <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
                            </svg>
                            <div>
                                <div className="dataset-row-name">{overlay.name}</div>
                                <div className="dataset-row-desc">{overlay.description}</div>
                            </div>
                        </div>
                        {overlay.values != null && (
                            <div className="dataset-row-meta">{overlay.values} values</div>
                        )}
                    </div>
                ))}
            </div>
        </>
    );
}

function PrecedentsTab({ parcel }) {
    const [applications, setApplications] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!parcel?.id) return;
        const controller = new AbortController();
        setLoading(true);
        setError(null);
        getNearbyApplications(parcel.id, { signal: controller.signal })
            .then((data) => {
                setApplications(data.applications || []);
            })
            .catch((err) => {
                if (err?.name !== 'AbortError') setError('Failed to load nearby applications');
            })
            .finally(() => setLoading(false));
        return () => controller.abort();
    }, [parcel?.id]);

    const APP_TYPE_LABELS = { SA: 'Site Alteration', OZ: 'Official Plan / Zoning', CD: 'Condo Approval', SB: 'Site Plan / Boulevard', PL: 'Plan of Subdivision' };
    const DECISION_COLORS = { approved: '#2d8a4e', refused: '#c0392b', appealed: '#e67e22', pending: '#7f8c8d' };

    if (loading) {
        return (
            <div className="tab-section-header">
                <h3>Nearby Applications</h3>
                <p className="tab-section-desc">Loading nearby development applications...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="tab-section-header">
                <h3>Nearby Applications</h3>
                <p className="tab-section-desc" style={{ color: '#c0392b' }}>{error}</p>
            </div>
        );
    }

    if (!applications.length) {
        return (
            <div className="tab-section-header">
                <h3>Nearby Applications</h3>
                <p className="tab-section-desc">No development applications found within 2km of {parcel.address}.</p>
            </div>
        );
    }

    return (
        <>
            <div className="tab-section-header">
                <h3>Nearby Applications</h3>
                <p className="tab-section-desc">{applications.length} development application{applications.length !== 1 ? 's' : ''} within 2km</p>
            </div>
            <div className="dataset-list">
                {applications.map((app) => (
                    <div key={app.id} className="dataset-row">
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, flex: 1 }}>
                            <div style={{
                                width: 8, height: 8, borderRadius: '50%', marginTop: 6, flexShrink: 0,
                                backgroundColor: DECISION_COLORS[app.decision] || '#999',
                            }} />
                            <div style={{ flex: 1 }}>
                                <div className="dataset-row-name">{app.address || app.app_number}</div>
                                <div className="dataset-row-desc">
                                    {APP_TYPE_LABELS[app.app_type] || app.app_type}
                                    {app.proposed_height_m ? ` · ${app.proposed_height_m}m` : ''}
                                    {app.proposed_units ? ` · ${app.proposed_units} units` : ''}
                                </div>
                            </div>
                        </div>
                        <div style={{ textAlign: 'right', flexShrink: 0 }}>
                            <div style={{ fontSize: 12, color: DECISION_COLORS[app.decision] || '#999', fontWeight: 500 }}>
                                {app.decision || app.status || 'unknown'}
                            </div>
                            {app.distance_m != null && (
                                <div style={{ fontSize: 11, opacity: 0.6 }}>{app.distance_m < 1000 ? `${Math.round(app.distance_m)}m` : `${(app.distance_m / 1000).toFixed(1)}km`}</div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </>
    );
}

function UnresolvedParcelTab({ parcel }) {
    return (
        <div className="tab-empty">
            <p>{parcel.message}</p>
            <p style={{ marginTop: 10, opacity: 0.75 }}>
                The map can still center this address, but parcel-linked zoning, policy, datasets, precedents, and entitlements stay unavailable until a parcel record is matched.
            </p>
        </div>
    );
}

function MissingZoningGuidanceTab({ parcel }) {
    return (
        <div className="tab-empty">
            <p>
                This parcel resolved successfully, but the backend could not derive zoning standards for
                {' '}
                <strong>{parcel.zoneCode || parcel.zoning || 'unknown'}</strong>.
            </p>
            <p style={{ marginTop: 10, opacity: 0.75 }}>
                Policy extracts and datasets may still be available in their tabs, but overview, massing, and entitlement guidance are unavailable here.
            </p>
        </div>
    );
}

function formatCurrency(val) {
    if (val == null) return '—';
    if (Math.abs(val) >= 1e6) return `$${(val / 1e6).toFixed(1)}M`;
    if (Math.abs(val) >= 1e3) return `$${(val / 1e3).toFixed(0)}K`;
    return `$${val.toLocaleString()}`;
}

function FinancesTab({ parcel }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [activeEstimate, setActiveEstimate] = useState('rental');

    useEffect(() => {
        if (!parcel?.id) return;
        const controller = new AbortController();
        setLoading(true);
        getParcelFinancialSummary(parcel.id, { signal: controller.signal })
            .then((d) => { if (d) setData(d); })
            .catch(() => {})
            .finally(() => setLoading(false));
        return () => controller.abort();
    }, [parcel?.id]);

    if (loading) return <div className="tab-section-header"><h3>Financial Feasibility</h3><p className="tab-section-desc">Loading financial data...</p></div>;
    if (!data) return <div className="tab-section-header"><h3>Financial Feasibility</h3><p className="tab-section-desc">No financial data available for this parcel.</p></div>;

    const estimate = data.estimates?.[activeEstimate];
    const COMP_TYPE_LABELS = { rental: 'Rental', sale: 'Condo Sale', land_sale: 'Land Sale', construction_cost: 'Construction' };

    return (
        <>
            <div className="tab-section-header">
                <h3>Financial Feasibility</h3>
                <p className="tab-section-desc">Quick pro forma estimate for {data.address}</p>
            </div>

            {/* Parcel metrics */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, padding: '0 16px 12px' }}>
                <div className="kpi-card">
                    <div className="kpi-label">Assessed Value</div>
                    <div className="kpi-value">{formatCurrency(data.assessed_value)}</div>
                </div>
                <div className="kpi-card">
                    <div className="kpi-label">Max GFA</div>
                    <div className="kpi-value">{data.estimated_gfa_m2 ? `${data.estimated_gfa_m2.toLocaleString()} m²` : '—'}</div>
                </div>
                <div className="kpi-card">
                    <div className="kpi-label">Lot Area</div>
                    <div className="kpi-value">{data.lot_area_m2 ? `${Math.round(data.lot_area_m2).toLocaleString()} m²` : '—'}</div>
                </div>
                <div className="kpi-card">
                    <div className="kpi-label">Max FSI / Height</div>
                    <div className="kpi-value">{data.max_fsi ?? '—'} / {data.max_height_m ? `${data.max_height_m}m` : '—'}</div>
                </div>
            </div>

            {/* Tenure toggle */}
            {Object.keys(data.estimates || {}).length > 0 && (
                <div style={{ padding: '0 16px 8px', display: 'flex', gap: 6 }}>
                    {Object.keys(data.estimates).map((key) => (
                        <button
                            key={key}
                            onClick={() => setActiveEstimate(key)}
                            className={`tenure-toggle ${activeEstimate === key ? 'active' : ''}`}
                        >
                            {key === 'rental' ? 'Rental' : 'Condo'}
                        </button>
                    ))}
                </div>
            )}

            {/* Pro forma estimate */}
            {estimate && (
                <div style={{ padding: '0 16px 12px' }}>
                    <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, opacity: 0.7 }}>Pro Forma Estimate</div>
                    <div className="proforma-table">
                        <div className="proforma-row"><span>Revenue</span><span style={{ color: '#2d8a4e' }}>{formatCurrency(estimate.revenue)}</span></div>
                        {estimate.noi != null && <div className="proforma-row"><span>NOI</span><span>{formatCurrency(estimate.noi)}</span></div>}
                        <div className="proforma-row"><span>Hard Cost</span><span style={{ color: '#c0392b' }}>{formatCurrency(estimate.hard_cost)}</span></div>
                        <div className="proforma-row"><span>Soft Cost</span><span style={{ color: '#c0392b' }}>{formatCurrency(estimate.soft_cost)}</span></div>
                        <div className="proforma-row total"><span>Total Cost</span><span style={{ color: '#c0392b' }}>{formatCurrency(estimate.total_cost)}</span></div>
                        <div className="proforma-row"><span>Valuation</span><span>{formatCurrency(estimate.valuation)}</span></div>
                        <div className="proforma-row total" style={{ borderTop: '2px solid var(--border-color)' }}>
                            <span>Residual Land Value</span>
                            <span style={{ color: estimate.residual_land_value >= 0 ? '#2d8a4e' : '#c0392b', fontWeight: 700 }}>
                                {formatCurrency(estimate.residual_land_value)}
                            </span>
                        </div>
                    </div>
                </div>
            )}

            {/* Market comps */}
            {data.nearby_comps?.length > 0 && (
                <div style={{ padding: '0 16px 12px' }}>
                    <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, opacity: 0.7 }}>
                        Nearby Market Comps ({data.nearby_comps.length})
                    </div>
                    <div className="dataset-list">
                        {data.nearby_comps.map((comp, i) => (
                            <div key={i} className="dataset-row" style={{ padding: '8px 0' }}>
                                <div style={{ flex: 1 }}>
                                    <div className="dataset-row-name">{comp.address}</div>
                                    <div className="dataset-row-desc">
                                        {COMP_TYPE_LABELS[comp.comp_type] || comp.comp_type}
                                        {comp.attributes?.rent_psf_monthly ? ` · $${comp.attributes.rent_psf_monthly}/psf/mo` : ''}
                                        {comp.attributes?.sale_psf ? ` · $${comp.attributes.sale_psf}/psf` : ''}
                                        {comp.attributes?.price_per_buildable_sqft ? ` · $${comp.attributes.price_per_buildable_sqft}/bsf` : ''}
                                        {comp.attributes?.hard_cost_psf ? ` · $${comp.attributes.hard_cost_psf}/psf` : ''}
                                        {comp.attributes?.units ? ` · ${comp.attributes.units} units` : ''}
                                    </div>
                                </div>
                                {comp.distance_m != null && (
                                    <div style={{ fontSize: 11, opacity: 0.6, flexShrink: 0 }}>
                                        {comp.distance_m < 1000 ? `${Math.round(comp.distance_m)}m` : `${(comp.distance_m / 1000).toFixed(1)}km`}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </>
    );
}

function mapPolicyStack(data) {
    if (!data) return [];
    const entries = data.applicable_policies || [];
    const byDoc = {};

    for (const entry of entries) {
        const key = entry.document_id || entry.document_title;
        if (!byDoc[key]) {
            byDoc[key] = {
                name: entry.document_title || entry.doc_type || 'Policy Document',
                sections: [],
            };
        }
        if (entry.raw_text || entry.section_ref) {
            byDoc[key].sections.push({
                title: entry.section_ref || 'Section',
                text: entry.raw_text || '',
            });
        }
    }

    return Object.values(byDoc).map((doc) => ({
        ...doc,
        extracts: doc.sections.length,
    }));
}

function mapOverlays(data) {
    if (!data) return [];
    const overlays = data.overlays || [];
    const byLayer = {};

    for (const overlay of overlays) {
        const key = overlay.layer_id || overlay.layer_name || overlay.layer_type;
        if (!byLayer[key]) {
            byLayer[key] = {
                name: overlay.layer_name || overlay.name || overlay.layer_type || 'Dataset',
                description: overlay.source_url ? `Source: ${overlay.source_url}` : (overlay.layer_type || ''),
                count: 0,
            };
        }
        byLayer[key].count += 1;
    }

    return Object.values(byLayer).map((layer) => ({
        name: layer.name,
        description: layer.description,
        values: layer.count,
    }));
}

function mapZoningAnalysis(data) {
    if (!data?.standards) return null;
    const standards = data.standards;
    return {
        zoneString: data.zone_string || null,
        zoneCategory: data.components?.category || standards.category || null,
        label: standards.label || standards.category || 'Unknown Zone',
        maxHeight: standards.max_height_m,
        maxStoreys: standards.max_storeys,
        maxFsi: standards.max_fsi,
        frontSetback: standards.min_front_setback_m,
        rearSetback: standards.min_rear_setback_m,
        sideSetback: standards.min_interior_side_setback_m,
        exteriorSideSetback: standards.min_exterior_side_setback_m,
        lotCoverage: standards.max_lot_coverage_pct,
        landscaping: standards.min_landscaping_pct,
        uses: standards.permitted_uses || [],
        bylawSection: standards.bylaw_section,
        warnings: data.warnings || [],
        overlayConstraints: data.overlay_constraints || [],
    };
}

function DocumentsTab({ planId }) {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedDoc, setSelectedDoc] = useState(null);

    useEffect(() => {
        if (!planId) return;
        let cancelled = false;
        setLoading(true);
        getPlanDocuments(planId).then((docs) => {
            if (!cancelled) {
                setDocuments(docs);
                setLoading(false);
            }
        }).catch(() => { if (!cancelled) setLoading(false); });
        return () => { cancelled = true; };
    }, [planId]);

    const handleRegenerate = useCallback(async (docType) => {
        try {
            const doc = await regeneratePlanDocument(planId, docType, {});
            setDocuments((prev) => {
                const exists = prev.find((d) => d.doc_type === docType);
                if (exists) return prev.map((d) => d.doc_type === docType ? doc : d);
                return [...prev, doc];
            });
            setSelectedDoc(doc);
        } catch (err) {
            console.error('Regenerate failed:', err);
        }
    }, [planId]);

    if (!planId) {
        return (
            <div style={{ padding: 20, textAlign: 'center', opacity: 0.7 }}>
                <p>Generate a plan to view documents.</p>
                <p style={{ fontSize: 12, marginTop: 8 }}>Use the chat panel to generate a development plan, then view and manage documents here.</p>
            </div>
        );
    }

    if (loading) {
        return <div style={{ padding: 20, textAlign: 'center' }}>Loading documents...</div>;
    }

    const selected = selectedDoc || (documents.length > 0 ? documents[0] : null);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
            <div style={{ padding: '8px 12px', borderBottom: '1px solid #eee', fontSize: 12, color: '#666' }}>
                {documents.length} document{documents.length !== 1 ? 's' : ''} generated
            </div>
            <div style={{ flex: 1, overflow: 'auto', padding: '8px 0' }}>
                {documents.map((doc) => (
                    <button
                        key={doc.id}
                        onClick={() => setSelectedDoc(doc)}
                        style={{
                            display: 'flex', alignItems: 'center', gap: 8,
                            width: '100%', padding: '8px 12px', border: 'none', cursor: 'pointer',
                            background: selected?.id === doc.id ? '#f0f4ff' : 'transparent',
                            borderLeft: selected?.id === doc.id ? '3px solid #3b82f6' : '3px solid transparent',
                            textAlign: 'left', fontSize: 13,
                        }}
                    >
                        <span style={{
                            width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                            background: doc.review_status === 'approved' ? '#4caf50' : doc.review_status === 'under_review' ? '#ff9800' : '#9e9e9e',
                        }} />
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{doc.title}</span>
                    </button>
                ))}
            </div>
            {selected && (
                <div style={{ borderTop: '1px solid #eee', padding: 12, maxHeight: '50%', overflow: 'auto' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                        <strong style={{ fontSize: 13 }}>{selected.title}</strong>
                        <button
                            onClick={() => handleRegenerate(selected.doc_type)}
                            style={{ fontSize: 11, padding: '2px 8px', border: '1px solid #ccc', borderRadius: 4, cursor: 'pointer', background: '#fff' }}
                        >
                            Regenerate
                        </button>
                    </div>
                    <div style={{ fontSize: 12, lineHeight: 1.5, maxHeight: 300, overflow: 'auto', whiteSpace: 'pre-wrap', color: '#333' }}>
                        {(selected.content_text || '').slice(0, 2000)}
                        {(selected.content_text || '').length > 2000 && '...'}
                    </div>
                    <div style={{ marginTop: 8, fontSize: 11, color: '#888' }}>
                        Status: {selected.review_status} | Format: {selected.format}
                    </div>
                </div>
            )}
        </div>
    );
}

const TAB_TITLES = {
    overview: 'Project Overview',
    finances: 'Financial Analysis',
    policies: 'Policy Extracts',
    datasets: 'Data Sources',
    precedents: 'Precedents',
    documents: 'Documents',
    standards: 'Design Standards',
    network: 'Pipeline Network',
    inspections: 'Inspection Records',
};

const ZONING_TABS = new Set(['overview']);

function InfraStandardsTab() {
    return (
        <div className="tab-section">
            <h3 className="section-heading">Pipeline Design Standards</h3>
            <div className="policy-list">
                <div className="policy-item">
                    <span className="policy-badge">CSA</span>
                    <div className="policy-details">
                        <div className="policy-title">CSA Z662 — Oil and Gas Pipeline Systems</div>
                        <div className="policy-desc">Design, construction, operation, and maintenance requirements</div>
                    </div>
                </div>
                <div className="policy-item">
                    <span className="policy-badge">OPSD</span>
                    <div className="policy-details">
                        <div className="policy-title">OPSD 802 — Storm Sewer Design</div>
                        <div className="policy-desc">Ontario Provincial Standard Drawings for storm sewer construction</div>
                    </div>
                </div>
                <div className="policy-item">
                    <span className="policy-badge">OPSD</span>
                    <div className="policy-details">
                        <div className="policy-title">OPSD 803 — Sanitary Sewer Design</div>
                        <div className="policy-desc">Ontario Provincial Standard Drawings for sanitary sewer construction</div>
                    </div>
                </div>
                <div className="policy-item">
                    <span className="policy-badge">ECA</span>
                    <div className="policy-details">
                        <div className="policy-title">Environmental Compliance Approval</div>
                        <div className="policy-desc">MECP approval required for sewage works under Ontario Water Resources Act</div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function InfraNetworkTab() {
    return (
        <div className="tab-section">
            <h3 className="section-heading">Pipeline Network</h3>
            <p className="section-description">Select a location on the map to view nearby pipeline infrastructure, including storm sewers, sanitary sewers, water mains, and gas lines.</p>
            <div className="policy-list">
                <div className="policy-item">
                    <span className="policy-badge" style={{ background: 'var(--accent-bg)', color: 'var(--accent)' }}>Storm</span>
                    <div className="policy-details">
                        <div className="policy-title">Storm Sewer Network</div>
                        <div className="policy-desc">Municipal storm drainage system and outfall locations</div>
                    </div>
                </div>
                <div className="policy-item">
                    <span className="policy-badge" style={{ background: 'rgba(74, 222, 128, 0.12)', color: 'var(--success)' }}>Sanitary</span>
                    <div className="policy-details">
                        <div className="policy-title">Sanitary Sewer Network</div>
                        <div className="policy-desc">Wastewater collection system and treatment plant connections</div>
                    </div>
                </div>
                <div className="policy-item">
                    <span className="policy-badge" style={{ background: 'rgba(96, 165, 250, 0.12)', color: '#60a5fa' }}>Water</span>
                    <div className="policy-details">
                        <div className="policy-title">Water Main Network</div>
                        <div className="policy-desc">Pressurized water distribution system and hydrant locations</div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function InfraInspectionsTab() {
    return (
        <div className="tab-section">
            <h3 className="section-heading">Inspection Records</h3>
            <p className="section-description">CCTV inspection records, condition assessments, and maintenance history for nearby pipeline infrastructure.</p>
            <div className="tab-empty">
                <p>Search for a location to view inspection records for nearby infrastructure.</p>
            </div>
        </div>
    );
}


export default function PolicyPanel({ parcel, isOpen, onClose, activeNav, savedParcels, onSaveParcel, onUploadAnalyzed, activePlanId, assetType, selectedPipelineAsset }) {
    const { isResizing, handleProps: resizeHandleProps } = useResizable({
        defaultSize: 380,
        minSize: 280,
        maxSize: 600,
        axis: 'horizontal',
        reverse: true,
        cssVar: '--panel-width',
    });
    const [policies, setPolicies] = useState([]);
    const [overlays, setOverlays] = useState([]);
    const [zoningAnalysis, setZoningAnalysis] = useState(null);
    const [loadingPolicies, setLoadingPolicies] = useState(false);
    const [loadingOverlays, setLoadingOverlays] = useState(false);
    const [loadingZoning, setLoadingZoning] = useState(false);

    useEffect(() => {
        if (!isResolvedParcel(parcel)) {
            setPolicies([]);
            setOverlays([]);
            setZoningAnalysis(null);
            setLoadingPolicies(false);
            setLoadingOverlays(false);
            setLoadingZoning(false);
            return undefined;
        }

        const controller = new AbortController();
        const requestOptions = { signal: controller.signal };

        setLoadingPolicies(true);
        setLoadingOverlays(true);
        setLoadingZoning(true);

        getPolicyStack(parcel.id, requestOptions)
            .then((data) => {
                setPolicies(mapPolicyStack(data));
            })
            .catch((error) => {
                if (!isAbortError(error)) setPolicies([]);
            })
            .finally(() => {
                if (!controller.signal.aborted) setLoadingPolicies(false);
            });

        getParcelOverlays(parcel.id, requestOptions)
            .then((data) => {
                setOverlays(mapOverlays(data));
            })
            .catch((error) => {
                if (!isAbortError(error)) setOverlays([]);
            })
            .finally(() => {
                if (!controller.signal.aborted) setLoadingOverlays(false);
            });

        getParcelZoningAnalysis(parcel.id, requestOptions)
            .then((data) => {
                setZoningAnalysis(data);
            })
            .catch((error) => {
                if (!isAbortError(error)) setZoningAnalysis(null);
            })
            .finally(() => {
                if (!controller.signal.aborted) setLoadingZoning(false);
            });

        return () => {
            controller.abort();
        };
    }, [parcel]);

    const zoning = useMemo(() => mapZoningAnalysis(zoningAnalysis), [zoningAnalysis]);
    const visiblePolicies = isResolvedParcel(parcel) ? policies : [];
    const visibleOverlays = isResolvedParcel(parcel) ? overlays : [];
    const visiblePoliciesLoading = isResolvedParcel(parcel) ? loadingPolicies : false;
    const visibleOverlaysLoading = isResolvedParcel(parcel) ? loadingOverlays : false;
    const visibleZoningLoading = isResolvedParcel(parcel) ? loadingZoning : false;

    const renderTab = () => {
        // Pipeline mode: show asset detail when a segment is clicked
        if (assetType === 'pipeline' && selectedPipelineAsset && activeNav === 'overview') {
            return <PipelineAssetPanel asset={selectedPipelineAsset} />;
        }

        if (!parcel) {
            return (
                <div className="tab-empty">
                    {activeNav === 'overview' && assetType !== 'pipeline' && <FileUploadZone onUploadComplete={onUploadAnalyzed} />}
                    <p>{assetType === 'pipeline'
                        ? 'Click a pipeline segment on the map to view asset details.'
                        : 'Search for a property to view due diligence information.'
                    }</p>
                </div>
            );
        }
        if (isUnresolvedParcel(parcel)) {
            return <UnresolvedParcelTab parcel={parcel} />;
        }
        if (visibleZoningLoading && ZONING_TABS.has(activeNav)) {
            return <LoadingZoningTab parcel={parcel} />;
        }
        if (!zoning && ZONING_TABS.has(activeNav)) {
            return <MissingZoningGuidanceTab parcel={parcel} />;
        }

        switch (activeNav) {
            case 'overview':
                return <OverviewTab parcel={parcel} zoning={zoning} onUploadComplete={onUploadAnalyzed} />;
            case 'policies':
                return <PoliciesTab policies={visiblePolicies} loading={visiblePoliciesLoading} />;
            case 'datasets':
                return <DatasetsTab overlays={visibleOverlays} loading={visibleOverlaysLoading} />;
            case 'precedents':
                return <PrecedentsTab parcel={parcel} />;
            case 'finances':
                return <FinancesTab parcel={parcel} />;
            case 'documents':
                return <DocumentsTab planId={activePlanId} />;
            case 'standards':
                return <InfraStandardsTab />;
            case 'network':
                return <InfraNetworkTab />;
            case 'inspections':
                return <InfraInspectionsTab />;
            default:
                return <OverviewTab parcel={parcel} zoning={zoning} onUploadComplete={onUploadAnalyzed} />;
        }
    };

    return (
        <aside id="policy-panel" className={isOpen ? '' : 'panel-hidden'} style={{ userSelect: isResizing ? 'none' : undefined }}>
            <div {...resizeHandleProps} style={{ ...resizeHandleProps.style, left: -2 }} />
            <div id="policy-panel-header">
                <h2 id="policy-panel-title">
                    {assetType === 'pipeline' && selectedPipelineAsset
                        ? (selectedPipelineAsset.location || 'Water Main')
                        : (TAB_TITLES[activeNav] || 'Project Information')}
                </h2>
                <div className="panel-header-actions">
                    {isResolvedParcel(parcel) && onSaveParcel && (
                        <button className="panel-save-btn" onClick={() => onSaveParcel(parcel)} title="Save parcel for comparison">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
                            </svg>
                        </button>
                    )}
                    <button id="policy-panel-close" aria-label="Close panel" onClick={onClose}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="18" y1="6" x2="6" y2="18" />
                            <line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                    </button>
                </div>
            </div>

            <div id="policy-panel-content">
                {savedParcels && savedParcels.length > 0 && (
                    <div className="saved-parcels-strip">
                        <div className="saved-parcels-label">Saved Parcels</div>
                        <div className="saved-parcels-list">
                            {savedParcels.map((savedParcel, idx) => (
                                <div key={idx} className="saved-parcel-chip">
                                    <span className="saved-parcel-zone">{savedParcel.zoning || '—'}</span>
                                    <span className="saved-parcel-addr">{savedParcel.address?.split(',')[0]}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {renderTab()}
            </div>
        </aside>
    );
}
