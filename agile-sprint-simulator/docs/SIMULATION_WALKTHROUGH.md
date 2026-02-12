# Simulation Walkthrough -- Step-by-Step Sprint Guide

**Author:** Dr Amit Dua

This document walks through a complete simulation run, explaining what happens at each stage and how it maps to real-world Scrum practice.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Phase 1: Setup and Data Loading](#phase-1-setup-and-data-loading)
3. [Phase 2: Sprint Planning](#phase-2-sprint-planning)
4. [Phase 3: Sprint Execution (Daily Standups)](#phase-3-sprint-execution)
5. [Phase 4: Burndown Tracking](#phase-4-burndown-tracking)
6. [Phase 5: Kanban Board Visualization](#phase-5-kanban-board)
7. [Phase 6: Sprint Retrospective](#phase-6-sprint-retrospective)
8. [Phase 7: Report Generation](#phase-7-report-generation)
9. [Interpreting Results](#interpreting-results)
10. [Experimenting with Parameters](#experimenting-with-parameters)
11. [Mapping to Real-World Practice](#mapping-to-real-world-practice)

---

## Prerequisites

Before running the walkthrough, ensure:

```bash
# Navigate to the project directory
cd agile-sprint-simulator

# Activate your virtual environment
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows

# Verify dependencies
pip install -r requirements.txt

# Confirm sample data exists
ls data/sample_backlog.json
ls data/team.json
```

---

## Phase 1: Setup and Data Loading

### What Happens

The simulator reads two JSON files:

1. **`data/sample_backlog.json`** -- 20 user stories for a mobile banking app
2. **`data/team.json`** -- A 5-member cross-functional team called "Phoenix Squad"

### Running This Phase

```bash
# The full simulation loads data automatically:
python -m src.cli run --backlog data/sample_backlog.json --team data/team.json
```

### What You Will See

```
============================================================
  LOADING DATA
============================================================
  Loaded 20 user stories from data/sample_backlog.json
  Total backlog: 108 story points
  Team: Phoenix Squad (5 members)
    - Priya Sharma (Tech Lead, Senior)
    - Arjun Mehta (Developer, Mid)
    - Sneha Reddy (Developer, Mid)
    - Vikram Patel (QA Engineer, Mid)
    - Kavitha Nair (Designer, Senior)
```

### Real-World Equivalent

In a real Scrum team, this phase corresponds to:
- The Product Owner maintaining the Product Backlog in a tool like Jira or Azure DevOps
- The team roster being defined with roles and capacity
- Backlog refinement sessions where stories are detailed and estimated

### Understanding the Data

**Each user story includes:**
- **Story ID** -- Unique identifier (US-001 through US-020)
- **Title** -- Short name (e.g., "User Login with Biometrics")
- **Description** -- Full "As a... I want... so that..." statement
- **Priority** -- MoSCoW classification (Must Have / Should Have / Could Have)
- **Story Points** -- Fibonacci estimate of complexity (1, 2, 3, 5, 8, 13, 21)
- **Tasks** -- Breakdown of work items with hour estimates
- **Acceptance Criteria** -- Conditions for "Done"
- **Tags** -- Labels for categorization and skill matching

**The team includes:**
- Members with specific roles (Tech Lead, Developer, QA, Designer)
- Per-member capacity in hours per day
- Skill tags used for intelligent task assignment
- Experience levels (Junior / Mid / Senior) that affect productivity

---

## Phase 2: Sprint Planning

### What Happens

Sprint Planning follows these steps:

1. **Calculate team capacity** -- Sum of all members' daily hours multiplied by sprint days, adjusted by the focus factor (default 80%)
2. **Estimate velocity** -- Convert capacity hours to story points (heuristic: 1 point ~ 4 ideal hours)
3. **Prioritize the backlog** -- Sort stories by MoSCoW priority, then by story points descending
4. **Select stories** -- Greedily pick stories from the top until velocity budget is exhausted
5. **Generate tasks** -- Auto-create task breakdowns for any stories missing them
6. **Assign tasks** -- Distribute tasks to team members based on skill match and capacity

### Running This Phase Separately

```bash
python -m src.cli plan --strategy moscow --velocity 40
```

### What You Will See

```
============================================================
  SPRINT PLANNING
============================================================
  Team capacity: 198.4 hours
  Estimated velocity: 39 story points

  Committed stories:
    [US-001] User Login with Biometrics (8 pts, 5 tasks)
    [US-002] Account Balance Dashboard (5 pts, 4 tasks)
    [US-003] Fund Transfer Between Own Accounts (8 pts, 5 tasks)
    [US-004] Push Notification for Transactions (5 pts, 4 tasks)
    [US-005] Transaction History with Search (5 pts, 4 tasks)
    [US-010] Card Management (5 pts, 4 tasks)
    [US-015] Two-Factor Authentication Setup (5 pts, 4 tasks)
```

### Real-World Equivalent

In a real Sprint Planning meeting:
- The Product Owner presents the top backlog items
- The team discusses each story and asks clarification questions
- The team commits to what they believe they can deliver
- Stories are broken into tasks and team members volunteer for work

---

## Phase 3: Sprint Execution

### What Happens

For each of the 10 sprint days, the simulator runs a Daily Standup:

1. **Resolve expired blockers** -- Blockers that have lasted their full duration are cleared
2. **For each team member:**
   - Check if they have a new blocker (12% probability per day)
   - Calculate effective working hours based on capacity, experience, and blocker status
   - Apply work to their assigned tasks (prioritizing in-progress over to-do)
   - Generate natural-language standup messages
3. **Update story statuses** -- Derive from underlying task completion

### Running Standups Only

The full simulation runs all standups automatically. For the standalone flow:

```bash
# Run the full sim, then use saved data for analysis:
python -m src.cli run --seed 42
```

### What You Will See

```
  --- Day 3 ---
  Hours remaining: 102.4
  Points remaining: 28
  Stories done: 1
  Active blockers: 1

    [Priya Sharma]
      Yesterday: Completed Implementation and moved it to Done
      Today: Will write unit tests for Code review
    [Arjun Mehta]
      Yesterday: Worked on Build transfer form UI - made good progress
      Today: Plan to finish Build transfer form UI and move to review
      BLOCKER: Database migration script failing on test data
    [Sneha Reddy]
      Yesterday: Continued implementation of Build receipt generation service
      Today: Will continue working on Integration and QA testing
```

### Key Simulation Mechanics

- **Blocker probability:** 12% chance per member per day (configurable)
- **Blocker duration:** 1-3 days (during which productivity drops to 30%)
- **Productivity variance:** Daily output varies between 75% and 115% of base capacity
- **Experience multiplier:** Seniors work at 1.3x speed, Juniors at 0.7x, Mid at 1.0x
- **Task priority:** In-progress tasks are worked on before picking up new to-do items

---

## Phase 4: Burndown Tracking

### What Happens

After all standups are complete, the burndown calculator:

1. Computes the **ideal burndown** -- a straight line from total hours to zero
2. Extracts the **actual burndown** from daily log data
3. Calculates **trend analysis** -- ahead, behind, or on track
4. Estimates **projected completion day** based on average burn rate
5. Renders a **matplotlib chart** saved to `output/burndown.png`

### Running Burndown Separately

```bash
# Generate burndown chart from saved sprint data
python -m src.cli burndown --sprint-data output/sprint_data.json --metric hours

# Use ASCII chart if matplotlib is not installed
python -m src.cli burndown --sprint-data output/sprint_data.json --ascii
```

### Reading the Burndown Chart

The chart shows two lines:

- **Dashed gray line** -- Ideal burndown (where you should be)
- **Solid blue line** -- Actual remaining work (where you are)

**Green shading** between the lines means the team is ahead of schedule.
**Red shading** means the team is behind.

A **yellow dotted vertical line** shows the projected completion day based on the current burn rate.

### Interpreting Patterns

| Pattern | Meaning | Action |
|---------|---------|--------|
| Actual tracks ideal closely | Team is well-calibrated | Maintain current approach |
| Actual above ideal early, converges late | Slow start, strong finish | Check for planning overhead |
| Actual consistently above ideal | Team is behind | Reduce scope or address blockers |
| Flat sections in actual line | No progress on those days | Investigate blockers or interruptions |
| Actual below ideal | Team is ahead | Consider pulling in additional stories |

---

## Phase 5: Kanban Board

### What Happens

The Kanban board displays stories grouped into five columns:

| Column | Meaning |
|--------|---------|
| **TO DO** | Not yet started |
| **IN PROGRESS** | Actively being worked on |
| **IN REVIEW** | Code complete, pending review |
| **DONE** | Meets Definition of Done |
| **BLOCKED** | Impediment preventing progress |

### Running Kanban Display

```bash
python -m src.cli kanban --sprint-data output/sprint_data.json
```

### What You Will See

A color-coded table (if Rich is installed) showing each story as a card with:
- Story ID and title
- Priority (color-coded: red for Must Have, yellow for Should Have, green for Could Have)
- Story points
- Assignee
- Progress bar with percentage

---

## Phase 6: Sprint Retrospective

### What Happens

The retrospective analyzes the completed sprint and generates:

1. **Velocity metrics** -- Planned vs. actual story points
2. **Completion rate** -- Percentage of committed work delivered
3. **Blocker analysis** -- Count, duration, and impact of impediments
4. **Member performance** -- Individual hours worked, tasks completed, days blocked
5. **What Went Well** -- 3-5 positive observations from the sprint data
6. **What To Improve** -- 3-4 areas for improvement
7. **Action Items** -- 3-4 concrete next steps for the team
8. **Sprint Health Score** -- Composite score out of 100
9. **Happiness Index** -- Per-member satisfaction (simulated 1-5 scale)

### Running Retrospective Separately

```bash
python -m src.cli retro --sprint-data output/sprint_data.json
```

### What You Will See

```
Sprint Metrics:
  Planned Velocity:     39 pts
  Actual Velocity:      31 pts
  Completion Rate:      79.5%
  Stories Completed:    5/7
  Total Blockers:       4
  Sprint Health Score:  72.3/100

What Went Well:
  + Team delivered 31 story points (below the planned 39)
  + Sprint goal was partially achieved with 79.5% completion
  + Priya Sharma demonstrated strong productivity with 12 tasks completed

What To Improve:
  - 4 blockers were encountered -- consider proactive dependency management
  - Velocity fell short by 8 points -- review estimation accuracy

Action Items:
  1. Implement 'definition of ready' checklist for all stories
  2. Schedule mid-sprint backlog refinement to catch estimation gaps
  3. Create a shared dependency tracker with external teams
  4. Allocate 10% sprint capacity for addressing technical debt
```

---

## Phase 7: Report Generation

### What Happens

Two comprehensive reports are generated:

1. **`output/sprint_report.md`** -- Full Markdown report with all sprint data
2. **`output/sprint_report.html`** -- Styled HTML report suitable for stakeholders

Both include: sprint overview, metrics table, story breakdown, team performance, daily progress log, blocker log, retrospective highlights, and burndown chart (if generated).

### Running Reports Separately

```bash
# Generate both formats
python -m src.cli report --sprint-data output/sprint_data.json --format both

# Markdown only
python -m src.cli report --format markdown

# HTML only
python -m src.cli report --format html
```

### Opening the HTML Report

Simply open `output/sprint_report.html` in any web browser. The report uses a clean, responsive design with:
- Color-coded metrics cards
- Sortable story table with progress bars
- Retrospective insights organized by category

---

## Interpreting Results

### Healthy Sprint Indicators

- Completion rate above 80%
- Health score above 70/100
- Burndown line tracks close to ideal
- 0-2 blockers total
- All team members have tasks completing throughout the sprint

### Warning Signs

- Completion rate below 60% -- team may be over-committing
- Many blockers (5+) -- dependency management or environment issues
- Flat burndown early in sprint -- team is stuck or under-resourced
- One member doing most of the work -- workload imbalance
- Health score below 50 -- significant process issues

---

## Experimenting with Parameters

Try these variations to see how they affect outcomes:

### Change Sprint Duration

```bash
python -m src.cli run --sprint-days 5   # 1-week sprint
python -m src.cli run --sprint-days 14  # 2-week sprint (with weekends)
```

### Override Velocity

```bash
python -m src.cli plan --velocity 20  # Conservative commitment
python -m src.cli plan --velocity 60  # Aggressive commitment
```

### Change Prioritization Strategy

```bash
python -m src.cli plan --strategy moscow  # Priority-first (default)
python -m src.cli plan --strategy value   # Biggest stories first
python -m src.cli plan --strategy wsjf    # Best value/effort ratio first
python -m src.cli plan --strategy random  # Random (for comparison)
```

### Use a Random Seed

```bash
python -m src.cli run --seed 42    # Reproducible run
python -m src.cli run --seed 123   # Different but also reproducible
python -m src.cli run              # Non-deterministic (different each time)
```

---

## Mapping to Real-World Practice

| Simulation Phase | Real-World Scrum Event | Duration |
|-----------------|----------------------|----------|
| Data Loading | Backlog Refinement (ongoing) | 1-2 hours/week |
| Sprint Planning | Sprint Planning Ceremony | 2-4 hours |
| Daily Standups | Daily Scrum | 15 min/day |
| Burndown Tracking | Information Radiator | Continuous |
| Kanban Board | Physical or Digital Board | Continuous |
| Retrospective | Sprint Retrospective | 1-1.5 hours |
| Report Generation | Sprint Review Preparation | 30 min |

### Tips for Using This Tool in Team Training

1. **Run the simulation as a group exercise** -- project the output and discuss each phase
2. **Compare different strategies** -- run MoSCoW vs. WSJF and discuss trade-offs
3. **Analyze the retro insights** -- use them as discussion starters
4. **Modify the sample data** -- create stories relevant to your team's domain
5. **Run multiple sprints** -- observe how velocity stabilizes over time
6. **Experiment with team composition** -- add/remove members, change experience levels

---

*This walkthrough is part of the Agile Sprint Simulator project by Dr Amit Dua. For the Scrum theory behind each concept, see the [Agile Guide](AGILE_GUIDE.md).*
