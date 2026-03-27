## LLM-Routing — Provider, Modelle und Fallback konfigurieren

Der Agent ist LLM-agnostisch. Welcher Provider und welches Modell verwendet wird,
ist jederzeit änderbar — ohne Setup-Neustart.

---

### Voraussetzungen

> [!IMPORTANT]
> - gitea-agent eingerichtet ([Rezept 02](02-first-setup.md))
> - API-Key des gewünschten Providers in `.env` eingetragen

---

### Problem

Du willst den LLM-Provider wechseln, per-Task unterschiedliche Modelle nutzen
oder eine Fallback-Kette für den Fall einrichten, dass ein Provider nicht erreichbar ist.

---

### Lösung: Interaktiver --llm Wizard

```bash
cd ~/Gitea-Agent
python3 agent_start.py --llm
```

```
╔════════════════════════════════════════════════════════════════╗
║  LLM-Konfiguration — gitea-agent                               ║
╠════════════════════════════════════════════════════════════════╣
║  Verwalte Provider, Modelle und Fallback-Kette.                ║
║  Datei: config/llm/routing.json                                ║
║                                                                ║
║  Änderungen wirken sofort — kein Setup-Neustart nötig.         ║
╚════════════════════════════════════════════════════════════════╝

  Aktuelle Konfiguration:
  Standard:  claude / claude-sonnet-4-6
  Fallback:  claude → openai → local

  [1] Standard-Provider / Modell ändern
  [2] Per-Task Routing konfigurieren
  [3] Fallback-Kette konfigurieren
  [4] Konnektivität testen
  [5] Beenden
```

---

### Menü [1] — Standard-Provider / Modell ändern

```bash
  Auswahl: 1

  Aktuell: claude / claude-sonnet-4-6

  Standard-Anbieter (claude/openai/gemini/deepseek/local) [claude]: openai
  Bekannte Modelle:
    • gpt-4o
    • gpt-4o-mini
    • gpt-4-turbo

  Standard-Modell [gpt-4o-mini]: gpt-4o

  ⚠️  Nicht vergessen: OPENAI_API_KEY=... in .env eintragen

  ✅ Standard-Konfiguration gespeichert.
```

**Unterstützte Provider:**

| Provider   | Env-Variable         | Modell-Beispiele                                        |
|------------|----------------------|---------------------------------------------------------|
| `claude`   | `ANTHROPIC_API_KEY`  | claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5-* |
| `openai`   | `OPENAI_API_KEY`     | gpt-4o, gpt-4o-mini, gpt-4-turbo                        |
| `gemini`   | `GEMINI_API_KEY`     | gemini-1.5-pro, gemini-1.5-flash                        |
| `deepseek` | `DEEPSEEK_API_KEY`   | deepseek-chat, deepseek-coder                           |
| `local`    | *(kein Key nötig)*   | llama3, mistral, phi3, codellama (via Ollama)           |

---

### Menü [2] — Per-Task Routing

Verschiedene Aufgaben können unterschiedliche Provider/Modelle nutzen —
z.B. günstiges Modell für Analyse, starkes Modell für Implementierung:

```bash
  Auswahl: 2

  ── Issue-Analyse
    Anbieter [claude]: claude
    Modell [claude-haiku-4-5-20251001]: claude-haiku-4-5-20251001

  ── Implementierung
    Anbieter [claude]: claude
    Modell [claude-sonnet-4-6]: claude-sonnet-4-6

  ── PR-Review
    Anbieter [claude]: claude
    Modell [claude-sonnet-4-6]:

  ── Test-Generierung
    Anbieter [claude]: local
    Modell [claude-sonnet-4-6]: llama3
    Base-URL [http://localhost:11434]:

  ── Log-Analyse
    Anbieter [claude]: claude
    Modell [claude-haiku-4-5-20251001]:

  ── Self-Healing
    Anbieter [claude]: claude
    Modell [claude-sonnet-4-6]:

  ✅ Task-Routing gespeichert.
```

**Verfügbare Task-Typen:**

| Task               | Beschreibung                              | Empfehlung               |
|--------------------|-------------------------------------------|--------------------------|
| `issue_analysis`   | Issue lesen + Plan vorschlagen            | Günstig (haiku, mini)    |
| `implementation`   | Code schreiben                            | Stark (sonnet, gpt-4o)   |
| `pr_review`        | Pull Request reviewen                     | Stark                    |
| `test_generation`  | Tests generieren                          | Lokal möglich            |
| `log_analysis`     | Log-Muster erkennen                       | Günstig                  |
| `healing`          | Selbstheilung: Fehler autonom beheben     | Stark                    |

---

### Menü [3] — Fallback-Kette

Wenn ein Provider nicht erreichbar ist (Limit, Ausfall, kein API-Key),
wechselt der Agent automatisch zum nächsten:

```bash
  Auswahl: 3

  Aktuelle Fallback-Kette: (keine)
  Eingabe: Anbieter leerzeichen-getrennt, z.B.: claude openai local

  Fallback-Kette: claude openai local

  ✅ Fallback: claude → openai → local
```

---

### Menü [4] — Konnektivität testen

```bash
  Auswahl: 4

  Teste claude / claude-sonnet-4-6 ...
  ✅ Verbindung OK — Antwort: OK
```

---

### routing.json direkt bearbeiten

Die Konfigurationsdatei liegt in `~/Gitea-Agent/config/llm/routing.json`:

```json
{
    "_comment": "LLM-Routing — Erweitern: --llm",
    "default": {
        "provider": "claude",
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "timeout": 60
    },
    "fallback_chain": ["claude", "openai", "local"],
    "tasks": {
        "issue_analysis": {
            "provider": "claude",
            "model": "claude-haiku-4-5-20251001",
            "system_prompt": "config/llm/prompts/analyst.md"
        },
        "implementation": {
            "provider": "claude",
            "model": "claude-sonnet-4-6",
            "system_prompt": "config/llm/prompts/senior_python.md"
        },
        "test_generation": {
            "provider": "local",
            "model": "llama3",
            "base_url": "http://localhost:11434",
            "system_prompt": "config/llm/prompts/senior_python.md"
        }
    }
}
```

> [!TIP]
> Fehlende Task-Einträge verwenden automatisch den `default`-Provider.

---

### API-Keys in .env eintragen

```bash
# ~/Gitea-Agent/.env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AI...
DEEPSEEK_API_KEY=sk-...
```

> [!WARNING]
> `.env` niemals in git einchecken — sie ist bereits in `.gitignore`.

---

### Best Practice

> [!TIP]
> **Lokales Modell als Fallback:**
> ```
> Fallback-Kette: claude local
> ```
> → Bei Claude-Ausfall oder Limit läuft der Agent mit Ollama weiter.

> [!TIP]
> **Günstiges Modell für schnelle Tasks:**
> ```
> issue_analysis  → claude-haiku  (10× günstiger als sonnet)
> log_analysis    → claude-haiku
> implementation  → claude-sonnet (volle Stärke wo nötig)
> ```

> [!TIP]
> **Provider wechseln ohne Setup-Neustart:**
> ```bash
> python3 agent_start.py --llm
> # → [1] Standard-Provider ändern → sofort aktiv
> ```

---

### Nächste Schritte

✅ LLM-Routing konfiguriert
→ [04 — Health-Check](04-health-check.md)
→ [38 — CLI-Referenz](38-cli-reference.md)
