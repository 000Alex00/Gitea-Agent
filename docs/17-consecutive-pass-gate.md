## Consecutive-Pass-Gate (close_after_consecutive_passes)

Issue erst nach N erfolgreichen Eval-Läufen schließen.

---

### Voraussetzungen

> [!IMPORTANT]
> - Watch-Modus aktiv ([Rezept 14](14-watch-mode-tmux.md))
> - Eval konfiguriert ([Rezept 09](09-first-test.md))

---

### Problem

Ein Test fläkert (mal PASS, mal FAIL). Agent öffnet/schließt Issues im Loop. Du willst Stabilität: erst nach X erfolgreichen Läufen schließen.

---

### Lösung

```json
{
  "server_url": "http://localhost:8000",
  "chat_endpoint": "/chat",
  "close_after_consecutive_passes": 3,
  "tests": [
    {
      "name": "Netzwerk-Query",
      "message": "Wetter in Berlin?",
      "expected_keywords": ["Berlin", "Wetter"],
      "weight": 1,
      "tag": "network"
    }
  ]
}
```

**Watch-Modus Verhalten:**

```bash
cd ~/Gitea-Agent
python3 agent_start.py \
  --project ~/mein-projekt \
  --watch \
  --eval-interval 1800

# ──────────────────────────────────────────────────────────
# Szenario: Fläkernder Test
# ──────────────────────────────────────────────────────────
# Run 1 (00:00): Score 0/1 → Issue #45 erstellt
# Run 2 (00:30): Score 1/1 → Pass-Counter: 1
# Run 3 (01:00): Score 0/1 → Pass-Counter: RESET → 0
# Run 4 (01:30): Score 1/1 → Pass-Counter: 1
# Run 5 (02:00): Score 1/1 → Pass-Counter: 2
# Run 6 (02:30): Score 1/1 → Pass-Counter: 3 → Issue #45 geschlossen

# ──────────────────────────────────────────────────────────
# Ohne Gate (Standard: close_after_consecutive_passes = 1):
# ──────────────────────────────────────────────────────────
# Run 1: FAIL → Issue #45 eröffnet
# Run 2: PASS → Issue #45 geschlossen
# Run 3: FAIL → Issue #45 wieder eröffnet (reopen)
# Run 4: PASS → Issue #45 wieder geschlossen
# → Spam im Issue-Tracker
```

---

### Erklärung

**Pass-Counter Logik:**

```python
# agent_start.py (vereinfacht)
consecutive_passes = 0

while watch_mode:
    score = run_evaluation()
    
    if score >= baseline:
        consecutive_passes += 1
        if consecutive_passes >= close_after_consecutive_passes:
            close_issue()
            consecutive_passes = 0
    else:
        consecutive_passes = 0  # RESET bei Fehler
        reopen_issue()
    
    time.sleep(eval_interval)
```

**Gate-Werte:**

| Wert | Use-Case |
|------|----------|
| `1` | Standard (sofort schließen bei PASS) |
| `2` | Moderate Stabilität (2× PASS erforderlich) |
| `3` | Hohe Stabilität (Night-Modus, kritische Repos) |
| `5+` | Extreme Paranoia (flaky externe APIs) |

**Issue-Kommentare:**

```markdown
# Issue #45: Test "Netzwerk-Query" fehlschlägt

## Agent-Kommentar (Run 2):
✓ Eval-Lauf bestanden (Score: 1.0 / 1.0)
Pass-Counter: 1 / 3

## Agent-Kommentar (Run 3):
✗ Eval-Lauf fehlgeschlagen (Score: 0.0 / 1.0)
Pass-Counter zurückgesetzt: 1 → 0

## Agent-Kommentar (Run 6):
✓ Eval-Lauf bestanden (Score: 1.0 / 1.0)
Pass-Counter: 3 / 3 → Issue wird geschlossen
```

---

### Best Practice

> [!TIP]
> **Gate je nach Kritikalität:**
> ```json
> {
>   "tests": [
>     {"name": "Critical-API", "tag": "critical", "...": "..."},
>     {"name": "Nice-to-have", "tag": "optional", "...": "..."}
>   ],
>   "close_after_consecutive_passes": 3
> }
> ```
> → Gate gilt für **alle** Tests global

> [!TIP]
> **Night-Modus Gate:**
> ```bash
> # .env oder agent_eval.json
> NIGHT_MODE_CONSECUTIVE_PASSES=3
> PATCH_MODE_CONSECUTIVE_PASSES=2
> ```

> [!TIP]
> **Logging beobachten:**
> ```bash
> tail -f ~/mein-projekt/data/*.log
> # [2024-01-15 02:00] Pass-Counter: 1 / 3
> # [2024-01-15 02:30] Pass-Counter: 2 / 3
> # [2024-01-15 03:00] Pass-Counter: 3 / 3 → Close
> ```

---

### Warnung

> [!WARNING]
> **Gate zu hoch = Issues nie geschlossen:**
> ```json
> {"close_after_consecutive_passes": 10}
> ```
> → Bei eval_interval=1800 (30 Min) = 5 Stunden Wartezeit
> → Issue bleibt tagelang offen bei gelegentlichen Flakes

> [!WARNING]
> **Gate zu niedrig = Flappy-Issues:**
> ```json
> {"close_after_consecutive_passes": 1}
> ```
> → Ein zufälliger PASS schließt Issue
> → Nächster Run: FAIL → Issue reopen
> → Spam

> [!WARNING]
> **Externe API-Abhängigkeiten:**
> ```
> Test: "Wetter-API abrufen"
> → API down 2/10 Runs
> → Gate=3 funktioniert nicht
> ```
> → Externe Calls mocken oder höheres Gate (5+)

---

### Nächste Schritte

✅ Consecutive-Pass-Gate konfiguriert  
→ [18 — Tag-Aggregation](18-tag-aggregation.md)  
→ [16 — Night vs Patch Modus](16-night-vs-patch.md)  
→ [36 — Watch-Modus Crashes](36-watch-mode-crashes.md)
