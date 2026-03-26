## Zwei Repos — Ein Agent (--self)

Agent auf sich selbst anwenden + normales Projekt parallel betreiben.

---

### Voraussetzungen

> [!IMPORTANT]
> - gitea-agent installiert ([Rezept 01](01-installation.md))
> - Gitea-Repository für gitea-agent selbst existiert
> - Normales Projekt bereits eingerichtet

---

### Problem

Du willst den gitea-agent weiterentwickeln UND gleichzeitig für dein Projekt nutzen. Du brauchst zwei getrennte Konfigurationen.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Setup: Zwei .env-Dateien erstellen
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent

# .env → normales Projekt
cat > .env << 'EOF'
GITEA_URL=http://localhost:3000
GITEA_USER=admin
GITEA_TOKEN=abc123...
GITEA_REPO=admin/mein-projekt
PROJECT_ROOT=/home/user/mein-projekt
EOF

# .env.agent → gitea-agent selbst
cat > .env.agent << 'EOF'
GITEA_URL=http://localhost:3000
GITEA_USER=admin
GITEA_TOKEN=abc123...
GITEA_REPO=admin/gitea-agent
PROJECT_ROOT=/home/user/Gitea-Agent
CONTEXT_DIR=/home/user/Gitea-Agent/workspace
EOF

# ──────────────────────────────────────────────────────────
# Normales Projekt (Standard):
# ──────────────────────────────────────────────────────────
python3 agent_start.py --issue 21
# → Verwendet .env (mein-projekt)

# ──────────────────────────────────────────────────────────
# Agent-Eigenentwicklung (--self):
# ──────────────────────────────────────────────────────────
python3 agent_start.py --self --issue 42
# → Verwendet .env.agent (gitea-agent)

python3 agent_start.py --self --implement 42
python3 agent_start.py --self --pr 42 --branch feat/... --summary "..."

# ──────────────────────────────────────────────────────────
# Kontext-Export für Agent-Issues:
# ──────────────────────────────────────────────────────────
./scripts/context_export.sh 42 --self
# → Exportiert Kontext aus gitea-agent, nicht mein-projekt
```

---

### Erklärung

**Wie funktioniert --self?**
1. `AGENT_ENV_FILE=".env.agent"` wird gesetzt
2. `settings.py` liest `.env.agent` statt `.env`
3. Alle Befehle arbeiten auf gitea-agent-Repository

**Verzeichnisstruktur:**
```
~/Gitea-Agent/
    .env                    ← normales Projekt
    .env.agent              ← agent selbst
    agent_start.py
    workspace/              ← mixed (beide Projekte)
        open/21-enhancement/   ← mein-projekt
        open/42-feature/       ← gitea-agent (mit --self)

~/mein-projekt/
    config/
    data/
```

**Wann verwenden?**
- Agent-Bugs fixen während Projekt-Arbeit
- Agent-Features entwickeln
- Agent-Tests schreiben

---

### Best Practice

> [!TIP]
> **Alias für --self:**
> ```bash
> # In ~/.bashrc
> alias agent="python3 ~/Gitea-Agent/agent_start.py"
> alias agent-self="python3 ~/Gitea-Agent/agent_start.py --self"
> 
> # Dann:
> agent --issue 21        # normales Projekt
> agent-self --issue 42   # gitea-agent
> ```

> [!TIP]
> **Projekt-Check:**
> ```bash
> python3 agent_start.py --doctor
> # → PROJECT_ROOT: /home/user/mein-projekt
> 
> python3 agent_start.py --self --doctor
# → PROJECT_ROOT: /home/user/Gitea-Agent
> ```

> [!TIP]
> **Zwei Watch-Modi parallel:**
> ```bash
> # Terminal 1:
> tmux new -s agent-projekt
> python3 agent_start.py --watch
> 
> # Terminal 2:
> tmux new -s agent-self
> python3 agent_start.py --self --watch --patch
> ```

---

### Warnung

> [!WARNING]
> **.env.agent muss im Agent-Root liegen:**
> ```
> ~/Gitea-Agent/.env.agent  ✅
> ~/mein-projekt/.env.agent ❌
> ```

> [!WARNING]
> **PROJECT_ROOT darf nicht identisch sein:**
> ```bash
> # .env
> PROJECT_ROOT=/home/user/Gitea-Agent  ❌ Kollision!
> 
> # .env.agent
> PROJECT_ROOT=/home/user/Gitea-Agent  ❌ Gleicher Pfad!
> 
> # Korrekt:
> # .env → /home/user/mein-projekt
> # .env.agent → /home/user/Gitea-Agent
> ```

> [!WARNING]
> **--self vergessen:**
> ```bash
> python3 agent_start.py --issue 42
> # → Arbeitet auf mein-projekt, nicht gitea-agent!
> # Immer --self für Agent-Issues verwenden
> ```

---

### Nächste Schritte

✅ Dual-Repo-Setup aktiv  
→ [08 — Manueller Workflow](08-manual-workflow.md)  
→ [26 — .env verstehen](26-env-configuration.md)
