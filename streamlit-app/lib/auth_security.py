"""Passwort-Hashing mit bcrypt — pure Python, keine Streamlit-Imports.

bcrypt verwendet ein Salt pro Hash und ist Industrie-Standard für
Passwort-Speicherung. Die `cost` von 12 ist ein guter Default
(langsam genug gegen Brute-Force, schnell genug für Login).
"""

from __future__ import annotations

import bcrypt

BCRYPT_COST = 12


def hash_password(plaintext: str) -> str:
    """Hash ein Klartext-Passwort. Gibt UTF-8 String zurück (gut für Airtable)."""
    if not plaintext:
        raise ValueError("Passwort darf nicht leer sein")
    salt = bcrypt.gensalt(rounds=BCRYPT_COST)
    return bcrypt.hashpw(plaintext.encode("utf-8"), salt).decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    """Prüft Klartext gegen einen bcrypt-Hash. False bei leerem Input."""
    if not plaintext or not hashed:
        return False
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        # Defekter Hash → kein Crash, einfach reject
        return False
