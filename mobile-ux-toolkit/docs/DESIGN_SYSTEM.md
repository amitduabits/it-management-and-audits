# Design System Specification

A comprehensive design system for mobile banking and financial services applications. This document defines all design tokens, component specifications, and usage guidelines for building consistent, accessible, and professional mobile experiences.

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Color System](#color-system)
3. [Typography](#typography)
4. [Spacing & Layout](#spacing--layout)
5. [Elevation & Shadows](#elevation--shadows)
6. [Border Radius](#border-radius)
7. [Iconography](#iconography)
8. [Motion & Animation](#motion--animation)
9. [Component Tokens](#component-tokens)
10. [Responsive Breakpoints](#responsive-breakpoints)

---

## Design Principles

### 1. Trust First
Every visual decision should reinforce trust and security. Use stable, professional colors. Avoid flashy animations or aggressive marketing patterns that undermine user confidence.

### 2. Clarity Over Decoration
Financial data must be immediately readable. Prioritize clear typography, sufficient contrast, and logical information hierarchy over decorative elements.

### 3. Accessible by Default
Every component must meet WCAG 2.1 AA standards. Minimum contrast ratios, touch target sizes, and screen reader support are non-negotiable requirements, not enhancements.

### 4. Consistent & Predictable
Users should never have to relearn interaction patterns. Same actions produce same results. Visual patterns remain consistent across all screens.

### 5. Mobile-Native Feel
The design system is built for touch interfaces. Sizing, spacing, and interaction patterns are optimized for thumb-zone ergonomics on mobile devices.

---

## Color System

### Primary Scale (Trust Blue)

The primary color communicates trust, stability, and professionalism -- core attributes for financial services.

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `--color-primary-50` | `#eff6ff` | `239, 246, 255` | Subtle backgrounds, highlights |
| `--color-primary-100` | `#dbeafe` | `219, 234, 254` | Hover backgrounds, badges |
| `--color-primary-200` | `#bfdbfe` | `191, 219, 254` | Borders, dividers |
| `--color-primary-300` | `#93c5fd` | `147, 197, 253` | Focus rings (inner) |
| `--color-primary-400` | `#60a5fa` | `96, 165, 250` | Icons (decorative) |
| `--color-primary-500` | `#3b82f6` | `59, 130, 246` | Focus rings, links |
| `--color-primary-600` | `#1a56db` | `26, 86, 219` | Primary buttons, CTAs |
| `--color-primary-700` | `#1346b0` | `19, 70, 176` | Hover states, headers |
| `--color-primary-800` | `#0f3a8a` | `15, 58, 138` | Active/pressed states |
| `--color-primary-900` | `#0c2d6b` | `12, 45, 107` | Dark accents |

### Neutral Scale

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-neutral-0` | `#ffffff` | Card backgrounds, inputs |
| `--color-neutral-50` | `#f9fafb` | Page backgrounds |
| `--color-neutral-100` | `#f3f4f6` | Dividers, secondary backgrounds |
| `--color-neutral-200` | `#e5e7eb` | Borders, disabled backgrounds |
| `--color-neutral-300` | `#d1d5db` | Input borders, inactive elements |
| `--color-neutral-400` | `#9ca3af` | Placeholder text, tertiary text |
| `--color-neutral-500` | `#6b7280` | Secondary text, captions |
| `--color-neutral-600` | `#4b5563` | Body text (secondary) |
| `--color-neutral-700` | `#374151` | Strong secondary text |
| `--color-neutral-800` | `#1f2937` | Headings (secondary) |
| `--color-neutral-900` | `#111827` | Primary text, headings |

### Semantic Colors

#### Success (Green)
| Token | Hex | Usage |
|-------|-----|-------|
| `--color-success-50` | `#ecfdf5` | Success backgrounds |
| `--color-success-100` | `#d1fae5` | Success badges |
| `--color-success-500` | `#10b981` | Success icons |
| `--color-success-600` | `#059669` | Positive amounts, confirmations |
| `--color-success-700` | `#047857` | Success text on light backgrounds |

#### Danger (Red)
| Token | Hex | Usage |
|-------|-----|-------|
| `--color-danger-50` | `#fef2f2` | Error backgrounds |
| `--color-danger-100` | `#fee2e2` | Error badges |
| `--color-danger-500` | `#ef4444` | Error icons |
| `--color-danger-600` | `#dc2626` | Error text, negative amounts |
| `--color-danger-700` | `#b91c1c` | Danger text on light backgrounds |

#### Warning (Amber)
| Token | Hex | Usage |
|-------|-----|-------|
| `--color-warning-50` | `#fffbeb` | Warning backgrounds |
| `--color-warning-100` | `#fef3c7` | Warning badges |
| `--color-warning-500` | `#f59e0b` | Warning icons, pending states |
| `--color-warning-600` | `#d97706` | Warning text |
| `--color-warning-700` | `#b45309` | Warning text on light backgrounds |

### Color Usage Guidelines

- **Never** use color as the sole indicator of state. Always pair with icons, text, or patterns.
- **Positive monetary values** use `success-600` green.
- **Negative monetary values** use `neutral-900` (not red), unless the context is explicitly a loss or error.
- **Interactive elements** use `primary-600` as the base, with `primary-700` for hover and `primary-800` for active.
- **Backgrounds** should alternate between `neutral-0` (cards) and `neutral-50` (page).

### Contrast Ratios

All text/background combinations meet the following minimums:

| Combination | Ratio | Standard |
|-------------|-------|----------|
| neutral-900 on neutral-0 | 17.4:1 | AAA |
| neutral-500 on neutral-0 | 5.4:1 | AA |
| primary-600 on neutral-0 | 5.8:1 | AA |
| neutral-0 on primary-600 | 5.8:1 | AA |
| success-600 on neutral-0 | 4.6:1 | AA |
| danger-600 on neutral-0 | 4.6:1 | AA |

---

## Typography

### Font Stack

```css
--font-family-primary: -apple-system, BlinkMacSystemFont, 'SF Pro Display',
  'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
--font-family-mono: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
```

System fonts ensure native rendering, fast load times, and visual consistency with the host operating system.

### Type Scale

| Level | Size | Weight | Line Height | Letter Spacing | Usage |
|-------|------|--------|-------------|----------------|-------|
| Display | 32px | 700 | 1.2 | -0.02em | Hero amounts, feature headlines |
| H1 | 24px | 700 | 1.2 | -0.02em | Screen titles |
| H2 | 20px | 600 | 1.375 | 0 | Section headers |
| H3 | 18px | 600 | 1.375 | 0 | Card titles, subheadings |
| Body | 16px | 400 | 1.5 | 0 | General content |
| Body Medium | 16px | 500 | 1.5 | 0 | Emphasized body text |
| Small | 14px | 400 | 1.5 | 0 | Supporting text, descriptions |
| Caption | 12px | 400 | 1.5 | 0.025em | Labels, metadata, timestamps |
| Overline | 12px | 600 | 1.5 | 0.05em | Section labels (uppercase) |

### Monetary Amount Formatting

- Currency symbol: Regular weight, 65% of amount font size, superscript alignment
- Whole dollars: Bold weight, full size
- Cents: Medium weight, 60% of amount font size, superscript alignment
- Always use locale-appropriate thousand separators
- Use monospace font for account numbers and card numbers

---

## Spacing & Layout

### Spacing Scale

Based on a 4px base unit:

| Token | Value | Common Usage |
|-------|-------|-------------|
| `--space-1` | 4px | Tight gaps between related elements |
| `--space-2` | 8px | Default gap in compact layouts |
| `--space-3` | 12px | Input padding, small component gaps |
| `--space-4` | 16px | Standard padding, section gaps |
| `--space-5` | 20px | Screen horizontal padding |
| `--space-6` | 24px | Section separation |
| `--space-8` | 32px | Large section breaks |
| `--space-10` | 40px | Hero section padding |
| `--space-12` | 48px | Empty state vertical padding |
| `--space-16` | 64px | Major page sections |
| `--space-20` | 80px | Full-page content centering |
| `--space-24` | 96px | Maximum spacing |

### Layout Constants

| Token | Value | Usage |
|-------|-------|-------|
| `--mobile-width` | 375px | Base mobile width (iPhone reference) |
| `--mobile-max-width` | 428px | Maximum prototype width |
| `--header-height` | 56px | App bar height |
| `--bottom-nav-height` | 64px | Bottom navigation height |

### Safe Areas

The design system supports iOS safe areas via `env(safe-area-inset-*)` for proper notch and home indicator handling.

---

## Elevation & Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-xs` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle separation |
| `--shadow-sm` | `0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)` | Cards, list groups |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.04)` | Elevated cards, dropdown |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.08), 0 4px 6px rgba(0,0,0,0.04)` | Modals, bank cards |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.1), 0 8px 10px rgba(0,0,0,0.04)` | Floating elements |
| `--shadow-2xl` | `0 25px 50px rgba(0,0,0,0.15)` | Overlays |

### Elevation Hierarchy

1. **Base level** (no shadow): Page background
2. **Level 1** (shadow-sm): Cards, list groups, inputs
3. **Level 2** (shadow-md): Hover states, dropdowns
4. **Level 3** (shadow-lg): Bank card visuals, FABs
5. **Level 4** (shadow-xl): Modals, bottom sheets
6. **Level 5** (shadow-2xl): Full-screen overlays

---

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 6px | Small elements, badges |
| `--radius-md` | 8px | Buttons (small), inputs |
| `--radius-lg` | 12px | Standard buttons, cards |
| `--radius-xl` | 16px | Card groups, containers |
| `--radius-2xl` | 20px | Hero cards, balance cards |
| `--radius-3xl` | 24px | Bottom sheets |
| `--radius-full` | 9999px | Avatars, pills, toggles |

---

## Iconography

### Icon Specifications

- **Style**: Outlined (stroke-based), 2px stroke weight
- **Grid**: 24x24px viewBox
- **Touch target**: Minimum 44x44px (with padding)
- **Color**: Inherits from parent via `currentColor`
- **Source**: Feather Icons or compatible SVG icon set

### Icon Sizes

| Context | Icon Size | Touch Target |
|---------|-----------|-------------|
| Bottom navigation | 24px | 60x48px (with padding) |
| List item leading | 20px | 44x44px (container) |
| Button inline | 18-20px | Button min-height 48px |
| Header actions | 20-24px | 40x40px button |
| Quick action grid | 24px | 52x52px (container) |

---

## Motion & Animation

### Duration Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--duration-fast` | 150ms | Hover states, toggles, ripples |
| `--duration-normal` | 250ms | Standard transitions, fade-in |
| `--duration-slow` | 400ms | Screen transitions, slide-in |
| `--duration-slower` | 600ms | Complex animations, bounce |

### Easing Functions

| Token | Value | Usage |
|-------|-------|-------|
| `--ease-default` | `cubic-bezier(0.4, 0, 0.2, 1)` | General purpose |
| `--ease-in` | `cubic-bezier(0.4, 0, 1, 1)` | Elements leaving the screen |
| `--ease-out` | `cubic-bezier(0, 0, 0.2, 1)` | Elements entering the screen |
| `--ease-spring` | `cubic-bezier(0.175, 0.885, 0.32, 1.275)` | Playful, bouncy entrances |

### Animation Guidelines

- Always respect `prefers-reduced-motion` -- disable all non-essential animation.
- Use stagger delays (50ms increments) for list items appearing sequentially.
- Screen transitions should feel like native mobile navigation (slide left/right).
- Loading states should use subtle pulse or shimmer animations, not spinners, when possible.
- Financial amounts should never animate their values -- display the final number immediately.

---

## Component Tokens

### Buttons

| Property | Primary | Secondary | Outline | Ghost |
|----------|---------|-----------|---------|-------|
| Background | primary-600 | primary-50 | transparent | transparent |
| Text | neutral-0 | primary-600 | primary-600 | neutral-600 |
| Border | none | none | primary-600 | none |
| Hover bg | primary-700 | primary-100 | primary-50 | neutral-100 |
| Min height | 48px | 48px | 48px | 48px |
| Border radius | radius-lg | radius-lg | radius-lg | radius-lg |

### Form Inputs

| Property | Value |
|----------|-------|
| Height | 48px minimum |
| Padding | 12px 16px |
| Border | 1.5px solid neutral-300 |
| Border (focus) | 1.5px solid primary-500 |
| Focus ring | 0 0 0 3px primary-100 |
| Border radius | radius-lg |
| Placeholder color | neutral-400 |

### Cards

| Property | Value |
|----------|-------|
| Background | neutral-0 |
| Border radius | radius-xl |
| Padding | 20px |
| Shadow | shadow-sm |
| Hover shadow | shadow-md (interactive cards) |

---

## Responsive Breakpoints

While this toolkit is mobile-first, it supports display in browser device emulation:

| Breakpoint | Width | Usage |
|------------|-------|-------|
| Mobile S | 320px | Minimum supported width |
| Mobile M | 375px | Base design width (iPhone) |
| Mobile L | 428px | Maximum prototype width |
| Tablet | 768px+ | Side-by-side preview mode |

All prototype screens are constrained to `max-width: 428px` with `margin: 0 auto` for centered display on larger viewports.

---

## Z-Index Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--z-base` | 1 | Elevated content above siblings |
| `--z-dropdown` | 10 | Dropdown menus |
| `--z-sticky` | 20 | Sticky headers, bottom nav |
| `--z-overlay` | 30 | Background overlays |
| `--z-modal` | 40 | Modals, bottom sheets |
| `--z-toast` | 50 | Toast notifications |
| `--z-tooltip` | 60 | Tooltips, popovers |

---

*This design system is intended for prototyping. Production implementations should extend these tokens to match your platform-specific design framework (SwiftUI, Jetpack Compose, React Native, Flutter).*
