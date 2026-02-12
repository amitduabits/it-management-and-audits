"""
Risk Matrix Module - 5x5 risk assessment matrix with visualization.

Implements a standard 5x5 risk matrix (Likelihood x Impact) for
classifying and visualizing security risks. Supports both terminal
(Rich) and HTML output formats.

Likelihood Levels:
    1 = Rare, 2 = Unlikely, 3 = Possible, 4 = Likely, 5 = Almost Certain

Impact Levels:
    1 = Negligible, 2 = Minor, 3 = Moderate, 4 = Major, 5 = Catastrophic
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Risk matrix color mapping (Likelihood, Impact) -> Risk Rating
# L=Likelihood (rows), I=Impact (columns)
RISK_MATRIX = {
    # (Likelihood, Impact): (Risk Score, Risk Rating, Color)
    (1, 1): (1, "Very Low", "#22c55e"),
    (1, 2): (2, "Low", "#22c55e"),
    (1, 3): (3, "Low", "#84cc16"),
    (1, 4): (4, "Medium", "#eab308"),
    (1, 5): (5, "Medium", "#eab308"),
    (2, 1): (2, "Low", "#22c55e"),
    (2, 2): (4, "Low", "#84cc16"),
    (2, 3): (6, "Medium", "#eab308"),
    (2, 4): (8, "High", "#f97316"),
    (2, 5): (10, "High", "#f97316"),
    (3, 1): (3, "Low", "#84cc16"),
    (3, 2): (6, "Medium", "#eab308"),
    (3, 3): (9, "High", "#f97316"),
    (3, 4): (12, "High", "#f97316"),
    (3, 5): (15, "Critical", "#ef4444"),
    (4, 1): (4, "Medium", "#eab308"),
    (4, 2): (8, "High", "#f97316"),
    (4, 3): (12, "High", "#f97316"),
    (4, 4): (16, "Critical", "#ef4444"),
    (4, 5): (20, "Critical", "#ef4444"),
    (5, 1): (5, "Medium", "#eab308"),
    (5, 2): (10, "High", "#f97316"),
    (5, 3): (15, "Critical", "#ef4444"),
    (5, 4): (20, "Critical", "#ef4444"),
    (5, 5): (25, "Critical", "#dc2626"),
}

LIKELIHOOD_LABELS = {
    1: "Rare",
    2: "Unlikely",
    3: "Possible",
    4: "Likely",
    5: "Almost Certain",
}

IMPACT_LABELS = {
    1: "Negligible",
    2: "Minor",
    3: "Moderate",
    4: "Major",
    5: "Catastrophic",
}


@dataclass
class RiskItem:
    """A single risk item plotted on the matrix."""

    name: str
    description: str
    likelihood: int  # 1-5
    impact: int  # 1-5
    risk_score: int = 0
    risk_rating: str = ""
    color: str = ""
    category: str = ""
    current_controls: str = ""
    recommended_controls: str = ""

    def __post_init__(self):
        """Calculate risk score and rating from likelihood and impact."""
        key = (self.likelihood, self.impact)
        if key in RISK_MATRIX:
            self.risk_score, self.risk_rating, self.color = RISK_MATRIX[key]


@dataclass
class RiskMatrixResult:
    """Result containing all risk items mapped to the matrix."""

    risk_items: List[RiskItem] = field(default_factory=list)
    matrix_data: Dict = field(default_factory=dict)
    summary: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "risk_items": [
                {
                    "name": r.name,
                    "description": r.description,
                    "likelihood": r.likelihood,
                    "likelihood_label": LIKELIHOOD_LABELS.get(
                        r.likelihood, ""
                    ),
                    "impact": r.impact,
                    "impact_label": IMPACT_LABELS.get(r.impact, ""),
                    "risk_score": r.risk_score,
                    "risk_rating": r.risk_rating,
                    "color": r.color,
                    "category": r.category,
                    "current_controls": r.current_controls,
                    "recommended_controls": r.recommended_controls,
                }
                for r in self.risk_items
            ],
            "matrix_grid": self.matrix_data,
            "summary": self.summary,
        }


class RiskMatrix:
    """
    5x5 Risk Assessment Matrix.

    Maps security findings onto a Likelihood x Impact matrix to
    provide a visual risk classification. Supports terminal output
    via Rich library and HTML generation for reports.

    The matrix uses standard risk management methodology:
    - Risk Score = Likelihood x Impact (1-25)
    - Risk Ratings: Very Low, Low, Medium, High, Critical

    Example:
        matrix = RiskMatrix()
        result = matrix.generate(risk_assessment_data)
        print(matrix.render_terminal(result))
        html = matrix.render_html(result)
    """

    def generate(
        self, scan_data: Dict, compliance_data: Optional[Dict] = None
    ) -> RiskMatrixResult:
        """
        Generate risk matrix from scan and compliance data.

        Maps findings to likelihood/impact coordinates based on
        severity and exploitability.

        Args:
            scan_data: Combined scan results dictionary.
            compliance_data: Optional compliance assessment results.

        Returns:
            RiskMatrixResult with all risk items positioned on the matrix.
        """
        result = RiskMatrixResult()

        # Map network findings
        network = scan_data.get("network_scan", {})
        if network:
            for finding in network.get("findings", []):
                likelihood, impact = self._severity_to_coordinates(
                    finding.get("severity", "info"),
                    finding.get("cvss_score", 0),
                    "network",
                )
                result.risk_items.append(RiskItem(
                    name=finding.get("title", "Unknown"),
                    description=finding.get("description", ""),
                    likelihood=likelihood,
                    impact=impact,
                    category="Network Security",
                    current_controls="",
                    recommended_controls=finding.get("remediation", ""),
                ))

        # Map web findings
        web = scan_data.get("web_scan", {})
        if web:
            for finding in web.get("all_findings", []):
                likelihood, impact = self._severity_to_coordinates(
                    finding.get("severity", "info"),
                    finding.get("cvss_score", 0),
                    "web",
                )
                result.risk_items.append(RiskItem(
                    name=finding.get("title", "Unknown"),
                    description=finding.get("description", ""),
                    likelihood=likelihood,
                    impact=impact,
                    category="Application Security",
                    current_controls="",
                    recommended_controls=finding.get("remediation", ""),
                ))

        # Map DNS findings
        dns = scan_data.get("dns_scan", {})
        if dns:
            for finding in dns.get("findings", []):
                likelihood, impact = self._severity_to_coordinates(
                    finding.get("severity", "info"),
                    finding.get("cvss_score", 0),
                    "dns",
                )
                result.risk_items.append(RiskItem(
                    name=finding.get("title", "Unknown"),
                    description=finding.get("description", ""),
                    likelihood=likelihood,
                    impact=impact,
                    category="Data Protection",
                    current_controls="",
                    recommended_controls=finding.get("remediation", ""),
                ))

        # Build matrix grid data
        result.matrix_data = self._build_matrix_grid(result.risk_items)

        # Build summary
        result.summary = self._build_summary(result.risk_items)

        return result

    def _severity_to_coordinates(
        self, severity: str, cvss_score: float, finding_type: str
    ) -> Tuple[int, int]:
        """
        Convert a severity rating and CVSS score to matrix coordinates.

        Args:
            severity: Severity string (critical, high, medium, low, info).
            cvss_score: CVSS score (0-10).
            finding_type: Type of finding (network, web, dns).

        Returns:
            Tuple of (likelihood, impact) each 1-5.
        """
        # Base coordinates from severity
        severity_map = {
            "critical": (4, 5),
            "high": (3, 4),
            "medium": (3, 3),
            "low": (2, 2),
            "info": (1, 1),
        }
        base_likelihood, base_impact = severity_map.get(
            severity.lower(), (1, 1)
        )

        # Adjust based on CVSS score
        if cvss_score >= 9.0:
            base_likelihood = min(base_likelihood + 1, 5)
            base_impact = 5
        elif cvss_score >= 7.0:
            base_impact = max(base_impact, 4)
        elif cvss_score >= 4.0:
            base_impact = max(base_impact, 3)

        # Network findings slightly more likely to be exploited
        if finding_type == "network":
            base_likelihood = min(base_likelihood + 1, 5)

        return (base_likelihood, base_impact)

    def _build_matrix_grid(
        self, risk_items: List[RiskItem]
    ) -> Dict:
        """
        Build the 5x5 matrix grid with item counts per cell.

        Returns a dictionary with cell positions and their contents.
        """
        grid = {}
        for l in range(1, 6):
            for i in range(1, 6):
                key = f"{l},{i}"
                score, rating, color = RISK_MATRIX[(l, i)]
                items_in_cell = [
                    r.name for r in risk_items
                    if r.likelihood == l and r.impact == i
                ]
                grid[key] = {
                    "likelihood": l,
                    "impact": i,
                    "risk_score": score,
                    "risk_rating": rating,
                    "color": color,
                    "item_count": len(items_in_cell),
                    "items": items_in_cell[:5],  # Limit to 5 per cell
                }
        return grid

    def _build_summary(self, risk_items: List[RiskItem]) -> Dict:
        """Build a summary of risk distribution."""
        rating_counts = {
            "Critical": 0,
            "High": 0,
            "Medium": 0,
            "Low": 0,
            "Very Low": 0,
        }

        for item in risk_items:
            if item.risk_rating in rating_counts:
                rating_counts[item.risk_rating] += 1

        total = len(risk_items)
        return {
            "total_risks": total,
            "distribution": rating_counts,
            "highest_risk_score": (
                max(r.risk_score for r in risk_items) if risk_items else 0
            ),
            "average_risk_score": (
                round(
                    sum(r.risk_score for r in risk_items) / total, 1
                ) if total > 0 else 0
            ),
        }

    def render_terminal(self, result: RiskMatrixResult) -> str:
        """
        Render the risk matrix as a formatted terminal string.

        Returns a text representation of the 5x5 matrix suitable
        for terminal display.

        Args:
            result: RiskMatrixResult to render.

        Returns:
            Formatted string representation.
        """
        lines = []
        lines.append("")
        lines.append("=" * 78)
        lines.append("               5x5 RISK ASSESSMENT MATRIX")
        lines.append("=" * 78)
        lines.append("")

        # Column headers
        lines.append(
            f"{'':>18} | {'Negligible':^12} | {'Minor':^12} | "
            f"{'Moderate':^12} | {'Major':^12} | {'Catastrophic':^12}"
        )
        lines.append(
            f"{'LIKELIHOOD':>18} | {'Impact 1':^12} | {'Impact 2':^12} | "
            f"{'Impact 3':^12} | {'Impact 4':^12} | {'Impact 5':^12}"
        )
        lines.append("-" * 93)

        # Matrix rows (from highest likelihood to lowest)
        for l in range(5, 0, -1):
            label = f"{LIKELIHOOD_LABELS[l]} ({l})"
            cells = []
            for i in range(1, 6):
                score, rating, _ = RISK_MATRIX[(l, i)]
                count = sum(
                    1 for r in result.risk_items
                    if r.likelihood == l and r.impact == i
                )
                if count > 0:
                    cell = f"{score:>2} [{count}]"
                else:
                    cell = f"{score:>2}"
                cells.append(f"{cell:^12}")
            lines.append(f"{label:>18} | {'|'.join(cells)}")
            if l > 1:
                lines.append(f"{'':>18} |{'':^12}|{'':^12}|{'':^12}|{'':^12}|{'':^12}")

        lines.append("-" * 93)
        lines.append("")

        # Summary
        summary = result.summary
        lines.append("RISK DISTRIBUTION:")
        for rating, count in summary.get("distribution", {}).items():
            if count > 0:
                bar = "#" * count
                lines.append(f"  {rating:>10}: {count:>3} {bar}")

        lines.append("")
        lines.append(
            f"Total Risks: {summary.get('total_risks', 0)} | "
            f"Highest Score: {summary.get('highest_risk_score', 0)} | "
            f"Average Score: {summary.get('average_risk_score', 0)}"
        )
        lines.append("=" * 78)

        return "\n".join(lines)

    def render_html(self, result: RiskMatrixResult) -> str:
        """
        Render the risk matrix as an HTML table.

        Generates a color-coded HTML table suitable for embedding
        in reports and dashboards.

        Args:
            result: RiskMatrixResult to render.

        Returns:
            HTML string of the risk matrix table.
        """
        html_parts = []
        html_parts.append('<div class="risk-matrix-container">')
        html_parts.append('<table class="risk-matrix">')

        # Header row
        html_parts.append("<thead><tr>")
        html_parts.append('<th class="axis-label">Likelihood / Impact</th>')
        for i in range(1, 6):
            html_parts.append(f'<th class="impact-header">{IMPACT_LABELS[i]}<br>({i})</th>')
        html_parts.append("</tr></thead>")

        # Matrix body (top to bottom = highest likelihood to lowest)
        html_parts.append("<tbody>")
        for l in range(5, 0, -1):
            html_parts.append("<tr>")
            html_parts.append(
                f'<td class="likelihood-label">{LIKELIHOOD_LABELS[l]} ({l})</td>'
            )
            for i in range(1, 6):
                score, rating, color = RISK_MATRIX[(l, i)]
                count = sum(
                    1 for r in result.risk_items
                    if r.likelihood == l and r.impact == i
                )
                cell_class = rating.lower().replace(" ", "-")
                badge = (
                    f'<span class="risk-count">{count}</span>'
                    if count > 0
                    else ""
                )
                html_parts.append(
                    f'<td class="risk-cell {cell_class}" '
                    f'style="background-color: {color}20; border-left: 4px solid {color};">'
                    f'<span class="risk-score">{score}</span>'
                    f'{badge}</td>'
                )
            html_parts.append("</tr>")
        html_parts.append("</tbody>")

        html_parts.append("</table>")

        # Legend
        html_parts.append('<div class="matrix-legend">')
        legend_items = [
            ("Critical", "#ef4444"),
            ("High", "#f97316"),
            ("Medium", "#eab308"),
            ("Low", "#84cc16"),
            ("Very Low", "#22c55e"),
        ]
        for label, color in legend_items:
            count = result.summary.get("distribution", {}).get(label, 0)
            html_parts.append(
                f'<span class="legend-item">'
                f'<span class="legend-color" style="background-color:{color};"></span>'
                f'{label} ({count})</span>'
            )
        html_parts.append("</div>")
        html_parts.append("</div>")

        return "\n".join(html_parts)

    def get_risk_level(self, likelihood: int, impact: int) -> Dict:
        """
        Get the risk level for a specific likelihood/impact combination.

        Args:
            likelihood: Likelihood level (1-5).
            impact: Impact level (1-5).

        Returns:
            Dictionary with risk_score, risk_rating, and color.
        """
        likelihood = max(1, min(5, likelihood))
        impact = max(1, min(5, impact))
        score, rating, color = RISK_MATRIX[(likelihood, impact)]
        return {
            "likelihood": likelihood,
            "likelihood_label": LIKELIHOOD_LABELS[likelihood],
            "impact": impact,
            "impact_label": IMPACT_LABELS[impact],
            "risk_score": score,
            "risk_rating": rating,
            "color": color,
        }
