# Screenshots

This directory is reserved for dashboard screenshots used in documentation
and project presentations.

---

## Recommended Screenshots

When documenting the application, capture the following views:

### 1. Upload Page
- **File:** `upload_page.png`
- **Description:** The landing page with file upload dropzone, sample dataset
  selector, and feature overview cards.

### 2. Configuration Page
- **File:** `configure_page.png`
- **Description:** The dashboard configuration step showing detected columns,
  column type badges, and template selection options.

### 3. Dashboard Overview
- **File:** `dashboard_overview.png`
- **Description:** Full dashboard view with KPI cards, filter bar, and
  multiple charts rendered from sample sales data.

### 4. KPI Cards Detail
- **File:** `kpi_cards.png`
- **Description:** Close-up of KPI cards showing formatted values, trend
  arrows, and period-over-period change percentages.

### 5. Interactive Charts
- **File:** `charts_interactive.png`
- **Description:** Charts showing hover tooltips, zoom controls, and
  Plotly toolbar interactions.

### 6. Filter Panel Active
- **File:** `filters_active.png`
- **Description:** Dashboard with active filters applied, showing filtered
  KPIs and charts.

### 7. Data Preview Table
- **File:** `data_table.png`
- **Description:** The sortable, paginated data preview table with search
  functionality.

### 8. Mobile Responsive View
- **File:** `mobile_view.png`
- **Description:** Dashboard rendered on a mobile viewport showing the
  responsive layout with collapsed sidebar.

### 9. Chart Fullscreen Modal
- **File:** `chart_fullscreen.png`
- **Description:** A chart expanded to fullscreen modal for detailed analysis.

### 10. Financial Dashboard
- **File:** `finance_dashboard.png`
- **Description:** Dashboard using the finance template with revenue,
  expenses, profit margins, and departmental breakdowns.

---

## Capture Guidelines

- Use a browser window width of 1440px for desktop screenshots.
- Use 375px width for mobile screenshots.
- Capture at 2x resolution for crisp display in documentation.
- Save as PNG with reasonable compression.
- Avoid including any sensitive or real business data in screenshots.

---

## Adding Screenshots

Place screenshot files directly in this directory:

```
docs/screenshots/
    SCREENSHOTS.md
    upload_page.png
    dashboard_overview.png
    kpi_cards.png
    ...
```

Reference them in documentation using relative paths:

```markdown
![Dashboard Overview](docs/screenshots/dashboard_overview.png)
```
