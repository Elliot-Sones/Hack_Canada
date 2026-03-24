# CoCivil UI Overhaul — Linear DNA Transplant

**Date:** 2026-03-23
**Status:** Approved
**Inspiration:** Linear (craft, density, keyboard-first, purposeful motion)

---

## 1. Component Library

15 reusable primitives built on existing design tokens (`variables.css`). All components use CSS variables for theming, no external component library.

### Components

| Component | Variants | Key Behavior |
|-----------|----------|-------------|
| Button | ghost / solid / outline; sm / md / lg | Loading spinner state, kbd hint slot, gold accent for primary |
| Input | default / error / disabled | Gold border on focus, icon prefix/suffix slots |
| Badge | status colors (green/amber/red/blue/purple/gray) | Dot indicator variant, pill shape |
| Tooltip | top / bottom / left / right | 300ms hover delay, fade in, dark bg |
| Dropdown | single / multi-select | Arrow key navigation, search filter, grouped items, 120ms scale animation |
| Modal | default / sheet (slide-up) | Backdrop blur, Escape to close, focus trap |
| CommandPalette | — | Cmd+K trigger, fuzzy search, grouped actions, recent items |
| Toast | info / success / warning / error | Bottom-left stack, 4s auto-dismiss, undo slot, slide-in |
| Skeleton | line / circle / rect / card | Shimmer pulse animation, matches real content layout |
| Tabs | underline / pill | Animated underline slides between tabs (spring physics) |
| Kbd | — | Keyboard shortcut display chip (e.g., ⌘K) |
| Progress | bar / stepper | Thin horizontal bar with smooth fill, or multi-step pipeline |
| Avatar | image / initials | Status dot overlay, size sm/md/lg |
| Card | default / interactive | Hover: subtle lift + border highlight |
| ContextMenu | — | Right-click trigger, kbd hints per item, nested submenus |

### Design Token Usage

All components pull from:
- `--accent`, `--accent-light`, `--accent-dim` for interactive states
- `--bg-primary/secondary/tertiary` for surfaces
- `--text-primary/secondary/muted` for text hierarchy
- `--radius-sm/md/lg` for border radius
- `--transition` (0.25s cubic-bezier) for all transitions
- `--shadow-sm/md/lg` for elevation
- `--blur` for glassmorphism

---

## 2. Navigation & Layout

### Top Bar
- **Left:** CoCivil logo (clickable → dashboard home)
- **Center:** Command palette trigger input — shows "Search or jump to... ⌘K"
- **Right:** User avatar with dropdown (settings, sign out)
- **Height:** 48px, border-bottom 1px `--border`

### Sidebar (Left, 220px default)
220px default (up from 160px — more room for parcel addresses). Collapsible via `⌘B`. When collapsed: 52px width (unchanged), icons only, labels fade out. Update `--sidebar-width: 220px` in variables.css.

**Structure:**
```
[Workspace label]

⊕ Parcels          (collapsible group)
  ├─ Active         (filtered view)
  ├─ Analyzed       (filtered view)
  └─ Archived       (filtered view)

⊕ Projects         (collapsible group)
  ├─ In Progress
  └─ Complete

─────────

Views
  ├─ Map
  ├─ Table
  └─ 3D

─────────

Shortcuts (footer)
  ⌘K  Search
  ⌘/  Chat
  ⌘B  Sidebar
```

- Each parcel row: status icon (colored) + address truncated + badge count
- Hover: background tint `--accent-bg`, 100ms
- Active item: left border 2px `--accent`, background `--accent-bg`
- Groups expand/collapse with 200ms height animation

### Detail Panel (Right, 380px default)
Contextual panel with tabs at top:

**Tabs:** Policy | Zoning | Infrastructure | Chat | Documents

- Animated underline indicator slides between tabs
- Panel resizable via drag handle (min 300px, max 500px)
- Collapsible via click on edge or `⌘]`
- State persisted to localStorage

### Main Content Area
Full remaining space between sidebar and detail panel. Houses:
- MapView (default)
- 3D ModelViewer (switchable via Views nav)
- Table view (new — parcel list with sortable columns)

### Chat Relocation
Chat moves from bottom panel → detail panel tab. Benefits:
- Full vertical space for map/3D
- Chat gets full panel height instead of constrained 280px
- Consistent with Linear's detail panel pattern

---

## 3. Status & Workflow Pipeline

### Parcel Status System

| Status | Icon | Color | Meaning |
|--------|------|-------|---------|
| Pending | ○ | `--text-muted` (gray) | Added, no analysis |
| Searching | ◐ | `#60a5fa` (blue) | Geocoding/ArcGIS lookup |
| Analyzing | ◑ | `--warning` (amber) | Zoning + policy running |
| Infrastructure | ◕ | `#a78bfa` (purple) | Servicing checks |
| Complete | ● | `--success` (green) | Report ready |
| Blocked | ⊘ | `--error` (red) | Failed/missing data |

### Pipeline Stepper
Horizontal progress bar shown in detail panel header when a parcel is selected:

```
[Search] ——→ [Analyze] ——→ [Infrastructure] ——→ [Complete]
   ●            ◐              ○                   ○
```

- Completed steps: filled dot + solid connector
- Active step: pulsing dot + label bold
- Pending steps: hollow dot + dashed connector
- Animated transitions between states (300ms)

### Batch Operations
- Checkbox selection on parcel rows (Shift+click for range)
- Floating action bar appears at bottom: "3 parcels selected — Run Analysis | Generate Report | Archive"
- Bar slides up with 150ms ease-out

---

## 4. Micro-interactions & Motion

### Timing Standards
- **Instant feedback:** 80ms (hover tints, button press)
- **Quick transitions:** 120-150ms (dropdowns, tooltips, panel slides)
- **Standard transitions:** 200-250ms (tab switches, sidebar collapse, skeleton crossfade)
- **Deliberate animations:** 300ms (status morphs, page transitions, command palette)

### Specific Animations
- **Panel transitions:** 150ms ease-out translateX
- **Skeleton → content:** 200ms crossfade, skeleton shimmer stops mid-pulse
- **Toast enter:** slideUp from bottom-left, 150ms
- **Toast exit:** fadeOut 200ms on dismiss or after 4s
- **Sidebar collapse:** width 200ms, labels opacity 0 at halfway point
- **Tab underline:** spring physics (tension 300, friction 20)
- **Dropdown open:** scale 0.95→1.0 + opacity, 120ms
- **Command palette:** backdrop blur 200ms, modal scale 0.98→1.0
- **Parcel row hover:** bg-color 80ms
- **Context menu:** opacity + scale, 80ms
- **Status icon change:** morph 300ms + brief color pulse (scale 1.0→1.1→1.0)
- **Empty state enter:** fadeInUp (opacity + translateY 8px), 250ms

### Easing
- Standard: `cubic-bezier(0.4, 0, 0.2, 1)` (existing)
- Enter: `cubic-bezier(0, 0, 0.2, 1)`
- Exit: `cubic-bezier(0.4, 0, 1, 1)`
- Spring (tabs): CSS `transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)`

---

## 5. Empty States

Each view gets a purposeful empty state:

| View | Message | CTA |
|------|---------|-----|
| No parcels | "Search for a parcel address or click the map to begin" | Search input + "Or browse the map" link |
| No projects | "Create your first project to organize parcels" | "New Project" button |
| No chat history | "Ask anything about zoning, policy, or site feasibility" | 3 suggested prompt chips |
| Analysis pending | Pipeline stepper (all hollow) | "Run Analysis" button |
| No documents | "Documents will appear here after analysis completes" | Status link to pipeline |
| No infrastructure data | "Infrastructure data loads during analysis" | — |
| Search no results | "No parcels found for '[query]'" | "Try a different address" hint |

All empty states: centered vertically, muted text color, subtle icon above text (Lucide), fadeInUp entrance.

---

## 6. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `⌘K` | Open command palette |
| `⌘/` | Focus chat input |
| `⌘B` | Toggle sidebar |
| `⌘]` | Toggle detail panel |
| `⌘Enter` | Run analysis on selected parcel |
| `Escape` | Close modal/palette/dropdown |
| `↑↓` | Navigate lists (parcels, dropdown items, command results) |
| `Enter` | Select focused item |
| `⌘1-5` | Switch detail panel tabs |

---

## 7. Typography & Spacing Tightening

### Grid System
4px base grid. Keep existing token names (`--space-xs` through `--space-2xl`) — just tighten values:
- `--space-xs`: 4px (unchanged)
- `--space-sm`: 8px (unchanged)
- `--space-md`: 12px (unchanged)
- `--space-lg`: 16px (unchanged)
- `--space-xl`: 24px (unchanged)
- `--space-2xl`: 32px (unchanged)

### Typography Scale (tightened, keeping rem units)
- `--font-xs`: 0.6875rem (11px) / 1rem line-height (labels, kbd)
- `--font-sm`: 0.75rem (12px) / 1rem (secondary text, badges)
- `--font-base`: 0.8125rem (13px) / 1.25rem (body text, inputs)
- `--font-md`: 0.875rem (14px) / 1.25rem (nav items, emphasis)
- `--font-lg`: 1rem (16px) / 1.5rem (section headers)
- `--font-xl`: 1.25rem (20px) / 1.75rem (page titles)

### Font Weight
- Regular (400): body text
- Medium (500): nav items, labels, badges
- Semibold (600): headings, active states

---

## 8. Files to Create/Modify

### New Files
```
frontend/src/app/components/ui/
  Button.jsx
  Input.jsx
  Badge.jsx
  Tooltip.jsx
  Dropdown.jsx
  Modal.jsx
  CommandPalette.jsx
  Toast.jsx
  Skeleton.jsx
  Tabs.jsx
  Kbd.jsx
  Progress.jsx
  Avatar.jsx
  Card.jsx
  ContextMenu.jsx
  EmptyState.jsx
  ToastProvider.jsx

frontend/src/app/styles/
  spacing.css          (4px grid tokens)
```

### Modified Files
```
frontend/src/app/components/
  DashboardView.jsx    (new layout: top bar + sidebar + main + detail)
  Sidebar.jsx          (Linear-style workspace nav)
  PolicyPanel.jsx      (becomes detail panel with tabs)
  ChatPanel.jsx        (moves into detail panel tab)
  MapView.jsx          (full height, remove bottom chat space)

frontend/src/app/styles/
  variables.css        (add spacing tokens, tighten typography)
  animations.css       (add new keyframes)
  globals.css          (import spacing.css)
```

---

## 9. Responsive Strategy

Mobile (< 900px) is already handled in `variables.css` with sidebar collapse and full-width panels. For this phase:
- **< 900px:** Sidebar collapses to icon-only, detail panel becomes a slide-over sheet (full width), main content takes full width
- **900–1200px:** Sidebar at 220px, detail panel at 340px (narrower)
- **> 1200px:** Full three-panel layout as designed
- Breakpoints stay in `variables.css` media queries (existing pattern)

## 10. Accessibility Baseline

- All interactive components get appropriate ARIA roles
- Toasts announced via `aria-live="polite"` region
- `prefers-reduced-motion`: disable all animations, use instant transitions
- Focus rings: 2px `--accent` outline with 2px offset on all interactive elements
- Spring physics note: CSS cubic-bezier approximation only (no framer-motion dependency)
- Fuzzy search in command palette: use `fuse.js` (lightweight, well-maintained)

## 11. Component Organization

New primitives go in `frontend/src/app/components/ui/`. Existing components (`Sidebar.jsx`, `ChatPanel.jsx`, etc.) stay in `frontend/src/app/components/`. Only new reusable primitives live in `ui/`.

## 12. What's NOT Changing

- Color palette (warm dark + gold works perfectly)
- 3D viewers (ModelViewer, InfrastructureViewer) — already impressive
- MapLibre integration — stays as main content view
- Auth flow — untouched
- Landing page — separate concern
- Backend API — no changes
- Better Auth + JWT exchange — untouched
