"""
log.py — Logging-Konfiguration für gitea-agent.

Zwei Handler:
    Console: WARNING und höher (nicht zu viel Rauschen)
    File:    INFO und höher (vollständige Analyse-Grundlage)

Verwendung in anderen Modulen:
    from log import get_logger
    log = get_logger(__name__)
    log.info("Plan gepostet für Issue #21")
    log.warning("Label 'ready-for-agent' nicht gefunden")
    log.error("Gitea API nicht erreichbar: ...")
"""

import logging
import sys
from pathlib import Path


def setup(log_file: str = "gitea-agent.log", level: str = "INFO") -> None:
    """
    Initialisiert Root-Logger mit Console- und File-Handler.

    Aufgerufen von:
        agent_start.py — einmalig beim Start

    Args:
        log_file: Pfad zur Log-Datei (relativ zum Script-Verzeichnis)
        level:    Log-Level für File-Handler (DEBUG/INFO/WARNING/ERROR)
    """
    numeric = getattr(logging, level.upper(), logging.INFO)
    root    = logging.getLogger()
    root.setLevel(logging.DEBUG)  # Root fängt alles — Handler filtern

    fmt = logging.Formatter("%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")

    # Console: nur WARNING+ (kein Rauschen im Terminal)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.WARNING)
    console.setFormatter(fmt)

    # File: INFO+ (vollständiger Audit-Trail)
    log_path = Path(__file__).parent / log_file
    file_h   = logging.FileHandler(log_path, encoding="utf-8")
    file_h.setLevel(numeric)
    file_h.setFormatter(fmt)

    root.addHandler(console)
    root.addHandler(file_h)


def get_logger(name: str) -> logging.Logger:
    """
    Gibt einen benannten Logger zurück.

    Args:
        name: Modul-Name (üblicherweise __name__)

    Returns:
        Logger-Instanz.
    """
    return logging.getLogger(name)
