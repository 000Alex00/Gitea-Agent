## Dashboard-Customization (HTML-Export)

Eval-Metriken als selbst-gehostetes Dashboard.

---

### Voraussetzungen

> [!IMPORTANT]
> - Watch-Modus läuft ([Rezept 14](14-watch-mode-tmux.md))
> - Webserver für Hosting (nginx, Apache, Python http.server)

---

### Problem

Score-History nur als JSON. Du willst: grafisches Dashboard mit Charts.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Schritt 1: Dashboard aktivieren
# ──────────────────────────────────────────────────────────
# ~/mein-projekt/config/dashboard.json

{
  "enabled": true,
  "output_dir": "data/dashboard",
  "update_interval": 3600,
  "charts": {
    "score_history": {
      "type": "line",
      "title": "Eval-Score-Verlauf",
      "y_axis": "Score",
      "x_axis": "Zeit"
    },
    "test_pass_rate": {
      "type": "bar",
      "title": "Test-Pass-Rate (Last 7 Days)",
      "y_axis": "Pass-Rate (%)"
    },
    "response_time": {
      "type": "line",
      "title": "Average Response Time",
      "y_axis": "Milliseconds"
    }
  },
  "tables": {
    "recent_failures": {
      "title": "Recent Test Failures",
      "columns": ["Test", "Failed At", "Error", "Issue"]
    }
  }
}

# ──────────────────────────────────────────────────────────
# Schritt 2: Dashboard generieren
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 dashboard.py \
  --project ~/mein-projekt \
  --config config/dashboard.json

# Output:
# [✓] Reading score_history.json
# [✓] Generating charts...
# [✓] Generating tables...
# [✓] Dashboard saved: ~/mein-projekt/data/dashboard/index.html

# ──────────────────────────────────────────────────────────
# Schritt 3: Dashboard hosten
# ──────────────────────────────────────────────────────────
# Option A: Python http.server
cd ~/mein-projekt/data/dashboard
python3 -m http.server 8080
# → http://localhost:8080

# Option B: nginx
sudo cp -r ~/mein-projekt/data/dashboard /var/www/html/agent-dashboard
sudo systemctl restart nginx
# → http://your-server/agent-dashboard

# Option C: Gitea Pages (falls aktiviert)
cd ~/mein-projekt
git add data/dashboard/
git commit -m "Update dashboard"
git push
# → https://gitea.example.com/user/repo/dashboard

# ──────────────────────────────────────────────────────────
# Schritt 4: Auto-Update im Watch-Modus
# ──────────────────────────────────────────────────────────
python3 agent_start.py \
  --project ~/mein-projekt \
  --watch \
  --dashboard-enabled

# Bei jedem Eval-Lauf:
# → score_history.json updated
# → dashboard.py regeneriert HTML
# → Dashboard zeigt neuste Daten
```

---

### Erklärung

**Dashboard-Struktur:**

```
data/dashboard/
├── index.html           # Haupt-Dashboard
├── assets/
│   ├── style.css        # Custom-Styling
│   ├── charts.js        # Chart-Logik (Chart.js)
│   └── data.json        # Exported Metrics
└── images/
    ├── score_history.png
    ├── pass_rate.png
    └── response_time.png
```

**Chart-Typen:**

### Line-Chart (Score-History):
```json
{
  "type": "line",
  "data": {
    "labels": ["2024-01-15 10:00", "2024-01-15 11:00", ...],
    "datasets": [{
      "label": "Score",
      "data": [8.0, 7.5, 8.0, 6.0, 8.0]
    }]
  }
}
```

### Bar-Chart (Test-Pass-Rate):
```json
{
  "type": "bar",
  "data": {
    "labels": ["RAG-Query", "Health-Check", "Context", ...],
    "datasets": [{
      "label": "Pass-Rate (%)",
      "data": [95, 100, 87, 92]
    }]
  }
}
```

### Table (Recent-Failures):
```html
<table>
  <tr>
    <th>Test</th><th>Failed At</th><th>Error</th><th>Issue</th>
  </tr>
  <tr>
    <td>RAG-Query</td>
    <td>2024-01-15 12:00</td>
    <td>Timeout</td>
    <td><a href="...">#100</a></td>
  </tr>
</table>
```

**Data-Export (data.json):**

```json
{
  "last_updated": "2024-01-15T14:30:00Z",
  "current_score": 8.0,
  "baseline": 8.0,
  "status": "PASS",
  "total_tests": 10,
  "passed_tests": 10,
  "failed_tests": 0,
  "score_history": [
    {"timestamp": "2024-01-15T10:00:00Z", "score": 8.0},
    {"timestamp": "2024-01-15T11:00:00Z", "score": 7.5}
  ],
  "test_details": [
    {
      "name": "RAG-Query",
      "status": "PASS",
      "last_run": "2024-01-15T14:30:00Z",
      "response_time_ms": 2345
    }
  ]
}
```

---

### Best Practice

> [!TIP]
> **Responsive Dashboard:**
> ```html
> <!-- index.html -->
> <!DOCTYPE html>
> <html>
> <head>
>   <meta name="viewport" content="width=device-width, initial-scale=1.0">
>   <link rel="stylesheet" href="assets/style.css">
> </head>
> <body>
>   <div class="container">
>     <h1>Agent Dashboard</h1>
>     <canvas id="scoreChart"></canvas>
>   </div>
>   <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
>   <script src="assets/charts.js"></script>
> </body>
> </html>
> ```

> [!TIP]
> **Dark-Mode Toggle:**
> ```css
> @media (prefers-color-scheme: dark) {
>   body {
>     background: #1e1e1e;
>     color: #d4d4d4;
>   }
> }
> ```

> [!TIP]
> **Auto-Refresh:**
> ```html
> <meta http-equiv="refresh" content="300">
> <!-- Refresh alle 5 Minuten -->
> ```

---

### Warnung

> [!WARNING]
> **Sensitive Daten im Dashboard:**
> ```json
> {
>   "test_details": [
>     {
>       "name": "Auth-Test",
>       "error": "Token abc123 invalid"  // ← Token exposed
>     }
>   ]
> }
> ```
> → Error-Messages sanieren vor Export

> [!WARNING]
> **Dashboard ohne Auth:**
> ```
> http://public-server/agent-dashboard
> → Jeder kann Metriken sehen
> ```
> → nginx Basic-Auth oder VPN nutzen

> [!WARNING]
> **Große score_history.json:**
> ```json
> {
>   "score_history": [
>     /* 10.000 Entries */
>   ]
> }
> ```
> → Browser-Performance leidet
> → Nur letzte 500 Entries exportieren

---

### Nächste Schritte

✅ Dashboard deployed  
→ [12 — Performance-Tests](12-performance-tests.md)  
→ [18 — Tag-Aggregation](18-tag-aggregation.md)  
→ [40 — Best Practices](40-best-practices.md)
