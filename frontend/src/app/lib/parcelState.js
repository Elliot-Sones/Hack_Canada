const DEFAULT_UNRESOLVED_MESSAGE =
  'No backend parcel match was found for this address. Parcel-linked zoning, policy, and overlay data are unavailable until a parcel record is matched.';

function getDisplayAddress(location) {
  return location?.shortAddress || location?.address || 'Selected location';
}

// Preserve the full zone string when we have it, but also expose a short category label
// for compact chips and UI affordances.
function normalizeZoneCode(zoneCode) {
  if (typeof zoneCode !== 'string') return null;
  const match = zoneCode.trim().match(/^([A-Za-z]+)/);
  return match ? match[1].toUpperCase() : null;
}

export function createResolvedParcel(location, parcelMatch) {
  const zoneCode = parcelMatch?.zone_code ?? parcelMatch?.zoning ?? null;
  return {
    status: 'resolved',
    id: parcelMatch.id,
    address: getDisplayAddress(location),
    fullAddress: location?.address || getDisplayAddress(location),
    zoning: normalizeZoneCode(zoneCode),
    zoneCode,
    lotArea: Number.isFinite(parcelMatch?.lot_area_m2) ? parcelMatch.lot_area_m2 : null,
    geom: parcelMatch?.geom || null,
  };
}

export function createUnresolvedParcel(location, message = DEFAULT_UNRESOLVED_MESSAGE) {
  return {
    status: 'unresolved',
    id: null,
    address: getDisplayAddress(location),
    fullAddress: location?.address || getDisplayAddress(location),
    zoning: null,
    zoneCode: null,
    lotArea: null,
    message,
  };
}

export function buildParcelState(location, parcelMatches) {
  const firstMatch = Array.isArray(parcelMatches) ? parcelMatches[0] : null;
  if (firstMatch?.id) {
    return createResolvedParcel(location, firstMatch);
  }
  return createUnresolvedParcel(location);
}

export function isResolvedParcel(parcel) {
  return parcel?.status === 'resolved' && Boolean(parcel?.id);
}

export function isUnresolvedParcel(parcel) {
  return parcel?.status === 'unresolved';
}

export function formatParcelContext(parcel) {
  if (!isResolvedParcel(parcel)) return null;

  const parts = [`Current parcel: ${parcel.address}`];
  if (parcel.zoneCode || parcel.zoning) parts.push(`Zoning: ${parcel.zoneCode || parcel.zoning}`);
  if (Number.isFinite(parcel.lotArea)) parts.push(`Lot Area: ${parcel.lotArea}m²`);
  return parts.join(', ');
}

// ─── Display helpers (DRY) ───

export function getShortAddress(p) {
  return (p?.address || '').split(',')[0] || 'Parcel';
}

export function getZoneLabel(p) {
  return p?.zoning || p?.zoneCode || '—';
}

// ─── Multi-parcel context for AI chat ───

export function formatMultiParcelContext(parcels, primaryId) {
  if (!Array.isArray(parcels) || parcels.length === 0) return null;

  const valid = parcels.filter(Boolean);
  if (valid.length === 0) return null;

  if (valid.length === 1) return formatParcelContext(valid[0]);

  const lines = valid.map((p) => {
    const tag = p.id === primaryId ? '(PRIMARY)' : '(comparison)';
    if (!isResolvedParcel(p)) {
      return `${tag} [${getShortAddress(p)}] — no parcel data available`;
    }
    const parts = [getShortAddress(p)];
    if (p.zoneCode || p.zoning) parts.push(`Zoning: ${p.zoneCode || p.zoning}`);
    if (Number.isFinite(p.lotArea)) parts.push(`Lot Area: ${p.lotArea}m²`);
    return `${tag} ${parts.join(', ')}`;
  });

  lines.push('Compare and contrast these parcels.');
  return lines.join('\n');
}

// ─── Multi-selection helpers ───

export const MAX_SELECTED_PARCELS = 4;

export function addParcelToSelection(selection, parcel) {
  if (!parcel?.id) return selection;
  if (selection.length >= MAX_SELECTED_PARCELS) return selection;
  if (selection.some(p => p.id === parcel.id)) return selection;
  return [...selection, parcel];
}

export function removeParcelFromSelection(selection, id) {
  return selection.filter(p => p.id !== id);
}

export function toggleParcelInSelection(selection, parcel) {
  if (!parcel?.id) return selection;
  if (selection.some(p => p.id === parcel.id)) {
    return removeParcelFromSelection(selection, parcel.id);
  }
  return addParcelToSelection(selection, parcel);
}

export { DEFAULT_UNRESOLVED_MESSAGE };
