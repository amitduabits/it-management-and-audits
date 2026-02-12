# User Journey Maps

Detailed journey maps for the five core flows in a mobile banking application. Each journey captures the user's actions, thoughts, emotions, and identifies opportunities for improvement at every stage.

---

## Journey 1: First-Time Login (Sarah's Perspective)

### Context
Sarah has just downloaded the app and completed registration. This is her first login.

```
Stage:    ONBOARDING          LOGIN              DASHBOARD           EXPLORATION
          ─────────────────── ─────────────────── ─────────────────── ───────────
Action:   Swipe through       Set up biometric    View balance        Tap quick actions
          4 welcome slides    Enter 6-digit PIN   See transactions    Explore screens

Thought:  "This looks          "Fingerprint is     "Oh, there's my    "I like the
          professional"        convenient"          balance right       quick actions.
                                                    away. Nice."       Very clean."

Emotion:  Curious ───────────> Confident ─────────> Satisfied ─────────> Engaged
          ★★★☆☆                ★★★★☆                ★★★★★               ★★★★☆
```

### Touchpoints
| Stage | Screen | Duration | Key Elements |
|-------|--------|----------|-------------|
| Welcome | `onboarding.html` | 15-30 sec | 4 slides, skip option, progress dots |
| Auth Setup | `login.html` | 10-20 sec | PIN entry, biometric option |
| First View | `dashboard.html` | 5-10 sec | Balance, account summary, quick actions |
| Discovery | Various screens | 30-60 sec | Navigation, feature exploration |

### Opportunities
1. **Auto-detect biometric capability** and pre-select the appropriate method
2. **Highlight one key feature** on the dashboard for first-time users (e.g., "Set up your first transfer")
3. **Reduce onboarding to 3 screens** for users who skip (track skip rate)
4. **Show a welcome toast** on first dashboard load: "Welcome, Sarah!"

### Pain Points to Prevent
- Onboarding screens that require reading too much text
- Biometric setup that requires multiple attempts
- Empty dashboard (ensure sample data or guided setup)

---

## Journey 2: Sending Money to a Friend (Sarah's Perspective)

### Context
Sarah wants to split a dinner bill by sending $50 to her friend Alex.

```
Stage:    INITIATE            SELECT RECIPIENT    ENTER AMOUNT        CONFIRM & SEND
          ─────────────────── ─────────────────── ─────────────────── ───────────
Action:   Tap Transfer        Tap Alex from       Tap $50 quick       Review details
          from dashboard      recent contacts     amount button       Tap Continue

Thought:  "Need to send       "There he is,       "$50 sounds         "Yep, $50 to
          Alex his half"      easy to find"        right"              Alex. Done."

Emotion:  Intentional ──────> Relieved ──────────> Confident ─────────> Satisfied
          ★★★☆☆               ★★★★☆                ★★★★★               ★★★★★
```

### Detailed Flow

| Step | Action | Screen | Time | Success Criteria |
|------|--------|--------|------|-----------------|
| 1 | Tap "Transfer" quick action | Dashboard | 1 sec | Immediate navigation |
| 2 | See recent contacts | Transfer | 0 sec | Alex visible without scrolling |
| 3 | Tap Alex's avatar | Transfer | 1 sec | Recipient confirmed with visual feedback |
| 4 | Tap "$50" quick amount | Transfer | 1 sec | Amount displays in large text |
| 5 | Review recipient, amount, source | Transfer | 2-3 sec | All details visible at once |
| 6 | Tap "Continue" | Transfer | 1 sec | Loading indicator appears |
| 7 | See success toast | Transfer | 0 sec | Confirmation with amount and recipient |

**Total estimated time: 6-8 seconds**

### Opportunities
1. **Pre-populate the transfer screen** if coming from a contact's profile
2. **Show available balance** next to the amount to prevent overdraft attempts
3. **Remember the last transfer amount** to a specific contact
4. **Offer a "Request Money" option** as an alternative to "Send Money"
5. **Add a note/memo field** for splitting bills ("Dinner at Chez Laurent")

### Error Scenarios
- Insufficient funds: Show clear message with current balance, suggest a lower amount
- Network error: Save as draft, offer retry
- Wrong recipient: Provide a "Change" button that is always visible

---

## Journey 3: Paying a Bill (Robert's Perspective)

### Context
Robert receives a notification that his internet bill is due tomorrow. He wants to pay it immediately.

```
Stage:    NOTIFICATION        NAVIGATE TO BILL    REVIEW DETAILS      PAY & CONFIRM
          ─────────────────── ─────────────────── ─────────────────── ───────────
Action:   Tap notification    See bill details    Check amount        Tap Pay Now
          banner              and due date        and due date        See confirmation

Thought:  "Better pay this    "There it is,       "Okay, $79.99      "Good, it went
          before I forget"    due tomorrow"        looks right"        through."

Emotion:  Concerned ────────> Focused ───────────> Cautious ──────────> Relieved
          ★★☆☆☆               ★★★☆☆                ★★★★☆               ★★★★★
```

### Detailed Flow

| Step | Action | Screen | Time | Success Criteria |
|------|--------|--------|------|-----------------|
| 1 | Receive push notification | System | 0 sec | Clear title: "Bill Due Tomorrow" |
| 2 | Tap notification | Notifications | 1 sec | Navigates to Payments screen |
| 3 | Identify the bill | Payments | 2 sec | Urgency badge, amount, payee name |
| 4 | Tap "Pay Now" | Payments | 1 sec | Loading state on button |
| 5 | See success confirmation | Payments | 0 sec | Toast with amount and payee |
| 6 | Verify in transaction history | History | 5 sec | Transaction appears as "Pending" |

**Total estimated time: 9-12 seconds**

### Opportunities
1. **Deep link from notification** directly to the specific bill payment
2. **Show payment source** (which account will be debited) before confirming
3. **Offer autopay setup** after a manual payment: "Set up autopay for this bill?"
4. **Send a payment receipt** via email automatically
5. **Display next due date** after payment: "Next payment due March 13"

### Error Scenarios
- Bill amount changed since last check: Show updated amount with explanation
- Payment source insufficient: Suggest alternative account
- Duplicate payment warning: "You already paid this bill on [date]. Pay again?"

---

## Journey 4: Checking Transaction History (Maya's Perspective)

### Context
Maya notices a charge she doesn't recognize and wants to investigate.

```
Stage:    CONCERN             SEARCH              IDENTIFY            RESOLVE
          ─────────────────── ─────────────────── ─────────────────── ───────────
Action:   Open app,           Search for          Find the charge,    Feel reassured
          go to History       the amount          recognize merchant  or contact support

Thought:  "What is that       "Let me search      "Oh! That's the    "Okay, I
          $18.50 charge?"     for $18.50"          Uber ride"         remember now"

Emotion:  Anxious ───────────> Determined ────────> Recognizing ──────> Relieved
          ★☆☆☆☆               ★★★☆☆                ★★★★☆               ★★★★★
```

### Detailed Flow

| Step | Action | Screen | Time | Success Criteria |
|------|--------|--------|------|-----------------|
| 1 | Open app, authenticate | Login | 3 sec | Biometric instant |
| 2 | Tap History in bottom nav | Dashboard | 1 sec | Navigation to History |
| 3 | See today's transactions | History | 0 sec | Grouped by date |
| 4 | Spot the $18.50 charge | History | 2 sec | Amount visible, scannable |
| 5 | Read merchant name | History | 1 sec | "Uber" with transportation icon |
| 6 | Recall the transaction | - | - | User memory confirmation |

**Total estimated time: 7-10 seconds (if found by browsing)**

### Alternative Flow: Using Search

| Step | Action | Screen | Time |
|------|--------|--------|------|
| 3a | Tap search field | History | 1 sec |
| 4a | Type "18.50" or "uber" | History | 3 sec |
| 5a | See filtered results | History | 0 sec |

### Opportunities
1. **Show merchant category icons** for quick visual identification
2. **Include merchant logo** when available (future enhancement)
3. **Allow filtering by amount range** ("$10-$25")
4. **Show transaction location** (if available) for additional context
5. **One-tap dispute button** on each transaction detail view
6. **"This doesn't look right?"** link on unrecognized-looking charges

### If the Charge Is Fraudulent
- Clear path from transaction detail to "Dispute Transaction"
- Pre-fill dispute form with transaction details
- Show estimated resolution time
- Provide option to freeze the card immediately

---

## Journey 5: Managing a Card (Robert's Perspective)

### Context
Robert lost his wallet at a restaurant. He needs to freeze his primary card immediately.

```
Stage:    PANIC               FIND CARD           FREEZE              NEXT STEPS
          ─────────────────── ─────────────────── ─────────────────── ───────────
Action:   Open app urgently   Navigate to Cards   Tap Freeze button   Consider reporting
                              Find primary card                       lost card

Thought:  "I need to freeze   "Where's the        "Okay, it's        "Should I order
          my card NOW"         freeze option?"      frozen. Safe."     a replacement?"

Emotion:  Panicked ──────────> Stressed ──────────> Immediate Relief ─> Cautious
          ☆☆☆☆☆               ★★☆☆☆                ★★★★★               ★★★☆☆
```

### Detailed Flow

| Step | Action | Screen | Time | Success Criteria |
|------|--------|--------|------|-----------------|
| 1 | Open app, authenticate | Login | 3 sec | Must work fast under stress |
| 2 | Tap "Cards" in bottom nav | Dashboard | 1 sec | Direct navigation to Cards |
| 3 | See primary card | Cards | 0 sec | Card is first in carousel |
| 4 | Tap "Freeze" button | Cards | 1 sec | Button is immediately visible |
| 5 | Card visual changes (grayscale) | Cards | 0 sec | Clear visual confirmation |
| 6 | Toast: "Card has been frozen" | Cards | 0 sec | Verbal confirmation |
| 7 | See "Report Lost" option | Cards | 2 sec | Available in card actions |

**Total estimated time: 7-10 seconds**

### Critical Design Requirements
1. **Freeze must be ONE TAP** -- no confirmation dialog for freeze (only for unfreeze)
2. **Visual feedback must be INSTANT** -- card appearance changes immediately
3. **Report Lost must be visible** without scrolling when card is frozen
4. **Phone support shortcut** should appear when card is frozen
5. **Card status badge** must update to "Frozen" immediately

### Opportunities
1. **Add freeze shortcut** to the dashboard quick actions
2. **Emergency freeze via notification** action button
3. **Automatic freeze recommendation** if unusual activity is detected
4. **Replacement card ordering** in the same flow
5. **Temporary virtual card** while physical card is being replaced

---

## Journey Map Summary

| Journey | Primary Persona | Emotional Arc | Key Metric | Target |
|---------|----------------|---------------|------------|--------|
| First Login | Sarah | Curious to Engaged | Onboarding completion | 80%+ |
| Send Money | Sarah | Intentional to Satisfied | Time to complete | <10 sec |
| Pay Bill | Robert | Concerned to Relieved | On-time payment rate | 95%+ |
| Check History | Maya | Anxious to Relieved | Time to find transaction | <10 sec |
| Freeze Card | Robert | Panicked to Relieved | Time to freeze | <10 sec |

---

## How to Use These Journey Maps

### For Prototyping
- Walk through each journey in the prototype to verify the flow matches the mapped experience
- Time each journey and compare against target metrics
- Identify any screens or interactions not covered by these journeys

### For User Testing
- Use these journeys as test scenarios
- Ask participants to think aloud to capture thoughts and emotions
- Compare observed emotions with the mapped emotional arcs

### For Stakeholder Communication
- Present journey maps to demonstrate user-centered design thinking
- Use emotional arcs to justify UX investments ("This change moves the user from Anxious to Relieved")
- Reference pain points to prioritize backlog items

---

*Journey maps should be updated after each round of user testing. The emotional arcs and pain points documented here are hypotheses to be validated with real user data.*
