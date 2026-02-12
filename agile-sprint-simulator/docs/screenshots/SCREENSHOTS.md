# Screenshots & Visual Reference

This directory contains screenshots and visual artifacts from the Agile Sprint Simulator.

---

## How to Generate Screenshots

Run the full simulation to produce visual outputs:

```bash
python -m src.cli run --backlog data/sample_backlog.json --team data/team.json --seed 42
```

This creates the following in the `output/` directory:

| File | Description |
|------|-------------|
| `burndown.png` | Burndown chart showing ideal vs. actual progress |
| `sprint_report.html` | Styled HTML report (open in browser for best results) |
| `sprint_report.md` | Markdown report (viewable in any text editor or GitHub) |
| `sprint_data.json` | Raw sprint data for further analysis |

---

## Terminal Output Examples

### Kanban Board

The Kanban board renders in the terminal using the Rich library:

```
python -m src.cli kanban --sprint-data output/sprint_data.json
```

Expected output: A color-coded table with columns for To Do, In Progress, In Review, Done, and Blocked. Each card shows the story ID, title, priority, assignee, and progress bar.

### Sprint Planning Summary

```
python -m src.cli plan
```

Expected output: Lists committed stories with point estimates, team utilization percentages, and total capacity vs. committed hours.

### Retrospective Display

```
python -m src.cli retro --sprint-data output/sprint_data.json
```

Expected output: Formatted panels showing sprint metrics, member performance table, what went well, improvements, action items, and happiness index.

---

## Burndown Chart

The burndown chart (`output/burndown.png`) shows:

- **Dashed gray line** -- Ideal (linear) burndown from total hours to zero
- **Solid blue line** -- Actual remaining hours per sprint day
- **Green shading** -- Days where the team is ahead of schedule
- **Red shading** -- Days where the team is behind schedule
- **Yellow dotted line** -- Projected completion day based on current velocity
- **Annotation** -- Final remaining hours at the end of the sprint

Chart dimensions: 12x7 inches at 150 DPI.

---

## HTML Report

The HTML report (`output/sprint_report.html`) includes:

1. **Header banner** -- Sprint ID, goal, dates, and team name
2. **Metrics dashboard** -- Six cards showing key metrics (points completed, completion rate, stories done, velocity, blockers, hours remaining)
3. **Story breakdown table** -- All stories with status, priority, and progress bars
4. **Retrospective section** -- Color-coded insights (green for positives, yellow for improvements, blue for action items)
5. **Burndown chart image** -- Embedded if available

The report uses a clean, responsive CSS design that works well in any modern browser.

---

## Adding Your Own Screenshots

To capture terminal screenshots:

1. Run the desired command in a terminal with a dark background
2. Use your OS screenshot tool or a terminal recording tool like `asciinema`
3. Save images to this directory with descriptive names

Suggested naming convention:
- `kanban_day5.png` -- Kanban board at sprint midpoint
- `burndown_complete.png` -- Burndown chart for a completed sprint
- `retro_metrics.png` -- Retrospective metrics panel
- `planning_summary.png` -- Sprint planning output

---

*Screenshots are not committed to version control (see `.gitignore`). Generate them locally by running the simulation.*
