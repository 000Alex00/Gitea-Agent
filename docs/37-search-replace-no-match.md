## Search-Replace No-Match debuggen

Whitespace, CRLF, Encoding-Probleme.

---

### Voraussetzungen

> [!IMPORTANT]
> - Search-Replace-Patches verstanden ([Rezept 23](23-search-replace-patches.md))
> - Patch schlägt fehl

---

### Problem

Agent generiert Patch, aber "No match found". Code sieht identisch aus.

---

### Lösung

```bash
# ══════════════════════════════════════════════════════════
# Problem 1: Trailing Whitespace
# ══════════════════════════════════════════════════════════
# Patch:
SEARCH = "def process(msg):\n    return msg"
# File:
# "def process(msg):\n    return msg  "  ← 2 Spaces am Ende

# Debugging:
cat -A src/api.py | grep "def process"
# def process(msg):$
#     return msg  $  ← sichtbare Spaces

# Lösung:
# agent_start.py: Whitespace normalisieren
def normalize_whitespace(text):
    return "\n".join(line.rstrip() for line in text.split("\n"))

# ══════════════════════════════════════════════════════════
# Problem 2: Tabs vs Spaces
# ══════════════════════════════════════════════════════════
# LLM generiert mit Spaces:
SEARCH = "def process(msg):\n    return msg"
#                            ^^^^

# File nutzt Tabs:
# "def process(msg):\n\treturn msg"
#                      ^^

# Debugging:
cat -T src/api.py | grep "def process"
# def process(msg):
# ^Ireturn msg  ← ^I = Tab

# Lösung:
# agent_start.py: Tabs → Spaces vor Matching
def normalize_indentation(text):
    return text.replace("\t", "    ")  # 1 Tab = 4 Spaces

# ══════════════════════════════════════════════════════════
# Problem 3: CRLF vs LF
# ══════════════════════════════════════════════════════════
# Windows-File: \r\n (CRLF)
# Linux-File: \n (LF)

# Debugging:
file src/api.py
# src/api.py: ASCII text, with CRLF line terminators

hexdump -C src/api.py | grep "0d 0a"
# 0d 0a = \r\n

# Lösung A: Normalisieren
dos2unix src/api.py

# Lösung B: Agent ignoriert \r
def normalize_newlines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n")

# ══════════════════════════════════════════════════════════
# Problem 4: Encoding (UTF-8 vs Latin-1)
# ══════════════════════════════════════════════════════════
# File enthält: "Ümlaut"
# LLM sendet: "Ã\x9cmlaut" (Encoding-Fehler)

# Debugging:
file -bi src/api.py
# text/plain; charset=iso-8859-1

# Python:
with open("src/api.py", "rb") as f:
    raw = f.read()
    print(raw)  # b'\xdc' statt b'\xc3\x9c'

# Lösung:
# Immer UTF-8 lesen/schreiben:
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# ══════════════════════════════════════════════════════════
# Problem 5: Context-Lines fehlen
# ══════════════════════════════════════════════════════════
# LLM generiert nur geänderte Zeile:
SEARCH = "return msg"

# File hat 5× "return msg" an verschiedenen Stellen
# → Falsche Zeile wird matched

# Debugging:
grep -n "return msg" src/api.py
# 45:    return msg
# 78:    return msg
# 112:   return msg

# Lösung: Context-Lines hinzufügen
SEARCH = """
def process(msg):
    if not msg:
        raise ValueError()
    return msg
"""

# → Eindeutiger Match

# ══════════════════════════════════════════════════════════
# Problem 6: Invisible-Characters (BOM, Zero-Width)
# ══════════════════════════════════════════════════════════
# File startet mit BOM (Byte-Order-Mark): \xef\xbb\xbf

# Debugging:
hexdump -C src/api.py | head -n 1
# 00000000  ef bb bf 64 65 66  ← BOM vor "def"

# Lösung:
with open(file_path, "r", encoding="utf-8-sig") as f:
    content = f.read()  # BOM wird automatisch entfernt
```

---

### Erklärung

**Normalisierungs-Pipeline:**

```python
def normalize_for_matching(text):
    # 1. Newlines normalisieren
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # 2. Tabs → Spaces
    text = text.replace("\t", "    ")
    
    # 3. Trailing Whitespace
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    
    # 4. Leading/Trailing Newlines
    text = text.strip()
    
    return text
```

**Debugging-Tools:**

| Tool | Use-Case |
|------|----------|
| `cat -A` | Zeigt $, ^I (Newlines, Tabs) |
| `cat -T` | Zeigt nur Tabs als ^I |
| `hexdump -C` | Zeigt Hex-Bytes |
| `file -bi` | Zeigt Encoding |
| `dos2unix` | CRLF → LF Konvertierung |

**Match-Strategies (Fallback):**

1. **Exact-Match:** String == String
2. **Normalized-Match:** normalize(String) == normalize(String)
3. **Fuzzy-Match:** 90% Ähnlichkeit
4. **AST-Match:** Semantisch (ignoriert Whitespace/Comments)
5. **Interactive:** Manuelles Review

---

### Best Practice

> [!TIP]
> **Pre-Commit-Hook für Whitespace:**
> ```bash
> # .git/hooks/pre-commit
> #!/bin/bash
> git diff --cached --check
> if [ $? -ne 0 ]; then
>   echo "Trailing whitespace detected!"
>   exit 1
> fi
> ```

> [!TIP]
> **EditorConfig:**
> ```ini
> # .editorconfig
> root = true
> 
> [*]
> end_of_line = lf
> charset = utf-8
> trim_trailing_whitespace = true
> insert_final_newline = true
> 
> [*.py]
> indent_style = space
> indent_size = 4
> ```

> [!TIP]
> **Diff-Preview vor Apply:**
> ```python
> import difflib
> 
> expected = normalize(search_string)
> actual = normalize(file_content)
> 
> diff = difflib.unified_diff(
>     expected.splitlines(),
>     actual.splitlines(),
>     lineterm=""
> )
> 
> print("\n".join(diff))
> ```

---

### Warnung

> [!WARNING]
> **Aggressive Normalisierung:**
> ```python
> text = text.replace(" ", "")  # ← alle Spaces entfernen
> → "return msg" matched auch "returnmsg"
> ```

> [!WARNING]
> **Encoding-Konvertierung verliert Daten:**
> ```python
> # File ist Latin-1, wir lesen als UTF-8
> with open(file, "r", encoding="utf-8") as f:
>     content = f.read()  # UnicodeDecodeError
> ```
> → chardet-Library für Auto-Detection

> [!WARNING]
> **Fuzzy-Match zu niedrig:**
> ```python
> if similarity > 0.5:  # 50%
>     apply_patch()
> → Fast alles matched
> ```
> → Minimum: 0.90 (90%)

---

### Nächste Schritte

✅ Search-Replace debugged  
→ [23 — Search-Replace-Patches](23-search-replace-patches.md)  
→ [34 — Eval-Debugging](34-debug-eval-fail.md)
