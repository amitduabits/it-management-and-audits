# WCAG 2.1 AA Accessibility Checklist

A comprehensive accessibility checklist for mobile banking applications, mapped to WCAG 2.1 Level AA success criteria. Each item includes the WCAG reference, testing method, and implementation notes specific to financial app UX.

---

## Perceivable

### 1.1 Text Alternatives

- [ ] **1.1.1 Non-text Content (A)** — All images, icons, and visual elements have appropriate text alternatives
  - All SVG icons in buttons have `aria-label` on the button element
  - Decorative icons use `aria-hidden="true"`
  - Card chip visuals and background decorations are excluded from the accessibility tree
  - Bank card images provide meaningful alt text ("Visa Platinum card ending in 7832")
  - Avatar initials are announced with the full name via `aria-label`

### 1.2 Time-based Media

- [ ] **1.2.1-1.2.5** — Not applicable (no audio/video content in this prototype)

### 1.3 Adaptable

- [ ] **1.3.1 Info and Relationships (A)** — Semantic HTML conveys structure
  - Headings use proper `h1`-`h6` hierarchy (one `h1` per screen)
  - Lists use `ul`/`ol` with `li` elements
  - Form inputs are associated with `label` elements
  - Tables (if used) have `th` headers with `scope` attributes
  - Navigation landmarks use `nav` with `aria-label`
  - Main content uses `main` landmark
  - Related form fields are grouped with `fieldset` and `legend`

- [ ] **1.3.2 Meaningful Sequence (A)** — Reading order matches visual order
  - DOM order follows the visual top-to-bottom, left-to-right layout
  - CSS does not reorder content in a way that changes meaning
  - Bottom navigation appears last in the DOM

- [ ] **1.3.3 Sensory Characteristics (A)** — Instructions don't rely solely on shape, size, or position
  - Error messages reference the field name, not just "the field above"
  - Navigation instructions use labels, not just "tap the blue button"

- [ ] **1.3.4 Orientation (AA)** — Content works in both portrait and landscape
  - No CSS locks orientation to portrait-only
  - Content is accessible (if differently laid out) in landscape

- [ ] **1.3.5 Identify Input Purpose (AA)** — Input purposes are programmatically determinable
  - Login PIN input has `autocomplete="one-time-code"` where applicable
  - Email fields use `autocomplete="email"`
  - Name fields use `autocomplete="name"`

### 1.4 Distinguishable

- [ ] **1.4.1 Use of Color (A)** — Color is not the sole indicator of meaning
  - Transaction amounts use +/- prefix in addition to green/dark colors
  - Error states show error icons and text in addition to red borders
  - Active navigation items have a visual indicator (top bar) beyond color change
  - Status badges include text labels ("Active", "Pending", "Frozen")

- [ ] **1.4.2 Audio Control (A)** — Not applicable (no audio in prototype)

- [ ] **1.4.3 Contrast (Minimum) (AA)** — Text meets 4.5:1 ratio (3:1 for large text)
  - Primary text (neutral-900 on neutral-0): 17.4:1
  - Secondary text (neutral-500 on neutral-0): 5.4:1
  - Primary buttons (neutral-0 on primary-600): 5.8:1
  - Success amounts (success-600 on neutral-0): 4.6:1
  - Caption text (neutral-400 on neutral-0): 3.9:1 (large text only)

- [ ] **1.4.4 Resize Text (AA)** — Text resizes up to 200% without loss of function
  - Layout uses relative units where possible
  - No content is clipped or overlapping at 200% zoom

- [ ] **1.4.5 Images of Text (AA)** — Real text is used instead of images of text
  - No text is rendered as images
  - Bank card details use styled HTML text, not images

- [ ] **1.4.10 Reflow (AA)** — Content reflows at 320px width without horizontal scrolling
  - Prototype is designed for 320-428px viewport
  - No horizontal scrolling required for content (carousels are exceptions for horizontally-scrolled sets)

- [ ] **1.4.11 Non-text Contrast (AA)** — UI components and graphics meet 3:1 ratio
  - Input borders (neutral-300 on neutral-0): 3.1:1
  - Icon buttons meet 3:1 against their background
  - Progress bar tracks vs. fills meet 3:1

- [ ] **1.4.12 Text Spacing (AA)** — Content adapts to increased text spacing
  - No content is clipped when line height is increased to 1.5x font size
  - No content is lost when letter spacing is increased to 0.12x font size

- [ ] **1.4.13 Content on Hover or Focus (AA)** — Hover/focus content is dismissible and persistent
  - Tooltips (if any) can be dismissed without moving pointer
  - Toast notifications persist for minimum 3 seconds

---

## Operable

### 2.1 Keyboard Accessible

- [ ] **2.1.1 Keyboard (A)** — All functionality is available via keyboard
  - All interactive elements are focusable
  - Custom buttons use `button` element or `role="button"` with `tabindex="0"`
  - Modal/bottom sheet trap focus while open
  - PIN inputs allow keyboard navigation between fields

- [ ] **2.1.2 No Keyboard Trap (A)** — Focus can move freely through the page
  - Modals provide a close mechanism that returns focus to the trigger
  - Bottom sheets can be dismissed with Escape key

- [ ] **2.1.4 Character Key Shortcuts (A)** — No single-key shortcuts exist
  - The prototype does not implement single-character keyboard shortcuts

### 2.2 Enough Time

- [ ] **2.2.1 Timing Adjustable (A)** — Time limits can be adjusted
  - Session timeouts provide warning before logout
  - Toast notifications auto-dismiss after 3 seconds but can be manually dismissed earlier

- [ ] **2.2.2 Pause, Stop, Hide (A)** — Moving content can be controlled
  - Skeleton loading animations respect `prefers-reduced-motion`
  - Auto-advancing carousels (if any) have pause controls

### 2.3 Seizures and Physical Reactions

- [ ] **2.3.1 Three Flashes (A)** — No content flashes more than 3 times per second
  - All animations use durations of 150ms or longer
  - No strobe or rapid flash effects

### 2.4 Navigable

- [ ] **2.4.1 Bypass Blocks (A)** — Skip navigation is provided
  - Skip-to-content link is the first focusable element
  - Main landmark allows screen readers to jump to content

- [ ] **2.4.2 Page Titled (A)** — Each screen has a descriptive title
  - Format: "Screen Name -- NovaPay"
  - Title updates on each screen navigation

- [ ] **2.4.3 Focus Order (A)** — Focus order is logical and intuitive
  - Tab order follows visual layout: header, content, footer, bottom nav
  - Modal focus order: content, actions, close button

- [ ] **2.4.4 Link Purpose (A)** — Link text describes the destination
  - "See All" links include screen reader context ("See all transactions")
  - Navigation items have descriptive labels matching visible text

- [ ] **2.4.5 Multiple Ways (AA)** — Multiple navigation methods are available
  - Bottom navigation provides access to all major sections
  - Dashboard quick actions provide alternative paths
  - Back button provides reverse navigation

- [ ] **2.4.6 Headings and Labels (AA)** — Headings and labels are descriptive
  - Section headers clearly describe the content below
  - Form labels describe the expected input

- [ ] **2.4.7 Focus Visible (AA)** — Keyboard focus is always visible
  - Focus indicator: 2px solid primary-500, 2px offset
  - Focus is visible on all interactive elements
  - Custom focus styles via `:focus-visible` (not `:focus`) to avoid showing for mouse users

### 2.5 Input Modalities

- [ ] **2.5.1 Pointer Gestures (A)** — Multi-point gestures have single-point alternatives
  - Swipe gestures (if any) have tap alternatives
  - Pinch-to-zoom is not required for any functionality

- [ ] **2.5.2 Pointer Cancellation (A)** — Actions fire on up-event, not down-event
  - Click/tap handlers use `click` event (up-event), not `mousedown`/`touchstart`

- [ ] **2.5.3 Label in Name (A)** — Accessible names include visible text
  - Button `aria-label` values include the visible button text
  - Icon-only buttons have descriptive `aria-label` values

- [ ] **2.5.4 Motion Actuation (A)** — Shake/tilt features have alternatives
  - No motion-based interactions in this prototype

---

## Understandable

### 3.1 Readable

- [ ] **3.1.1 Language of Page (A)** — Page language is declared
  - `<html lang="en">` on all pages
  - Lang attribute matches the content language

- [ ] **3.1.2 Language of Parts (AA)** — Language changes are marked
  - Not applicable (single-language prototype)

### 3.2 Predictable

- [ ] **3.2.1 On Focus (A)** — Focus does not trigger unexpected changes
  - Focusing on an input does not navigate away or open a modal
  - Tab navigation does not auto-submit forms

- [ ] **3.2.2 On Input (A)** — Input does not trigger unexpected changes
  - Changing a select value does not auto-navigate
  - Typing in a search field filters results but does not navigate away
  - PIN completion navigates only after all digits are entered

- [ ] **3.2.3 Consistent Navigation (AA)** — Navigation is consistent across screens
  - Bottom navigation appears on all main screens in the same order
  - Back button is always in the top-left position
  - Header layout (left actions, center title, right actions) is consistent

- [ ] **3.2.4 Consistent Identification (AA)** — Same functions have same labels
  - "Transfer" is always labeled "Transfer" (not "Send" on some screens)
  - Icons are used consistently for the same functions across all screens

### 3.3 Input Assistance

- [ ] **3.3.1 Error Identification (A)** — Errors are clearly identified
  - Error messages appear below the relevant input field
  - Error text uses danger-600 color with a warning icon
  - Error inputs have a distinct red border (danger-500)

- [ ] **3.3.2 Labels or Instructions (A)** — Form fields have labels
  - All inputs have visible `label` elements
  - Required fields are indicated (though not with color alone)
  - Input format expectations are communicated (e.g., "6-digit PIN")

- [ ] **3.3.3 Error Suggestion (AA)** — Error messages suggest corrections
  - "Please enter a valid amount" instead of "Invalid input"
  - "PIN must be 6 digits" instead of "Error"
  - Transfer amount errors suggest the available balance

- [ ] **3.3.4 Error Prevention (AA)** — Important actions are reversible or confirmable
  - Transfers show a confirmation screen before execution
  - Bill payments display amount and payee for verification
  - Card freeze is immediately reversible (unfreeze)
  - Logout requires confirmation

---

## Robust

### 4.1 Compatible

- [ ] **4.1.1 Parsing (A)** — HTML is valid
  - No duplicate IDs on the same page
  - All elements are properly nested and closed
  - Attribute values are quoted

- [ ] **4.1.2 Name, Role, Value (A)** — Custom components have accessible names and roles
  - Toggle switches use `input[type="checkbox"]` with proper labeling
  - Custom PIN inputs have `aria-label` for each digit position
  - Bottom sheet uses `role="dialog"` with `aria-label`
  - Progress bars have `role="progressbar"` with `aria-valuenow`/`aria-valuemax`

- [ ] **4.1.3 Status Messages (AA)** — Status updates are announced to assistive technology
  - Toast notifications use `role="alert"` or `aria-live="polite"`
  - Search results count is announced when filters change
  - Loading states communicate progress to screen readers

---

## Mobile-Specific Considerations

### Touch Targets
- [ ] All interactive elements are minimum 44x44px
- [ ] Spacing between adjacent targets is minimum 8px
- [ ] Primary actions are positioned in the thumb zone (bottom third of screen)

### Screen Readers
- [ ] Tested with VoiceOver (iOS)
- [ ] Tested with TalkBack (Android)
- [ ] All screen transitions announce the new screen title
- [ ] Financial amounts are announced with currency (e.g., "negative eighty-four dollars and thirty-two cents")

### Reduced Motion
- [ ] `prefers-reduced-motion` media query disables all non-essential animations
- [ ] Essential animations (loading indicators) have reduced/simplified alternatives
- [ ] Screen transitions are instant when reduced motion is preferred

### High Contrast
- [ ] `prefers-contrast: high` media query increases border widths and shadow contrast
- [ ] All text remains readable in high contrast mode
- [ ] Focus indicators are extra-visible in high contrast mode

---

## Testing Tools

| Tool | Platform | Usage |
|------|----------|-------|
| axe DevTools | Chrome | Automated WCAG testing |
| Lighthouse | Chrome | Accessibility audit |
| VoiceOver | macOS/iOS | Screen reader testing |
| TalkBack | Android | Screen reader testing |
| Colour Contrast Analyser | Desktop | Manual contrast checking |
| WAVE | Web | Visual accessibility evaluation |

---

*This checklist should be reviewed during design, development, and QA phases. Automated tools catch approximately 30% of accessibility issues -- manual testing is essential for complete coverage.*
