## Self-Healing Loop — Fehlgeschlagene Tests autonom beheben

Der Agent analysiert fehlgeschlagene Tests mit einem LLM, generiert einen SEARCH/REPLACE-Patch,
wendet ihn an und prüft das Ergebnis erneut — vollautomatisch.

---

### Voraussetzungen

> [!IMPORTANT]
> - Tests konfiguriert ([Rezept 09](09-first-test.md))
> - LLM-API konfiguriert ([Rezept 42](42-llm-routing.md)):
>   - `routing.json` mit Task `healing` eingetragen, **oder**
>   - `CLAUDE_API_ENABLED=true` in `.env`
> - `.env` angepasst ([Rezept 26](26-env-configuration.md)): `HEALING_MAX_ATTEMPTS`, `HEALING_RISK_MAX`

---

### Problem

Ein Eval-Test schlägt fehl. Du willst nicht manuell debuggen — der Agent soll den Fehler
selbst analysieren, einen Fix erzeugen, einspielen und erneut testen.

---

### Lösung: Manuell via --heal

```bash
cd ~/Gitea-Agent

# ──────────────────────────────────────────────────────────
# Option A: Letzten fehlgeschlagenen Test aus Eval heilen
# ──────────────────────────────────────────────────────────
python3 agent_start.py --heal

# → Agent liest letzten fehlgeschlagenen Test aus Eval-Ergebnissen
# → Startet Healing-Loop

# ──────────────────────────────────────────────────────────
# Option B: Bestimmten Test namentlich heilen
# ──────────────────────────────────────────────────────────
python3 agent_start.py --heal "Routing einfach"

# → Führt Eval gezielt für diesen Test aus
# → Startet Healing-Loop wenn Test fehlschlägt
```

**Typische Ausgabe:**

```
[Heal] Starte Self-Healing für Test: "Routing einfach"
[Heal] Versuch 1 / 3
[Eval] FAIL — Test: Routing einfach
       Erwartet: ["4"]
       Erhalten: "Das ist eine schwierige Frage"
[LLM]  Analysiere Fehler mit Task 'healing' (healer.md)...
[LLM]  Patch generiert:
       SEARCH: return "Das ist eine schwierige Frage"
       REPLACE: return calculate_result(prompt)
[Patch] Angewendet auf routing.py:142
[Eval]  PASS — Test: Routing einfach ✓
[Heal]  Erfolg nach 1 Versuch — Branch: heal/routing-einfach-20260328
[Gitea] Ergebnis als Issue-Kommentar gepostet
```

---

### Lösung: Automatisch via --watch

Im Watch-Modus wird Healing nach jedem fehlgeschlagenen Test automatisch ausgelöst
(sofern Risikostufe ≤ `HEALING_RISK_MAX`):

```bash
python3 agent_start.py --watch
```

```
[Watch] Zyklus 3 — 2026-03-28 02:00:00
[Eval]  FAIL — Score: 6.0 / 7.0
        Fehlgeschlagen: "Routing einfach"
[Heal]  Risiko: 1 — Starte Healing (HEALING_RISK_MAX=2)
[Heal]  Versuch 1 / 3 ...
[Heal]  PASS nach 1 Versuch ✓
[Watch] Nächster Lauf in 60 Minuten...
```

> [!TIP]
> Healing im Watch-Modus läuft nur wenn `HEALING_RISK_MAX` ≥ Risikostufe des fehlgeschlagenen Tests.
> Damit werden riskante Änderungen nachts nicht automatisch eingespielt.

---

### Erklärung

**Was passiert in jedem Loop-Durchlauf?**

1. **Eval:** Test wird ausgeführt — Ist-Ausgabe vs. erwartetem Keyword-Match
2. **LLM-Analyse:** Fehlerdetails (Test-Name, Ist-/Soll-Ausgabe, betroffene Codestelle)
   werden an das LLM mit dem System-Prompt `healer.md` geschickt (Task: `healing`)
3. **Patch generieren:** LLM antwortet mit einem SEARCH/REPLACE-Block
4. **Patch anwenden:** Agent ersetzt den Codeblock in der Zieldatei
5. **Eval wiederholen:** Test läuft erneut
6. **Abbruch oder nächster Versuch:**
   - PASS → Erfolg, weiter zu Schritt 7
   - FAIL → nächster Versuch (max. `HEALING_MAX_ATTEMPTS`)
7. **Branch & Bericht:** Temporärer Branch `heal/<testname>-<datum>` wird erstellt,
   Fix wird committed, Ergebnis als Kommentar am zugehörigen Gitea-Issue gepostet

**Wann gibt der Agent auf?**

- Alle `HEALING_MAX_ATTEMPTS` Versuche erschöpft ohne PASS
- Token-Budget (`HEALING_MAX_TOKENS`) überschritten
- Patch konnte nicht angewendet werden (SEARCH-Block nicht gefunden)
- Risikostufe des Tests > `HEALING_RISK_MAX`

**Welches LLM / Prompt wird verwendet?**

| Konfiguration | Wert |
|---|---|
| Task-Name in routing.json | `healing` |
| System-Prompt | `config/llm/prompts/healer.md` |
| Empfohlenes Modell | Starkes Modell (z.B. claude-sonnet-4-6) |
| Fallback | `default`-Provider aus routing.json |

---

### Healing-Verhalten in .env konfigurieren

```bash
# ~/Gitea-Agent/.env

# ══════════════════════════════════════════════════════════
# SELF-HEALING
# ══════════════════════════════════════════════════════════

# Maximale Anzahl Heilungs-Versuche pro Test (Standard: 3)
HEALING_MAX_ATTEMPTS=3

# Maximale Risikostufe für automatisches Healing
# 1 = nur Docs/Cleanup-Failures
# 2 = auch Performance-Regressions
# 3 = alle fehlgeschlagenen Tests (Vorsicht!)
HEALING_RISK_MAX=2

# Token-Budget pro Heilungs-Lauf (Abbruch bei Überschreitung)
HEALING_MAX_TOKENS=50000
```

**Per-Task LLM-Routing für Healing:**

```json
// config/llm/routing.json
{
    "tasks": {
        "healing": {
            "provider": "claude",
            "model": "claude-sonnet-4-6",
            "system_prompt": "config/llm/prompts/healer.md"
        }
    }
}
```

> [!TIP]
> Starkes Modell für `healing` wählen — Patch-Qualität entscheidet über Erfolg.
> Ein günstiges Modell spart Kosten, erzeugt aber häufiger fehlerhafte Patches.

---

### Best Practice

> [!TIP]
> **Healing erst testen, dann Watch aktivieren:**
> ```bash
> # Manuell prüfen ob Healing für dein Projekt funktioniert:
> python3 agent_start.py --heal "Testname"
> # → Bei Erfolg: HEALING_RISK_MAX im Watch-Modus freigeben
> ```

> [!TIP]
> **Konservativ starten:**
> ```bash
> # .env
> HEALING_MAX_ATTEMPTS=2   # Weniger Versuche = weniger Token-Verbrauch
> HEALING_RISK_MAX=1        # Nur unkritische Failures automatisch heilen
> ```

> [!TIP]
> **Healing-Ergebnisse im Gitea-Issue lesen:**
> ```
> [Heal] Versuch 1: FAIL — Patch konnte SEARCH-Block nicht finden
> [Heal] Versuch 2: PASS ✓ — Fix applied to routing.py:142
> Branch: heal/routing-einfach-20260328
> ```
> → Issue-Kommentar zeigt jeden Versuch mit Patch-Inhalt und Eval-Ergebnis.

> [!TIP]
> **Healing im Night-Modus kombinieren:**
> ```bash
> # Watch + automatisches Healing nur bei unkritischen Fehlern:
> # .env:
> HEALING_RISK_MAX=1
> NIGHT_MAX_RISK=1
> ```
> → Heilt Docs/Cleanup-Failures autonom, lässt kritische Regressions für manuelle Analyse.

---

### Warnung

> [!WARNING]
> **Healing verändert Code autonom:**
> ```
> Der Agent schreibt Patches direkt in deine Codebase.
> → Immer auf einem separaten Branch (heal/...)
> → Patches vor Merge reviewen
> → HEALING_RISK_MAX=3 nur in kontrollierten Umgebungen
> ```

> [!WARNING]
> **HEALING_MAX_ATTEMPTS zu hoch = hohe Kosten:**
> ```
> HEALING_MAX_ATTEMPTS=10
> → Bis zu 10 LLM-Aufrufe pro Test × Anzahl fehlgeschlagener Tests
> → Standard: 3 (ausreichend für die meisten Fälle)
> ```

> [!WARNING]
> **Ohne LLM-API kein Healing:**
> ```
> [Heal] SKIP — LLM-API nicht konfiguriert
> → CLAUDE_API_ENABLED=true in .env setzen
> → Oder routing.json mit Task 'healing' konfigurieren
> ```

> [!WARNING]
> **Patch nicht anwendbar — SEARCH-Block nicht gefunden:**
> ```
> [Heal] Versuch 1: ERROR — SEARCH-Block nicht in Datei gefunden
> → LLM hat falschen Kontext erhalten (z.B. Datei zu groß)
> → Skeleton + --get-slice für betroffene Datei prüfen
> → HEALING_MAX_TOKENS erhöhen falls Kontext abgeschnitten
> ```

---

### Nächste Schritte

✅ Self-Healing konfiguriert
→ [42 — LLM-Routing (Provider, Modelle)](42-llm-routing.md)
→ [26 — .env-Konfiguration (alle Felder)](26-env-configuration.md)
→ [09 — Ersten Eval-Test schreiben](09-first-test.md)
→ [14 — Watch-Modus mit tmux](14-watch-mode-tmux.md)
