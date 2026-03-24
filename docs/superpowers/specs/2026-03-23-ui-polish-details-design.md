# CoCivil UI Polish — Professional Detail Pass

**Date:** 2026-03-23
**Status:** Approved
**Scope:** CSS-level and small component polish on the original dashboard layout. No layout restructuring.

---

## 1. Transitions on All Interactive Elements

Add `transition: all 150ms ease-out` to:
- Sidebar nav items (hover, active)
- Right panel open/close (200ms slide)
- Chat panel expand/collapse (200ms slide)
- Buttons (hover opacity/color)
- Search bar (focus border)
- Panel reopen tab (hover)

Panel slide uses `cubic-bezier(0.16, 1, 0.3, 1)` for entrance, `ease-out` for exit.

## 2. Custom Scrollbars

Replace default browser scrollbar in all scrollable containers (right panel, chat messages, sidebar history):

```css
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
```

Scrollbar only visible on hover over the container (use `:hover` on parent to toggle thumb opacity).

## 3. Focus Rings on Inputs

Search bar and chat input get a visible focus state:
```css
:focus-visible {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(200, 165, 92, 0.1);
  outline: none;
}
```

Use `:focus-visible` not `:focus` so mouse clicks don't trigger ugly outlines.

## 4. Sidebar Active State

Active nav item gets:
- `background: var(--accent-bg)` (rgba(200, 165, 92, 0.12))
- `border-left: 2px solid var(--accent)`
- `color: var(--text-primary)` (full opacity, not muted)
- `border-radius: 0 var(--radius-sm) var(--radius-sm) 0`
- Font weight does NOT change (prevents layout shift)

Hover state (non-active items):
- `background: rgba(255, 255, 255, 0.04)`

## 5. Skeleton Loaders

Replace "Loading..." text in PolicyPanel with shimmer skeleton placeholders:
- Use the existing `Skeleton` and `SkeletonGroup` components from `components/ui/Skeleton.jsx`
- Show 4-5 skeleton lines matching the layout shape of the content being loaded
- Shimmer animation: `background: linear-gradient(90deg, var(--bg-tertiary) 25%, var(--bg-secondary) 50%, var(--bg-tertiary) 75%)`

## 6. Sidebar Hover States

All nav items get subtle hover feedback:
- `background: rgba(255, 255, 255, 0.04)` on hover
- `border-radius: var(--radius-sm)`
- Transition: 150ms ease-out
- The change should be barely perceptible

## 7. Collapse Button Fix

The "Collapse" text at sidebar bottom is clipped by the icon. Fix:
- Ensure the icon and text have proper flex layout with gap
- Text should truncate with ellipsis if sidebar is too narrow
- Or simply show the chevron icon only, with a tooltip "Collapse sidebar"

## 8. Chat Input Styling

Chat input field needs:
- Background slightly lighter than surface: `rgba(255, 255, 255, 0.04)`
- 1px border at `rgba(255, 255, 255, 0.08)`
- On focus: border transitions to `rgba(255, 255, 255, 0.15)` + gold glow ring
- Placeholder text at lower opacity than current
- Send button hover: slight scale or brightness increase

## 9. Text Truncation

Add to all containers that could overflow:
```css
overflow: hidden;
text-overflow: ellipsis;
white-space: nowrap;
```

Applies to: sidebar nav labels, search history items, parcel addresses in SelectionChips, panel header text, chat message sender labels.

## 10. Panel Slide Animation

Right panel (PolicyPanel) open/close animates:
- Open: slide in from right, 200ms `cubic-bezier(0.16, 1, 0.3, 1)`
- Close: slide out to right, 150ms ease-out
- Use `transform: translateX()` for GPU-accelerated animation

Chat panel expand/collapse:
- Already has some animation but should use consistent timing (200ms)

## Files to Modify

```
frontend/src/app/styles/variables.css     — add scrollbar styles, transition tokens
frontend/src/app/styles/sidebar.css       — active state, hover states, collapse fix
frontend/src/app/styles/panel.css         — slide animation, scrollbar
frontend/src/app/styles/chat.css          — input styling, focus ring, scrollbar
frontend/src/app/styles/map-search.css    — search bar focus ring
frontend/src/app/components/PolicyPanel.jsx — skeleton loaders for loading states
frontend/src/app/components/Sidebar.jsx    — collapse button fix
```

## What's NOT Changing

- Layout structure (sidebar + map + right panel + bottom chat)
- Color palette
- Typography scale
- Component hierarchy
- Any backend/API behavior
