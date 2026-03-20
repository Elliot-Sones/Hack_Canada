import test from 'node:test';
import assert from 'node:assert/strict';

import {
  buildParcelState,
  createResolvedParcel,
  createUnresolvedParcel,
  formatParcelContext,
  formatMultiParcelContext,
  getShortAddress,
  getZoneLabel,
  isResolvedParcel,
  isUnresolvedParcel,
  addParcelToSelection,
  removeParcelFromSelection,
  toggleParcelInSelection,
  MAX_SELECTED_PARCELS,
} from './parcelState.js';

test('buildParcelState returns a resolved parcel when the backend returns a match', () => {
  const parcel = buildParcelState(
    { shortAddress: '123 King St W, Toronto', address: '123 King St W, Toronto, Ontario, Canada' },
    [{ id: 'parcel-1', zone_code: 'cr', lot_area_m2: 412.5 }]
  );

  assert.equal(parcel.status, 'resolved');
  assert.equal(parcel.id, 'parcel-1');
  assert.equal(parcel.zoning, 'CR');
  assert.equal(parcel.zoneCode, 'cr');
  assert.equal(parcel.lotArea, 412.5);
  assert.equal(isResolvedParcel(parcel), true);
  assert.equal(isUnresolvedParcel(parcel), false);
});

test('buildParcelState returns an unresolved parcel when there is no backend match', () => {
  const parcel = buildParcelState(
    { shortAddress: '404 Unknown Ave, Toronto', address: '404 Unknown Ave, Toronto, Ontario, Canada' },
    []
  );

  assert.equal(parcel.status, 'unresolved');
  assert.equal(parcel.id, null);
  assert.equal(parcel.zoning, null);
  assert.equal(parcel.zoneCode, null);
  assert.match(parcel.message, /No backend parcel match/i);
  assert.equal(isResolvedParcel(parcel), false);
  assert.equal(isUnresolvedParcel(parcel), true);
});

test('formatParcelContext only includes resolved parcel data', () => {
  const resolved = createResolvedParcel(
    { shortAddress: '20 Queen St W, Toronto' },
    { id: 'parcel-2', zone_code: 'RA', lot_area_m2: 250 }
  );
  const unresolved = createUnresolvedParcel({ shortAddress: '20 Queen St W, Toronto' });

  assert.equal(
    formatParcelContext(resolved),
    'Current parcel: 20 Queen St W, Toronto, Zoning: RA, Lot Area: 250m²'
  );
  assert.equal(formatParcelContext(unresolved), null);
});

// ─── Multi-selection helper tests ───────────────────────────────────────────

const mkParcel = (id) => createResolvedParcel(
  { shortAddress: `${id} St` },
  { id, zone_code: 'R', lot_area_m2: 100 }
);

test('addParcelToSelection adds a parcel to empty array', () => {
  const result = addParcelToSelection([], mkParcel('a'));
  assert.equal(result.length, 1);
  assert.equal(result[0].id, 'a');
});

test('addParcelToSelection ignores duplicate', () => {
  const sel = [mkParcel('a')];
  const result = addParcelToSelection(sel, mkParcel('a'));
  assert.equal(result.length, 1);
  assert.equal(result, sel); // same reference
});

test('addParcelToSelection enforces max 4', () => {
  const sel = [mkParcel('a'), mkParcel('b'), mkParcel('c'), mkParcel('d')];
  const result = addParcelToSelection(sel, mkParcel('e'));
  assert.equal(result.length, 4);
  assert.equal(result, sel);
});

test('addParcelToSelection ignores parcel without id', () => {
  const result = addParcelToSelection([], { id: null });
  assert.equal(result.length, 0);
});

test('removeParcelFromSelection removes correct parcel', () => {
  const sel = [mkParcel('a'), mkParcel('b'), mkParcel('c')];
  const result = removeParcelFromSelection(sel, 'b');
  assert.equal(result.length, 2);
  assert.equal(result[0].id, 'a');
  assert.equal(result[1].id, 'c');
});

test('removeParcelFromSelection no-op for missing id', () => {
  const sel = [mkParcel('a')];
  const result = removeParcelFromSelection(sel, 'z');
  assert.equal(result.length, 1);
});

test('toggleParcelInSelection adds if missing', () => {
  const result = toggleParcelInSelection([mkParcel('a')], mkParcel('b'));
  assert.equal(result.length, 2);
});

test('toggleParcelInSelection removes if present', () => {
  const result = toggleParcelInSelection([mkParcel('a'), mkParcel('b')], mkParcel('a'));
  assert.equal(result.length, 1);
  assert.equal(result[0].id, 'b');
});

test('toggleParcelInSelection respects max 4 on add', () => {
  const sel = [mkParcel('a'), mkParcel('b'), mkParcel('c'), mkParcel('d')];
  const result = toggleParcelInSelection(sel, mkParcel('e'));
  assert.equal(result.length, 4);
});

test('MAX_SELECTED_PARCELS is 4', () => {
  assert.equal(MAX_SELECTED_PARCELS, 4);
});

// ─── getShortAddress tests ────────────────────────────────────────────────────

test('getShortAddress returns first segment before comma', () => {
  const p = mkParcel('x');
  // mkParcel creates address "x St"
  assert.equal(getShortAddress(p), 'x St');

  const withComma = { address: '100 King St W, Toronto, ON' };
  assert.equal(getShortAddress(withComma), '100 King St W');
});

test('getShortAddress returns Parcel for null/empty', () => {
  assert.equal(getShortAddress(null), 'Parcel');
  assert.equal(getShortAddress({}), 'Parcel');
  assert.equal(getShortAddress({ address: '' }), 'Parcel');
});

// ─── getZoneLabel tests ───────────────────────────────────────────────────────

test('getZoneLabel fallback chain: zoning → zoneCode → dash', () => {
  assert.equal(getZoneLabel({ zoning: 'CR', zoneCode: 'cr 2.0' }), 'CR');
  assert.equal(getZoneLabel({ zoning: null, zoneCode: 'RA' }), 'RA');
  assert.equal(getZoneLabel({ zoning: null, zoneCode: null }), '—');
  assert.equal(getZoneLabel(null), '—');
});

// ─── formatMultiParcelContext tests ───────────────────────────────────────────

test('formatMultiParcelContext — empty array returns null', () => {
  assert.equal(formatMultiParcelContext([], 'any'), null);
  assert.equal(formatMultiParcelContext(null, 'any'), null);
});

test('formatMultiParcelContext — single parcel delegates to formatParcelContext', () => {
  const p = mkParcel('solo');
  const result = formatMultiParcelContext([p], 'solo');
  assert.equal(result, formatParcelContext(p));
});

test('formatMultiParcelContext — 2 resolved parcels builds comparison string', () => {
  const a = createResolvedParcel(
    { shortAddress: '10 King St W' },
    { id: 'p1', zone_code: 'CR', lot_area_m2: 500 }
  );
  const b = createResolvedParcel(
    { shortAddress: '20 Queen St E' },
    { id: 'p2', zone_code: 'RA', lot_area_m2: 300 }
  );
  const result = formatMultiParcelContext([a, b], 'p1');
  assert.ok(result.includes('(PRIMARY)'));
  assert.ok(result.includes('(comparison)'));
  assert.ok(result.includes('10 King St W'));
  assert.ok(result.includes('20 Queen St E'));
  assert.ok(result.includes('Compare and contrast these parcels.'));
});

test('formatMultiParcelContext — primary tag on correct parcel', () => {
  const a = mkParcel('p1');
  const b = mkParcel('p2');
  const result = formatMultiParcelContext([a, b], 'p2');
  const lines = result.split('\n');
  assert.ok(lines[0].startsWith('(comparison)'));
  assert.ok(lines[1].startsWith('(PRIMARY)'));
});

test('formatMultiParcelContext — mixed resolved + unresolved', () => {
  const resolved = mkParcel('r1');
  const unresolved = createUnresolvedParcel({ shortAddress: '999 Lost Ave' });
  const result = formatMultiParcelContext([resolved, unresolved], 'r1');
  assert.ok(result.includes('(PRIMARY)'));
  assert.ok(result.includes('no parcel data available'));
  assert.ok(result.includes('999 Lost Ave'));
});
