import datetime
import json
import os
from pathlib import Path

import evaluation
import settings

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="60">
    <title>Gitea Agent Live-Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; color: #333; }
        .container { max-width: 1200px; margin: auto; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .header h1 { margin: 0; }
        .status-bar { display: flex; gap: 20px; }
        .status-badge { padding: 8px 16px; border-radius: 4px; font-weight: bold; color: white; }
        .bg-success { background-color: #28a745; }
        .bg-danger { background-color: #dc3545; }
        .bg-warning { background-color: #ffc107; color: #333; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        .text-muted { color: #6c757d; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Agent Live-Dashboard</h1>
            <div class="status-bar">
                <div class="status-badge {SERVER_CLASS}">Server: {SERVER_STATUS}</div>
                <div class="status-badge {PI5_CLASS}">Pi5: {PI5_STATUS}</div>
            </div>
        </div>

        <div class="card">
            <h2>Score-Verlauf (Letzte 24h)</h2>
            <canvas id="scoreChart" height="80"></canvas>
        </div>

        <div style="display: flex; gap: 20px;">
            <div class="card" style="flex: 1;">
                <h2>Letzte Evaluierungen</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Zeitpunkt</th>
                            <th>Trigger</th>
                            <th>Score</th>
                            <th>Ergebnis</th>
                        </tr>
                    </thead>
                    <tbody>
                        {RECENT_RUNS}
                    </tbody>
                </table>
            </div>

            <div class="card" style="flex: 1;">
                <h2>Letzte 5 Fehler</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Test</th>
                            <th>Tag</th>
                            <th>Grund</th>
                        </tr>
                    </thead>
                    <tbody>
                        {RECENT_ERRORS}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <h2>Tag-Aggregation (Letzte 7 Tage)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Tag</th>
                        <th>Fehlschläge</th>
                    </tr>
                </thead>
                <tbody>
                    {TAG_AGGREGATION}
                </tbody>
            </table>
        </div>
        <p class="text-muted">Zuletzt aktualisiert: {LAST_UPDATE}</p>
    </div>

    <script>
        const ctx = document.getElementById('scoreChart').getContext('2d');
        const scoreChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: {CHART_LABELS},
                datasets: [{
                    label: 'Score',
                    data: {CHART_DATA},
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    fill: false
                },
                {
                    label: 'Baseline',
                    data: {CHART_BASELINE},
                    borderColor: 'rgb(255, 99, 132)',
                    borderDash: [5, 5],
                    tension: 0,
                    fill: false
                }]
            },
            options: {
                scales: {
                    y: { beginAtZero: true, suggestedMax: {CHART_MAX} }
                }
            }
        });
    </script>
</body>
</html>
"""


def generate(project_root: Path):
    cfg = evaluation._load_config(project_root) or {}
    server_url = cfg.get("server_url", "")
    pi5_url = cfg.get("pi5_url", "")

    server_ok = evaluation._ping(server_url) if server_url else False
    pi5_ok = evaluation._ping(pi5_url) if pi5_url else False

    hist_path = evaluation._resolve_path(
        project_root, "score_history.json", evaluation.SCORE_HISTORY
    )
    history = []
    if hist_path.exists():
        try:
            with hist_path.open(encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            pass

    now = datetime.datetime.now()

    chart_labels = []
    chart_data = []
    chart_baseline = []
    max_score = 1

    last_24h = now - datetime.timedelta(hours=24)
    last_7d = now - datetime.timedelta(days=7)

    recent_errors_html = ""
    recent_runs_html = ""
    tag_counts = {}

    error_count = 0
    runs_count = 0

    for entry in reversed(history):
        ts_str = entry.get("timestamp", "")
        try:
            ts = datetime.datetime.fromisoformat(ts_str)
        except ValueError:
            continue

        if runs_count < 5:
            score = entry.get("score", 0)
            ms = entry.get("max_score", 0)
            trigger = entry.get("trigger", "-")
            passed = "✅" if entry.get("passed") else "❌"
            recent_runs_html += f"<tr><td>{ts.strftime('%H:%M:%S %d.%m')}</td><td>{trigger}</td><td>{score}/{ms}</td><td>{passed}</td></tr>"
            runs_count += 1

        for f in entry.get("failed", []):
            if error_count < 5:
                tag = f.get("tag", "")
                name = f.get("name", "")
                reason = str(f.get("reason", ""))[:50]
                recent_errors_html += f"<tr><td>{name}</td><td><span class='status-badge bg-warning'>{tag}</span></td><td>{reason}</td></tr>"
                error_count += 1

            if ts >= last_7d:
                tag = f.get("tag", "")
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

    for entry in history:
        ts_str = entry.get("timestamp", "")
        try:
            ts = datetime.datetime.fromisoformat(ts_str)
        except ValueError:
            continue
        if ts >= last_24h:
            chart_labels.append(ts.strftime("%H:%M"))
            chart_data.append(entry.get("score", 0))
            chart_baseline.append(entry.get("baseline", 0))
            if entry.get("max_score", 0) > max_score:
                max_score = entry.get("max_score", 0)

    tag_html = ""
    for tag, count in sorted(
        tag_counts.items(), key=lambda item: item[1], reverse=True
    ):
        tag_html += f"<tr><td>{tag}</td><td>{count}</td></tr>"

    if not recent_errors_html:
        recent_errors_html = (
            "<tr><td colspan='3'>Keine Fehler in der Historie.</td></tr>"
        )
    if not recent_runs_html:
        recent_runs_html = (
            "<tr><td colspan='4'>Keine Evaluierungen in der Historie.</td></tr>"
        )
    if not tag_html:
        tag_html = (
            "<tr><td colspan='2'>Keine Tag-Fehler in den letzten 7 Tagen.</td></tr>"
        )

    html = HTML_TEMPLATE.replace(
        "{SERVER_STATUS}", "Online" if server_ok else "Offline"
    )
    html = html.replace("{SERVER_CLASS}", "bg-success" if server_ok else "bg-danger")
    html = html.replace(
        "{PI5_STATUS}", "Online" if pi5_ok else ("Offline" if pi5_url else "N/A")
    )
    html = html.replace(
        "{PI5_CLASS}",
        "bg-success" if pi5_ok else ("bg-danger" if pi5_url else "bg-warning"),
    )
    html = html.replace("{CHART_LABELS}", json.dumps(chart_labels))
    html = html.replace("{CHART_DATA}", json.dumps(chart_data))
    html = html.replace("{CHART_BASELINE}", json.dumps(chart_baseline))
    html = html.replace("{CHART_MAX}", str(max_score))
    html = html.replace("{RECENT_RUNS}", recent_runs_html)
    html = html.replace("{RECENT_ERRORS}", recent_errors_html)
    html = html.replace("{TAG_AGGREGATION}", tag_html)
    html = html.replace("{LAST_UPDATE}", now.strftime("%H:%M:%S %d.%m.%Y"))

    dash_path = project_root / getattr(settings, "DASHBOARD_PATH", "dashboard.html")
    dash_path.write_text(html, encoding="utf-8")

    local_path = Path(__file__).parent / "dashboard.html"
    if dash_path.resolve() != local_path.resolve():
        local_path.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    generate(Path(os.environ.get("PROJECT_ROOT", ".")))
