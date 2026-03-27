## config/project.json — Projekt-Typ und Feature-Flags

Vollständige Referenz für `config/project.json`.

---

### Voraussetzungen

> [!IMPORTANT]
> - Basis-Setup durchgeführt ([Rezept 02](02-first-setup.md))
> - Setup Wizard Schritt 7 erstellt `config/project.json` automatisch — oder die Datei wurde manuell angelegt

---

### Problem

Du willst wissen: welche Feature-Flags gibt es? Was ist per Projekt-Typ standardmäßig aktiv? Wie aktiviert oder deaktiviert man ein Feature nach dem Setup?

---

### Lösung

**Vollständige Struktur `<project_root>/config/project.json`:**

```json
{
    "type": "llm_chat",
    "features": {
        "eval": true,
        "health_checks": true,
        "auto_issues": true,
        "changelog": true,
        "watch": true,
        "pr_workflow": true
    }
}
```

**Feature manuell deaktivieren (Beispiel: `auto_issues`):**

```bash
# Direkt in der Datei editieren
nano <project_root>/config/project.json

# Feld auf false setzen:
# "auto_issues": false

# Kein Neustart nötig — Änderung wirkt beim nächsten Agent-Aufruf
```

**Datei manuell anlegen (ohne Wizard):**

```bash
cat > <project_root>/config/project.json << 'EOF'
{
    "type": "llm_chat",
    "features": {
        "eval": true,
        "health_checks": true,
        "auto_issues": true,
        "changelog": true,
        "watch": true,
        "pr_workflow": true
    }
}
EOF
```

---

### Erklärung

**Projekt-Typen:**

| type | Beschreibung |
|------|-------------|
| `web_api` | REST/GraphQL-Backend |
| `llm_chat` | Chat-Interface / LLM-Integration |
| `voice_assistant` | Sprach-basierte Anwendung |
| `iot` | Hardware / Sensor-Projekte |
| `cli_tool` | Kommandozeilen-Tool |
| `library` | Bibliothek / Package |
| `custom` | Alle Features starten deaktiviert, individuelle Auswahl |

---

**Feature-Flags und ihre Bedeutung:**

| Feature | Beschreibung | Abhängigkeit |
|---------|-------------|--------------|
| `eval` | Bewertet Server-Antworten automatisch | benötigt `server_url` in `agent_eval.json` |
| `health_checks` | Prüft ob Server erreichbar ist | benötigt `server_url` |
| `auto_issues` | Erstellt Issues bei Testfehlern automatisch | benötigt `eval: true` |
| `changelog` | Generiert `CHANGELOG.md` aus Commits | — |
| `watch` | Überwacht Gitea auf neue Issues | — |
| `pr_workflow` | Erstellt PRs nach Implementierung automatisch | — |

---

**Feature-Defaults nach Projekt-Typ:**

| Feature | web_api | llm_chat | voice_assistant | iot | cli_tool | library | custom |
|---------|:-------:|:--------:|:---------------:|:---:|:--------:|:-------:|:------:|
| `eval` | ✓ | ✓ | ✓ | — | ✓ | — | — |
| `health_checks` | ✓ | ✓ | ✓ | ✓ | — | — | — |
| `auto_issues` | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| `changelog` | ✓ | ✓ | — | — | ✓ | ✓ | — |
| `watch` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| `pr_workflow` | ✓ | ✓ | — | — | ✓ | ✓ | — |

> Der Wizard setzt diese Defaults automatisch in Schritt 7. Bei `custom` startet alles deaktiviert.

---

**Abhängigkeiten zwischen Features:**

```
server_url (in agent_eval.json)
    ├── eval
    │     └── auto_issues
    └── health_checks
```

- `auto_issues` ohne `eval: true` → kein Effekt, Issues werden nie erstellt
- `eval` ohne `server_url` → Eval-Schritt schlägt fehl, Feature wird übersprungen
- `health_checks` ohne `server_url` → Health-Check gibt immer "unreachable" zurück

---

**Was passiert wenn ein Feature deaktiviert ist:**

| Feature deaktiviert | Verhalten |
|--------------------|-----------|
| `eval: false` | Kein automatischer Test-Lauf, `auto_issues` hat keinen Effekt |
| `health_checks: false` | Server-Status wird nicht geprüft, kein Health-Issue |
| `auto_issues: false` | Testfehler werden geloggt, aber kein Gitea-Issue erstellt |
| `changelog: false` | `CHANGELOG.md` wird nicht aktualisiert |
| `watch: false` | Agent reagiert nicht auf neue Issues in Gitea |
| `pr_workflow: false` | Nach Implementierung kein automatischer PR, Branch bleibt offen |

---

### Best Practice

> [!TIP]
> **`custom` Typ für experimentelle Projekte:**
> ```json
> {
>     "type": "custom",
>     "features": {
>         "watch": true,
>         "changelog": true
>     }
> }
> ```
> Nur die gewünschten Features aktivieren — alle anderen bleiben aus.

> [!TIP]
> **Feature-Flags sind hot-reload-fähig:**
> ```bash
> # Kein Neustart des Agents nötig
> # Änderung in project.json → wirkt beim nächsten --run / --watch-Zyklus
> ```

> [!TIP]
> **Datei in Git versionieren:**
> ```bash
> git add config/project.json
> git commit -m "chore: project type llm_chat, all features enabled"
> # Keine Secrets enthalten — sicher zu committen
> ```

---

### Warnung

> [!WARNING]
> **`auto_issues` ohne `eval`:**
> ```
> "eval": false,
> "auto_issues": true   ← hat keinen Effekt
> ```
> `auto_issues` benötigt `eval: true` als Voraussetzung. Ohne Eval werden keine Testergebnisse erzeugt, aus denen Issues entstehen könnten.

> [!WARNING]
> **`eval` ohne `server_url` in agent_eval.json:**
> ```
> "eval": true  ← aktiviert
> agent_eval.json → kein "server_url" Feld
> → Eval-Schritt bricht mit Konfigurationsfehler ab
> ```
> Vor Aktivierung von `eval` oder `health_checks`: `server_url` in `config/agent_eval.json` eintragen.

> [!WARNING]
> **`type` nachträglich ändern:**
> ```
> Setup mit type: "web_api" → Features automatisch gesetzt
> Manuell auf type: "library" ändern → Features werden NICHT automatisch angepasst
> ```
> Den `type` zu ändern passt die Feature-Defaults nicht rückwirkend an. Features müssen manuell auf den gewünschten Stand gesetzt werden.

---

### Nächste Schritte

Datei `config/project.json` verstanden
→ [02 — Erst-Setup und Wizard](02-first-setup.md) (Schritt 7: Projekt-Typ wählen)
→ [27 — agent_eval.json-Referenz](27-eval-json-reference.md) (`server_url` und Eval-Konfiguration)
→ [04 — Health-Check](04-health-check.md) (`health_checks` Feature in Aktion)
→ [26 — .env-Konfiguration](26-env-configuration.md) (ergänzende Umgebungsvariablen)
