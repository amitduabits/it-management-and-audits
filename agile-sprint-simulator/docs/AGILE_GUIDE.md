# Comprehensive Scrum & Agile Reference Guide

**Author:** Dr Amit Dua

This guide provides a thorough reference for the Scrum framework as practiced in professional software development teams. It covers the principles, roles, events, and artifacts that make up modern Agile delivery.

---

## Table of Contents

1. [The Agile Manifesto](#the-agile-manifesto)
2. [Agile Principles](#agile-principles)
3. [Why Scrum?](#why-scrum)
4. [Scrum Roles](#scrum-roles)
5. [Scrum Events (Ceremonies)](#scrum-events)
6. [Scrum Artifacts](#scrum-artifacts)
7. [User Stories](#user-stories)
8. [Estimation Techniques](#estimation-techniques)
9. [Sprint Metrics](#sprint-metrics)
10. [Prioritization Frameworks](#prioritization-frameworks)
11. [Common Anti-Patterns](#common-anti-patterns)
12. [Scaling Scrum](#scaling-scrum)
13. [Recommended Reading](#recommended-reading)

---

## The Agile Manifesto

Published in 2001 by 17 software practitioners, the Agile Manifesto establishes four core values:

> **Individuals and interactions** over processes and tools
> **Working software** over comprehensive documentation
> **Customer collaboration** over contract negotiation
> **Responding to change** over following a plan

This does not mean the items on the right are unimportant -- it means the items on the left are valued **more**.

---

## Agile Principles

The 12 principles behind the Agile Manifesto:

1. **Satisfy the customer** through early and continuous delivery of valuable software.
2. **Welcome changing requirements**, even late in development. Agile processes harness change for the customer's competitive advantage.
3. **Deliver working software frequently**, from a couple of weeks to a couple of months, with a preference for the shorter timescale.
4. **Business people and developers** must work together daily throughout the project.
5. **Build projects around motivated individuals.** Give them the environment and support they need, and trust them to get the job done.
6. **Face-to-face conversation** is the most efficient and effective method of conveying information.
7. **Working software** is the primary measure of progress.
8. Agile processes promote **sustainable development**. The sponsors, developers, and users should be able to maintain a constant pace indefinitely.
9. Continuous attention to **technical excellence** and good design enhances agility.
10. **Simplicity** -- the art of maximizing the amount of work not done -- is essential.
11. The best architectures, requirements, and designs emerge from **self-organizing teams**.
12. At regular intervals, **the team reflects** on how to become more effective, then tunes and adjusts its behavior accordingly.

---

## Why Scrum?

Scrum is the most widely used Agile framework because it provides:

- **Structure without rigidity** -- just enough ceremony to stay organized
- **Transparency** -- everyone can see what's happening and why
- **Rapid feedback loops** -- problems surface in days, not months
- **Continuous improvement** -- built-in retrospectives drive process evolution
- **Predictability** -- velocity-based planning enables reliable forecasting

### Scrum vs. Other Agile Methods

| Method | Best For | Key Difference from Scrum |
|--------|----------|--------------------------|
| **Kanban** | Continuous flow work (support, ops) | No sprints; focus on WIP limits |
| **XP (Extreme Programming)** | Engineering practices | Prescribes technical practices (TDD, pair programming) |
| **SAFe** | Large enterprises (100+ people) | Multiple Scrum teams coordinated at scale |
| **Lean** | Eliminating waste | Broader philosophy, less prescriptive |

---

## Scrum Roles

### Product Owner (PO)

The Product Owner is the single point of accountability for the product's value.

**Responsibilities:**
- Maintain and prioritize the Product Backlog
- Define user stories with clear acceptance criteria
- Make scope and priority decisions
- Accept or reject completed work
- Represent stakeholder interests

**Key skill:** The ability to say "no" to low-priority requests.

### Scrum Master (SM)

The Scrum Master is a servant-leader who ensures the Scrum process runs smoothly.

**Responsibilities:**
- Facilitate all Scrum events
- Remove impediments that block the team
- Coach the team on Scrum practices
- Shield the team from external interruptions
- Drive continuous process improvement

**What the Scrum Master is NOT:** a project manager, a task assigner, or the team's boss.

### Development Team

A cross-functional group of professionals who do the actual work of delivering the product increment.

**Characteristics:**
- **Self-organizing** -- they decide how to turn backlog items into working increments
- **Cross-functional** -- the team collectively has all skills needed to deliver
- **Size** -- typically 3-9 members (optimal: 5-7)
- **No sub-teams or titles** -- everyone is a "Developer" regardless of specialty

---

## Scrum Events

### Sprint

The heartbeat of Scrum. A time-boxed iteration (typically 2 weeks) during which a "Done" product increment is created.

| Aspect | Details |
|--------|---------|
| Duration | 1-4 weeks (2 weeks is most common) |
| Start | Immediately after previous sprint ends |
| Scope | Cannot be changed once sprint starts (only clarified) |
| Cancelation | Only the Product Owner can cancel a sprint |

### Sprint Planning

**Purpose:** Define what will be delivered and how it will be achieved.

**Timebox:** 2 hours per week of sprint (4 hours for a 2-week sprint).

**Two parts:**
1. **What** -- The PO presents the highest-priority items. The team selects what they can commit to based on velocity.
2. **How** -- The team breaks selected stories into tasks and creates a plan for the sprint.

**Output:** Sprint Backlog + Sprint Goal

### Daily Scrum (Standup)

**Purpose:** Synchronize the team's work and identify impediments.

**Timebox:** 15 minutes, same time and place every day.

**Three questions per member:**
1. What did I do since the last standup?
2. What will I do before the next standup?
3. Are there any blockers preventing my progress?

**Rules:**
- Only the development team participates (PO and SM may observe)
- Not a status report -- it's for the team to coordinate
- Detailed discussions happen "offline" after the standup

### Sprint Review

**Purpose:** Inspect the increment and adapt the Product Backlog.

**Timebox:** 1 hour per week of sprint.

**Format:**
- Team demos completed work to stakeholders
- PO confirms which items meet the Definition of Done
- Stakeholders provide feedback
- Product Backlog is updated based on new insights

### Sprint Retrospective

**Purpose:** Inspect the process and create a plan for improvements.

**Timebox:** 45 minutes per week of sprint.

**Common formats:**
- **Start / Stop / Continue** -- What should we start doing, stop doing, and continue doing?
- **4 Ls** -- What did we Like, Learn, Lack, and Long for?
- **Mad / Sad / Glad** -- What made us angry, sad, or happy?
- **Sailboat** -- Wind (what propels us), anchors (what holds us back), rocks (risks ahead)

**Output:** 2-3 concrete action items for the next sprint.

---

## Scrum Artifacts

### Product Backlog

The single, ordered list of everything that is needed in the product.

**Properties:**
- Owned and maintained by the Product Owner
- Items at the top are small, well-defined, and ready for sprint planning
- Items at the bottom are large, vague, and need refinement
- Continuously refined (Backlog Refinement / Grooming)

### Sprint Backlog

The set of Product Backlog items selected for the sprint, plus a plan for delivering them.

**Properties:**
- Owned by the Development Team
- Updated daily (tasks are added, modified, or removed)
- Only the team can change the Sprint Backlog during the sprint
- Makes visible all work needed to meet the Sprint Goal

### Product Increment

The sum of all completed Product Backlog items during a sprint and the value of all previous sprints.

**Properties:**
- Must meet the Definition of Done
- Must be usable (even if the PO decides not to release it)
- Each sprint produces one increment

### Definition of Done (DoD)

A shared understanding of what "Done" means for the team. Every item must meet these criteria before it can be considered complete.

**Example DoD:**
- Code is written and peer-reviewed
- Unit tests pass with >80% coverage
- Integration tests pass
- Documentation is updated
- Feature is deployed to staging
- Product Owner has accepted the feature

---

## User Stories

### Format

The standard user story format is:

> **As a** [type of user], **I want** [some goal] **so that** [some benefit].

### Examples

- As a **mobile banking user**, I want to **log in with my fingerprint** so that I can **access my account quickly and securely**.
- As a **frequent traveler**, I want to **view balances in multiple currencies** so that I can **manage foreign transactions without confusion**.

### INVEST Criteria

Good user stories are:

| Letter | Criterion | Meaning |
|--------|-----------|---------|
| **I** | Independent | Can be developed without depending on other stories |
| **N** | Negotiable | Details can be discussed between PO and team |
| **V** | Valuable | Delivers clear value to the user or business |
| **E** | Estimable | The team can estimate its size |
| **S** | Small | Can be completed within a single sprint |
| **T** | Testable | Has clear acceptance criteria that can be verified |

### Acceptance Criteria

Every story needs explicit conditions for acceptance. Use the **Given/When/Then** format:

```
GIVEN I am on the login screen
WHEN I tap the fingerprint icon and authenticate successfully
THEN I am redirected to my account dashboard
AND my session token is stored securely
```

---

## Estimation Techniques

### Story Points

Relative measure of effort using the Fibonacci sequence: **1, 2, 3, 5, 8, 13, 21**.

- **1 point** = trivial change (copy fix, config change)
- **3 points** = small feature with known approach
- **5 points** = medium feature requiring some research
- **8 points** = large feature touching multiple components
- **13 points** = very large -- consider splitting
- **21 points** = epic-sized -- must be split before sprinting

### Planning Poker

The team's most popular estimation technique:

1. PO reads the user story
2. Each team member privately selects a card (Fibonacci number)
3. All cards are revealed simultaneously
4. If estimates diverge, highest and lowest explain their reasoning
5. Re-estimate until consensus (or near-consensus) is reached

### T-Shirt Sizing

Quick relative sizing: **XS, S, M, L, XL**

Useful for rough backlog ordering when precise estimates aren't needed yet.

### Affinity Estimation

1. Write all stories on sticky notes
2. Silently sort them into size groups
3. Assign point values to each group
4. Quick and effective for large backlogs

---

## Sprint Metrics

### Velocity

**Definition:** The total story points completed per sprint.

**Usage:**
- Track velocity over 3+ sprints to establish a reliable average
- Use average velocity to forecast future sprints
- Never compare velocity between teams (it's a relative measure)

### Burndown Chart

Shows remaining work (hours or points) over time.

**Reading the chart:**
- Line above ideal = behind schedule
- Line below ideal = ahead of schedule
- Flat sections = no progress (possible blockers)
- Upward spikes = scope increase

### Burnup Chart

Shows completed work accumulating over time, plotted against total scope.

**Advantage over burndown:** Makes scope changes visible.

### Cycle Time

**Definition:** Time from when work begins on a story to when it's done.

**Goal:** Reduce cycle time to deliver value faster.

### Lead Time

**Definition:** Time from when a story is requested to when it's delivered.

Includes time spent in the backlog before work begins.

### Cumulative Flow Diagram (CFD)

Shows the number of items in each status (To Do, In Progress, Done) over time.

**What to look for:**
- Bands should be roughly parallel (steady flow)
- Widening "In Progress" band = WIP is growing (bottleneck)
- Narrowing "To Do" band = backlog is depleting (need refinement)

---

## Prioritization Frameworks

### MoSCoW

| Category | Meaning | Guideline |
|----------|---------|-----------|
| **Must Have** | Non-negotiable requirements | ~60% of effort |
| **Should Have** | Important but not critical | ~20% of effort |
| **Could Have** | Nice to have | ~20% of effort |
| **Won't Have** | Explicitly out of scope (this time) | 0% of effort |

### Weighted Shortest Job First (WSJF)

```
WSJF = Cost of Delay / Job Duration
```

Where **Cost of Delay** considers:
- User/business value
- Time criticality
- Risk reduction / opportunity enablement

Higher WSJF = do it first.

### Value vs. Effort Matrix

Plot stories on a 2x2 grid:

| | Low Effort | High Effort |
|---|-----------|-------------|
| **High Value** | Quick Wins (do first) | Major Projects (plan carefully) |
| **Low Value** | Fill-ins (do if time) | Money Pits (avoid) |

### Kano Model

Categorizes features by customer satisfaction:

- **Must-be** (Basic): Expected; absence causes dissatisfaction
- **One-dimensional** (Performance): More is better; directly correlates with satisfaction
- **Attractive** (Excitement): Unexpected delights; absence does not cause dissatisfaction

---

## Common Anti-Patterns

### Planning Anti-Patterns
- **Over-committing:** Taking on more work than velocity supports
- **No sprint goal:** Stories lack a unifying objective
- **Hero-driven planning:** Relying on one person to carry the sprint
- **Ignoring technical debt:** Always prioritizing features over maintenance

### Standup Anti-Patterns
- **Status report to the manager:** Updates directed at PO/SM instead of team
- **Problem-solving in standup:** Discussions exceeding the 15-minute timebox
- **Absent members:** People skipping standups regularly
- **No follow-up on blockers:** Blockers mentioned but never resolved

### Retrospective Anti-Patterns
- **Blame culture:** Finger-pointing instead of systemic analysis
- **No action items:** Discussion without commitment to change
- **Same issues every sprint:** Action items from previous retros are ignored
- **Only the Scrum Master talks:** Team members do not feel safe to speak up

### Organizational Anti-Patterns
- **Micro-management:** Managers assigning tasks directly to developers
- **Shared team members:** People split across multiple Scrum teams
- **Absent Product Owner:** PO not available for questions during the sprint
- **No Definition of Done:** Quality standards are inconsistent

---

## Scaling Scrum

When a product requires more than one Scrum team:

### Scrum of Scrums

- Representatives from each team meet daily or multiple times per week
- Focus on inter-team dependencies and integration issues
- Lightweight coordination mechanism

### Nexus (by Scrum.org)

- 3-9 Scrum teams working on a single product
- Adds a Nexus Integration Team to manage dependencies
- Shared Product Backlog with a single Product Owner

### LeSS (Large-Scale Scrum)

- Multiple teams work from a single Product Backlog
- One Product Owner, one Definition of Done
- Shared Sprint Review and overall Retrospective

### SAFe (Scaled Agile Framework)

- Comprehensive framework for enterprise-scale Agile
- Adds Program Increment (PI) Planning layer above sprints
- Defines roles like Release Train Engineer and Solution Architect
- Most prescriptive of the scaling frameworks

---

## Recommended Reading

| Book | Author | Why Read It |
|------|--------|-------------|
| *Scrum: The Art of Doing Twice the Work in Half the Time* | Jeff Sutherland | Scrum co-creator's accessible introduction |
| *Agile Estimating and Planning* | Mike Cohn | Deep dive into estimation and velocity |
| *User Stories Applied* | Mike Cohn | Definitive guide to writing effective user stories |
| *Coaching Agile Teams* | Lyssa Adkins | Essential for Scrum Masters and coaches |
| *The Phoenix Project* | Gene Kim et al. | Novel format -- DevOps and Agile in a realistic scenario |
| *Accelerate* | Nicole Forsgren et al. | Research-backed evidence for Agile and DevOps practices |
| *Clean Agile* | Robert C. Martin | Back to basics -- what Agile really means |
| *Lean Software Development* | Mary & Tom Poppendieck | Lean thinking applied to software |

---

*This guide is part of the Agile Sprint Simulator project. For hands-on practice with these concepts, run the simulator and observe how the Scrum events and artifacts play out in a realistic sprint scenario.*
