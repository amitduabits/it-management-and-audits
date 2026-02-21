"""
BI Dashboard Builder - Main Flask Application

Handles routing, file uploads, dashboard configuration, and rendering.
Provides endpoints for data upload, dashboard generation, and API access.
"""

import os
import json
import uuid
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, session, send_from_directory
)
from werkzeug.utils import secure_filename

from app.data_processor import DataProcessor
from app.chart_generator import ChartGenerator
from app.kpi_calculator import KPICalculator

# ---------------------------------------------------------------------------
# Application Factory
# ---------------------------------------------------------------------------

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")
DATA_FOLDER = os.path.join(BASE_DIR, "data")
ALLOWED_EXTENSIONS = {"csv", "xlsx", "json"}

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)
app.secret_key = os.environ.get("SECRET_KEY", "bi-dashboard-secret-key-change-in-production")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB limit

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------------------------------------------------------------------
# Globals / Singletons
# ---------------------------------------------------------------------------

processor = DataProcessor()
chart_gen = ChartGenerator()
kpi_calc = KPICalculator()

# In-memory store for active sessions (swap for Redis/DB in production)
dashboard_sessions: dict = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def allowed_file(filename: str) -> bool:
    """Check whether the uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_dashboard_templates() -> list[dict]:
    """Scan the templates/ directory for dashboard config JSON files."""
    templates = []
    if os.path.isdir(TEMPLATE_FOLDER):
        for fname in os.listdir(TEMPLATE_FOLDER):
            if fname.endswith(".json"):
                fpath = os.path.join(TEMPLATE_FOLDER, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as fh:
                        cfg = json.load(fh)
                        cfg["_filename"] = fname
                        templates.append(cfg)
                except (json.JSONDecodeError, OSError):
                    continue
    return templates


def load_sample_datasets() -> list[dict]:
    """List available sample datasets in data/ folder."""
    datasets = []
    if os.path.isdir(DATA_FOLDER):
        for fname in os.listdir(DATA_FOLDER):
            if fname.endswith((".csv", ".xlsx")):
                datasets.append({
                    "filename": fname,
                    "path": os.path.join(DATA_FOLDER, fname),
                    "size": os.path.getsize(os.path.join(DATA_FOLDER, fname)),
                })
    return datasets


# ---------------------------------------------------------------------------
# Routes - Pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Landing / upload page."""
    templates = load_dashboard_templates()
    samples = load_sample_datasets()
    return render_template("index.html", templates=templates, samples=samples)


@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle data file upload and redirect to configuration step."""
    # Check if user selected a sample dataset
    sample_file = request.form.get("sample_dataset")
    if sample_file:
        file_path = os.path.join(DATA_FOLDER, secure_filename(sample_file))
        if os.path.exists(file_path):
            session_id = str(uuid.uuid4())
            try:
                df = processor.load_file(file_path)
                summary = processor.get_summary(df)
                dashboard_sessions[session_id] = {
                    "file_path": file_path,
                    "filename": sample_file,
                    "summary": summary,
                    "uploaded_at": datetime.now().isoformat(),
                }
                session["dashboard_id"] = session_id
                flash(f"Loaded sample dataset: {sample_file}", "success")
                return redirect(url_for("configure", session_id=session_id))
            except Exception as exc:
                flash(f"Error loading sample: {exc}", "danger")
                return redirect(url_for("index"))

    # Regular file upload
    if "datafile" not in request.files:
        flash("No file selected. Please choose a file to upload.", "warning")
        return redirect(url_for("index"))

    file = request.files["datafile"]
    if file.filename == "":
        flash("No file selected. Please choose a file to upload.", "warning")
        return redirect(url_for("index"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_name = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], saved_name)
        file.save(file_path)

        session_id = str(uuid.uuid4())
        try:
            df = processor.load_file(file_path)
            summary = processor.get_summary(df)
            dashboard_sessions[session_id] = {
                "file_path": file_path,
                "filename": filename,
                "summary": summary,
                "uploaded_at": datetime.now().isoformat(),
            }
            session["dashboard_id"] = session_id
            flash(f"File uploaded successfully: {filename}", "success")
            return redirect(url_for("configure", session_id=session_id))
        except Exception as exc:
            flash(f"Error processing file: {exc}", "danger")
            return redirect(url_for("index"))
    else:
        flash("Invalid file type. Please upload CSV, XLSX, or JSON files.", "danger")
        return redirect(url_for("index"))


@app.route("/configure/<session_id>")
def configure(session_id: str):
    """Dashboard configuration page - select charts, KPIs, layout."""
    if session_id not in dashboard_sessions:
        flash("Session expired. Please upload your data again.", "warning")
        return redirect(url_for("index"))

    sess = dashboard_sessions[session_id]
    templates = load_dashboard_templates()
    return render_template(
        "index.html",
        configure_mode=True,
        session_id=session_id,
        summary=sess["summary"],
        filename=sess["filename"],
        templates=templates,
        samples=load_sample_datasets(),
    )


@app.route("/dashboard/<session_id>", methods=["GET", "POST"])
def dashboard(session_id: str):
    """Render the interactive dashboard."""
    if session_id not in dashboard_sessions:
        flash("Session expired. Please upload your data again.", "warning")
        return redirect(url_for("index"))

    sess = dashboard_sessions[session_id]
    df = processor.load_file(sess["file_path"])

    # Determine which template to use
    template_file = request.form.get("template") or request.args.get("template")
    config = None
    if template_file:
        tpath = os.path.join(TEMPLATE_FOLDER, secure_filename(template_file))
        if os.path.exists(tpath):
            with open(tpath, "r", encoding="utf-8") as fh:
                config = json.load(fh)

    # Auto-detect configuration if no template selected
    if config is None:
        config = processor.auto_configure(df)

    # Calculate KPIs
    kpis = kpi_calc.calculate_all(df, config.get("kpis", []))

    # Generate charts
    charts = chart_gen.generate_all(df, config.get("charts", []))

    # Build filter options
    filters = processor.get_filter_options(df)

    return render_template(
        "dashboard.html",
        session_id=session_id,
        filename=sess["filename"],
        config=config,
        kpis=kpis,
        charts=charts,
        filters=filters,
        summary=sess["summary"],
        title=config.get("title", "Business Intelligence Dashboard"),
    )


# ---------------------------------------------------------------------------
# Routes - API Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/data/<session_id>")
def api_data(session_id: str):
    """Return raw data as JSON for client-side operations."""
    if session_id not in dashboard_sessions:
        return jsonify({"error": "Session not found"}), 404

    sess = dashboard_sessions[session_id]
    df = processor.load_file(sess["file_path"])

    # Apply optional filters from query params
    for col in df.columns:
        fval = request.args.get(f"filter_{col}")
        if fval:
            df = df[df[col].astype(str) == fval]

    limit = int(request.args.get("limit", 1000))
    offset = int(request.args.get("offset", 0))
    records = df.iloc[offset: offset + limit].to_dict(orient="records")

    return jsonify({
        "total": len(df),
        "limit": limit,
        "offset": offset,
        "columns": list(df.columns),
        "data": records,
    })


@app.route("/api/kpis/<session_id>")
def api_kpis(session_id: str):
    """Return KPI calculations as JSON."""
    if session_id not in dashboard_sessions:
        return jsonify({"error": "Session not found"}), 404

    sess = dashboard_sessions[session_id]
    df = processor.load_file(sess["file_path"])
    config = processor.auto_configure(df)
    kpis = kpi_calc.calculate_all(df, config.get("kpis", []))
    return jsonify({"kpis": kpis})


@app.route("/api/chart/<session_id>/<int:chart_index>")
def api_chart(session_id: str, chart_index: int):
    """Return a single chart's Plotly JSON."""
    if session_id not in dashboard_sessions:
        return jsonify({"error": "Session not found"}), 404

    sess = dashboard_sessions[session_id]
    df = processor.load_file(sess["file_path"])
    config = processor.auto_configure(df)
    charts_cfg = config.get("charts", [])

    if chart_index < 0 or chart_index >= len(charts_cfg):
        return jsonify({"error": "Chart index out of range"}), 404

    chart = chart_gen.generate_single(df, charts_cfg[chart_index])
    return jsonify(chart)


@app.route("/api/refresh/<session_id>", methods=["POST"])
def api_refresh(session_id: str):
    """Re-process data and return updated KPIs and charts."""
    if session_id not in dashboard_sessions:
        return jsonify({"error": "Session not found"}), 404

    sess = dashboard_sessions[session_id]
    df = processor.load_file(sess["file_path"])

    # Apply filters from request body
    filters = request.json.get("filters", {}) if request.is_json else {}
    for col, val in filters.items():
        if col in df.columns and val:
            df = df[df[col].astype(str) == str(val)]

    config = processor.auto_configure(df)
    kpis = kpi_calc.calculate_all(df, config.get("kpis", []))
    charts = chart_gen.generate_all(df, config.get("charts", []))

    return jsonify({"kpis": kpis, "charts": charts})


@app.route("/api/export/<session_id>")
def api_export(session_id: str):
    """Export dashboard configuration as JSON."""
    if session_id not in dashboard_sessions:
        return jsonify({"error": "Session not found"}), 404

    sess = dashboard_sessions[session_id]
    df = processor.load_file(sess["file_path"])
    config = processor.auto_configure(df)
    config["exported_at"] = datetime.now().isoformat()
    config["source_file"] = sess["filename"]
    return jsonify(config)


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return render_template("base.html", error="Page not found"), 404


@app.errorhandler(413)
def too_large(e):
    flash("File too large. Maximum size is 50 MB.", "danger")
    return redirect(url_for("index"))


@app.errorhandler(500)
def server_error(e):
    return render_template("base.html", error="Internal server error"), 500


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def create_app():
    """Application factory for external runners (gunicorn, pytest, etc.)."""
    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
