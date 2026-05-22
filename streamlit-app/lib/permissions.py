"""Role-Based Access Control — Permission-Matrix + can()-Helper.

Single source of truth: was darf welche Rolle pro Tool. Wird konsumiert
von:
    - app.py                  → Sidebar-Filter pro Rolle
    - jede Page               → require_tool_access(...) Gate am Anfang
    - Edit-Buttons in Pages   → if can(role, tool, "write"): ...

Tools sind logische IDs (kurz, snake_case), kein Page-Path. Eine Page
kann auch mehrere Tools nutzen (z.B. die Leads-Page nutzt "leads"
für die Liste und "mentoren" für die Mentor-Selectbox).

Permission-Levels:
    "full"           — alles erlaubt (read + write + delete)
    "write"          — read + write
    "limited_self"   — read + write nur für eigene Daten (Filter im Loader)
    "full_self"      — alles, aber gefiltert auf self
    "read_self"      — read nur eigene Daten
    "read"           — nur lesen (alle Datensätze)
    "none"           — kein Zugriff (Tool nicht in Sidebar)
"""

from __future__ import annotations

from typing import Literal

PermissionLevel = Literal[
    "full",
    "write",
    "limited_self",
    "full_self",
    "read_self",
    "read",
    "none",
]

Action = Literal["read", "write", "delete"]


# -----------------------------------------------------------------------------
# Die Rollen-Matrix — was darf welche Rolle pro Tool
# Fehlende Keys = "none" (Default)
# -----------------------------------------------------------------------------

ROLE_MATRIX: dict[str, dict[str, PermissionLevel]] = {
    "Hauptadmin": {
        # Übersicht
        "dashboard":     "full",
        "pipeline":      "full",
        # Operationen
        "leads":         "full",
        "mentoren":      "full",
        "mentees":       "full",
        "engagements":   "full",
        "sessions":      "read",       # alle sehen, eintragen tut der Mentor
        "programme":     "full",
        # Monitoring (read-only)
        "hot_leads":     "read",
        "strategie":     "read",
        # Analytics
        "performance":   "full",
        # System
        "benutzer":      "full",
        "einstellungen": "full",
    },

    "Sales": {
        "dashboard":   "read",
        "leads":       "limited_self",  # eigene Pipeline schreiben
        "mentoren":    "read",          # für Convert-Mentor-Pool-Sicht
        "mentees":     "write",         # nur beim Convert anlegen
        "engagements": "limited_self",  # eigene Conversions
        "programme":   "read",          # für Convert-Programm-Auswahl
        "hot_leads":   "full",
        "strategie":   "full",
        "performance": "read_self",
    },

    "Mentor": {
        "dashboard":   "read",
        "mentoren":    "read_self",      # nur eigener Mentor-Record
        "mentees":     "limited_self",   # nur eigene Mentees
        "sessions":    "full_self",      # eigene Sessions + neue eintragen
        "engagements": "read_self",      # eigene Engagements (read-only)
        "programme":   "read",
        "aufgaben":    "full_self",      # eigene Aufgaben markieren
        "performance": "read_self",
        "profil":      "read_self",
    },
}


# -----------------------------------------------------------------------------
# Permission-Check
# -----------------------------------------------------------------------------

def can(role: str, tool: str, action: Action = "read") -> bool:
    """Prüft, ob `role` die `action` auf `tool` ausführen darf.

    Args:
        role:   "Hauptadmin" | "Sales" | "Mentor"
        tool:   logische Tool-ID, z.B. "leads", "mentoren", "hot_leads"
        action: "read" | "write" | "delete"

    Returns:
        True wenn erlaubt, False sonst.
    """
    perm = ROLE_MATRIX.get(role, {}).get(tool, "none")
    if perm == "none":
        return False
    if action == "read":
        return True  # alle non-"none" Level erlauben Read
    if action == "write":
        return perm in ("full", "write", "limited_self", "full_self")
    if action == "delete":
        return perm == "full"
    return False


def is_self_scoped(role: str, tool: str) -> bool:
    """True wenn die Permission auf eigene Daten beschränkt ist.

    Wird im Loader genutzt: wenn True → DataFrame auf self filtern.
    """
    perm = ROLE_MATRIX.get(role, {}).get(tool, "none")
    return perm in ("limited_self", "full_self", "read_self")


def has_any_access(role: str) -> bool:
    """True wenn die Rolle überhaupt irgendwas darf — sonst Login verweigern."""
    return bool(ROLE_MATRIX.get(role))
