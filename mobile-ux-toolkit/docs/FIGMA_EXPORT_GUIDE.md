# Figma Export Guide

A step-by-step guide for translating the HTML/CSS prototype into a Figma design file. This guide covers token mapping, component recreation, layout techniques, and best practices for maintaining consistency between the prototype and design files.

---

## Table of Contents

1. [Setup & Structure](#setup--structure)
2. [Design Token Migration](#design-token-migration)
3. [Typography Setup](#typography-setup)
4. [Color Styles](#color-styles)
5. [Component Reconstruction](#component-reconstruction)
6. [Layout Techniques](#layout-techniques)
7. [Prototype Interactions](#prototype-interactions)
8. [Asset Export](#asset-export)
9. [Handoff Preparation](#handoff-preparation)

---

## Setup & Structure

### File Structure

Create a Figma file with the following page structure:

```
NovaPay Design System
├── Cover
├── Design Tokens
│   ├── Colors
│   ├── Typography
│   ├── Spacing
│   ├── Shadows
│   └── Border Radius
├── Components
│   ├── Buttons
│   ├── Cards
│   ├── Inputs
│   ├── Navigation
│   ├── Lists
│   ├── Badges & Chips
│   ├── Modals & Sheets
│   └── Misc
├── Screens
│   ├── Onboarding
│   ├── Login
│   ├── Dashboard
│   ├── Transfer
│   ├── Payments
│   ├── History
│   ├── Cards
│   ├── Notifications
│   ├── Profile
│   └── Support
└── Flows
    ├── Onboarding Flow
    ├── Transfer Flow
    └── Bill Payment Flow
```

### Frame Setup

Create a base frame for mobile screens:

- **Width**: 375px (iPhone 14 reference)
- **Height**: Auto layout, min 812px
- **Background**: `#F9FAFB` (neutral-50)

### Grid System

Add layout grids to your base frame:

- **Columns**: 4 columns, 20px margin, 16px gutter
- **Rows**: 4px baseline grid

---

## Design Token Migration

### Step 1: Create Local Variables (Figma Variables)

Figma supports variables (previously "design tokens"). Create the following collections:

#### Color Variables

```
Collection: Colors

Primitives/Primary/50    → #eff6ff
Primitives/Primary/100   → #dbeafe
Primitives/Primary/200   → #bfdbfe
Primitives/Primary/300   → #93c5fd
Primitives/Primary/400   → #60a5fa
Primitives/Primary/500   → #3b82f6
Primitives/Primary/600   → #1a56db
Primitives/Primary/700   → #1346b0
Primitives/Primary/800   → #0f3a8a
Primitives/Primary/900   → #0c2d6b

Primitives/Neutral/0     → #ffffff
Primitives/Neutral/50    → #f9fafb
Primitives/Neutral/100   → #f3f4f6
Primitives/Neutral/200   → #e5e7eb
Primitives/Neutral/300   → #d1d5db
Primitives/Neutral/400   → #9ca3af
Primitives/Neutral/500   → #6b7280
Primitives/Neutral/600   → #4b5563
Primitives/Neutral/700   → #374151
Primitives/Neutral/800   → #1f2937
Primitives/Neutral/900   → #111827

Primitives/Success/50    → #ecfdf5
Primitives/Success/600   → #059669
Primitives/Danger/50     → #fef2f2
Primitives/Danger/600    → #dc2626
Primitives/Warning/50    → #fffbeb
Primitives/Warning/500   → #f59e0b

Semantic/Text/Primary     → Neutral/900
Semantic/Text/Secondary   → Neutral/500
Semantic/Text/Tertiary    → Neutral/400
Semantic/Text/OnPrimary   → Neutral/0
Semantic/BG/Page          → Neutral/50
Semantic/BG/Card          → Neutral/0
Semantic/BG/Primary       → Primary/600
Semantic/Border/Default   → Neutral/300
Semantic/Border/Focus     → Primary/500
```

#### Spacing Variables

```
Collection: Spacing

Space/1   → 4
Space/2   → 8
Space/3   → 12
Space/4   → 16
Space/5   → 20
Space/6   → 24
Space/8   → 32
Space/10  → 40
Space/12  → 48
```

#### Border Radius Variables

```
Collection: Radius

SM    → 6
MD    → 8
LG    → 12
XL    → 16
2XL   → 20
3XL   → 24
Full  → 9999
```

### Step 2: Create Effect Styles

Create shadow styles matching the CSS tokens:

| Style Name | X | Y | Blur | Spread | Color |
|-----------|---|---|------|--------|-------|
| Shadow/XS | 0 | 1 | 2 | 0 | #000 5% |
| Shadow/SM (layer 1) | 0 | 1 | 3 | 0 | #000 8% |
| Shadow/SM (layer 2) | 0 | 1 | 2 | 0 | #000 4% |
| Shadow/MD (layer 1) | 0 | 4 | 6 | 0 | #000 6% |
| Shadow/MD (layer 2) | 0 | 2 | 4 | 0 | #000 4% |
| Shadow/LG (layer 1) | 0 | 10 | 15 | 0 | #000 8% |
| Shadow/LG (layer 2) | 0 | 4 | 6 | 0 | #000 4% |

---

## Typography Setup

### Text Styles

Create these text styles in Figma:

| Style Name | Font | Size | Weight | Line Height | Letter Spacing |
|-----------|------|------|--------|-------------|----------------|
| Display | SF Pro Display | 32 | Bold (700) | 38 (120%) | -0.64 |
| H1 | SF Pro Display | 24 | Bold (700) | 29 (120%) | -0.48 |
| H2 | SF Pro Display | 20 | Semibold (600) | 28 (138%) | 0 |
| H3 | SF Pro Display | 18 | Semibold (600) | 25 (138%) | 0 |
| Body | SF Pro Text | 16 | Regular (400) | 24 (150%) | 0 |
| Body Medium | SF Pro Text | 16 | Medium (500) | 24 (150%) | 0 |
| Small | SF Pro Text | 14 | Regular (400) | 21 (150%) | 0 |
| Caption | SF Pro Text | 12 | Regular (400) | 18 (150%) | 0.3 |
| Overline | SF Pro Text | 12 | Semibold (600) | 18 (150%) | 0.6 |
| Mono | SF Mono | 14 | Regular (400) | 21 (150%) | 0 |

> **Note**: Use "Inter" as a free alternative if SF Pro is unavailable.

---

## Color Styles

### Creating Color Styles

While variables handle the values, also create color styles for fills and strokes:

```
Fill/Primary        → Primary/600
Fill/Primary Hover  → Primary/700
Fill/Primary Light  → Primary/50
Fill/Success        → Success/600
Fill/Danger         → Danger/600
Fill/Warning        → Warning/500
Fill/Surface        → Neutral/0
Fill/Background     → Neutral/50

Stroke/Default      → Neutral/300
Stroke/Focus        → Primary/500
Stroke/Error        → Danger/500
```

---

## Component Reconstruction

### Buttons

Build button components with the following structure:

```
Button / Primary / Default
├── Auto Layout (horizontal, center, padding: 12 16)
│   ├── [Icon] (optional, 20x20)
│   └── Label (Body Medium, white)
├── Fill: Primary/600
├── Radius: 12 (LG)
├── Min Width: 48
├── Min Height: 48
│
├── Variants:
│   ├── State: Default, Hover, Pressed, Disabled, Loading
│   ├── Style: Primary, Secondary, Outline, Ghost, Danger
│   ├── Size: SM (36h), MD (48h), LG (56h)
│   └── Icon: None, Leading, Trailing, Icon Only
```

### Cards

```
Card / Default
├── Auto Layout (vertical, padding: 20)
│   ├── [Content slot]
├── Fill: Neutral/0
├── Radius: 16 (XL)
├── Shadow: SM
│
├── Variants:
│   ├── Elevation: Flat, Default, Elevated
│   └── Interactive: Yes, No
```

### List Items

```
List Item
├── Auto Layout (horizontal, center, padding: 16)
│   ├── Icon Container (44x44, radius: 12)
│   │   └── Icon (20x20)
│   ├── Content (fill, vertical)
│   │   ├── Title (Body Medium)
│   │   └── Subtitle (Small, Secondary)
│   └── Trailing (right-aligned, vertical)
│       ├── Amount (Body Medium)
│       └── Meta (Caption, Tertiary)
│
├── Border bottom: 1px Neutral/100
```

### Bottom Navigation

```
Bottom Nav
├── Auto Layout (horizontal, space-around)
│   ├── Nav Item x5
│   │   ├── Icon (24x24)
│   │   └── Label (10px, Medium)
├── Height: 64
├── Border top: 1px Neutral/200
├── Shadow: 0 -2 10 rgba(0,0,0,0.05)
│
├── Nav Item Variants:
│   └── State: Default, Active
```

---

## Layout Techniques

### Auto Layout Mapping

Map CSS flexbox/grid properties to Figma Auto Layout:

| CSS Property | Figma Equivalent |
|-------------|-----------------|
| `display: flex` | Auto Layout |
| `flex-direction: column` | Vertical Auto Layout |
| `flex-direction: row` | Horizontal Auto Layout |
| `gap: 16px` | Item spacing: 16 |
| `padding: 20px` | Padding: 20 |
| `justify-content: space-between` | Space between |
| `align-items: center` | Align center |
| `flex: 1` | Fill container |
| `width: 100%` | Fill container |

### Responsive Behavior

Set fill/hug properties to match CSS behavior:

- **Screen frame**: Fixed width (375px)
- **Cards**: Fill container horizontally, hug vertically
- **Buttons (full-width)**: Fill container
- **List items**: Fill container horizontally
- **Icons**: Fixed size
- **Text**: Fill container with text wrapping

---

## Prototype Interactions

### Screen Transitions

Set up prototype connections in Figma:

| From | To | Trigger | Animation |
|------|----|---------|-----------|
| Onboarding "Next" | Next slide | On Tap | Smart Animate, 300ms, Ease Out |
| Onboarding "Get Started" | Login | On Tap | Slide Left, 400ms |
| Login PIN complete | Dashboard | After delay 800ms | Slide Left, 300ms |
| Dashboard "Transfer" | Transfer | On Tap | Slide Left, 300ms |
| Any back button | Previous screen | On Tap | Slide Right, 300ms |
| Bottom nav item | Target screen | On Tap | Instant |

### Bottom Sheet

| Trigger | Action | Animation |
|---------|--------|-----------|
| Tap trigger button | Open overlay + sheet | Overlay: Dissolve 250ms; Sheet: Slide Up 400ms |
| Tap overlay | Close sheet | Reverse of open |
| Tap close button | Close sheet | Reverse of open |

### Toast Notifications

Use Figma's "After delay" trigger to auto-dismiss:

| Trigger | Action | Animation |
|---------|--------|-----------|
| Button tap | Show toast overlay | Slide Down, 250ms |
| After 3000ms delay | Dismiss toast | Slide Up, 200ms |

---

## Asset Export

### Icon Export Settings

- **Format**: SVG (for development), PNG @2x (for preview)
- **Size**: 24x24 base size
- **Stroke**: 2px, `currentColor`
- **Naming**: `icon-{name}.svg` (e.g., `icon-transfer.svg`)

### Screen Export for Documentation

- **Format**: PNG @2x
- **Frame**: Include device frame (optional)
- **Background**: Include page background
- **Naming**: `screen-{name}.png` (e.g., `screen-dashboard.png`)

---

## Handoff Preparation

### Inspection-Ready Setup

1. Name all layers descriptively (no "Frame 42" or "Group 17")
2. Use Auto Layout on all components for proper spacing inspection
3. Apply design tokens via variables so developers see token names, not raw values
4. Add component descriptions explaining usage guidelines
5. Mark ready-for-dev components with a green status badge

### Developer Notes

Add annotations for behaviors that are not visually apparent:

- "PIN auto-advances to next field on input"
- "Balance text truncates with ellipsis if account name is too long"
- "Bottom sheet opens on this button tap"
- "This filter chip supports multi-select"
- "Transaction list groups by date with sticky headers"

### Spec Sheet

Create a spec sheet page with:

- All spacing values used on each screen
- Animation timing and easing curves
- Touch target boundaries overlaid on interactive elements
- Color contrast ratios for all text/background combinations

---

## Figma Plugins That Help

| Plugin | Purpose |
|--------|---------|
| **Tokens Studio** | Sync CSS variables to Figma variables |
| **Iconify** | Access Feather Icons directly in Figma |
| **A11y - Color Contrast Checker** | Verify contrast ratios |
| **Autoflow** | Visualize user flows between frames |
| **Content Reel** | Populate realistic data in prototypes |

---

## Quality Checklist

Before sharing the Figma file:

- [ ] All screens match the HTML prototype pixel-for-pixel
- [ ] All text uses defined text styles (no local overrides)
- [ ] All colors use variables or color styles
- [ ] All components are properly named and organized
- [ ] Prototype connections cover all primary flows
- [ ] Layer naming is clean and descriptive
- [ ] Components have clear variant naming
- [ ] Spacing uses defined spacing variables
- [ ] File is organized into logical pages
- [ ] Cover page shows file name, version, and last update date

---

*This guide assumes Figma desktop or web app. All features are available on the free plan except some variable and library features which require a Professional plan.*
