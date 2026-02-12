# Screenshots Guide

This directory is reserved for prototype screenshots used in documentation and presentations.

---

## How to Capture Screenshots

### Method 1: Chrome DevTools Device Emulation

1. Open any prototype screen in Chrome (e.g., `prototype/screens/dashboard.html`)
2. Open DevTools: `Ctrl+Shift+I` (Windows) or `Cmd+Option+I` (Mac)
3. Toggle device emulation: `Ctrl+Shift+M` or click the device icon
4. Select a device: **iPhone 14** (390x844) or **iPhone 14 Pro** (393x852)
5. Capture screenshot: Open DevTools menu (three dots) > **Capture screenshot**
6. For full-page: **Capture full size screenshot**

### Method 2: Firefox Responsive Design Mode

1. Open the prototype screen in Firefox
2. Press `Ctrl+Shift+M` to open Responsive Design Mode
3. Set width to 375px
4. Click the camera icon to capture a screenshot

### Method 3: Browser Extension

Use the "GoFullPage" Chrome extension for consistent full-page captures.

---

## Recommended Screenshot Set

Capture these screenshots for a complete documentation package:

| # | Screen | File Name | Notes |
|---|--------|-----------|-------|
| 1 | Index (Home) | `01-index.png` | Shows the full screen grid |
| 2 | Onboarding Slide 1 | `02-onboarding-1.png` | "Banking Made Simple" |
| 3 | Onboarding Slide 2 | `03-onboarding-2.png` | "Bank-Grade Security" |
| 4 | Login | `04-login.png` | PIN entry with biometric option |
| 5 | Dashboard | `05-dashboard.png` | Full dashboard with balance |
| 6 | Dashboard (scrolled) | `06-dashboard-scrolled.png` | Quick actions and transactions |
| 7 | Transfer | `07-transfer.png` | Amount entry with keypad |
| 8 | Payments | `08-payments.png` | Bill list with urgency badges |
| 9 | Transaction History | `09-history.png` | Search, filters, grouped list |
| 10 | Cards | `10-cards.png` | Card carousel and actions |
| 11 | Notifications | `11-notifications.png` | Unread notifications |
| 12 | Profile | `12-profile.png` | Settings with toggles |
| 13 | Support | `13-support.png` | FAQ and contact options |

---

## Screenshot Specifications

| Property | Value |
|----------|-------|
| **Device width** | 375px or 390px |
| **Pixel ratio** | 2x (@2x retina) |
| **Format** | PNG (lossless) |
| **Background** | Include device background |
| **Status bar** | Include the simulated status bar |

---

## Usage

Screenshots are referenced in:

- `README.md` — Overview and quick preview
- `docs/DESIGN_SYSTEM.md` — Component visual references
- Presentation decks
- Stakeholder reviews
- Design handoff documentation

---

## Naming Convention

```
{number}-{screen-name}.png
{number}-{screen-name}-{variant}.png
```

Examples:
- `05-dashboard.png`
- `05-dashboard-scrolled.png`
- `07-transfer-amount-entered.png`
- `10-cards-frozen.png`

---

*Screenshots in this directory are excluded from version control by default (see `.gitignore`). Add them locally after capture or store them in your team's asset management system.*
