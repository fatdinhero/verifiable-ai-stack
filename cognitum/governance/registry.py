#!/usr/bin/env python3
"""
governance/registry.py
Layer-1-Compliance-Defense für COGNITUM / MPPS

Harte, deterministische Lookups für alle kritischen Engineering-Werte.
LLM darf diese Werte NUR referenzieren, niemals berechnen oder halluzinieren.

Quellen (lizenzkonform):
- TA Lärm: verwaltungsvorschriften-im-internet.de
- GEG / BEG: KfW-Merkblätter, gesetze-im-internet.de
- FMEA Action Priority: AIAG-VDA 2019 (öffentlich zugängliche Tabellen)
"""

import itertools
from decimal import Decimal
from typing import Any, Dict, List, Literal, Tuple

# ============================================================================
# TA LÄRM – Immissionsrichtwerte (Stand 2023/2026)
# ============================================================================

TA_LAERM: Dict[str, Dict[str, Decimal]] = {
    "industrie": {"tag": Decimal("70"), "nacht": Decimal("70")},
    "gewerbe":  {"tag": Decimal("65"), "nacht": Decimal("50")},
    "urban":    {"tag": Decimal("63"), "nacht": Decimal("45")},
    "misch":    {"tag": Decimal("60"), "nacht": Decimal("45")},
    "wohn":     {"tag": Decimal("55"), "nacht": Decimal("40")},
    "reines_wohn": {"tag": Decimal("50"), "nacht": Decimal("35")},
}

def get_ta_laerm(zonen_typ: str, tageszeit: Literal["tag", "nacht"]) -> Decimal:
    """Gibt den Immissionsrichtwert zurück oder wirft ValueError bei ungültigem Typ."""
    if zonen_typ not in TA_LAERM:
        raise ValueError(f"Ungültiger Zonen-Typ: {zonen_typ}")
    return TA_LAERM[zonen_typ][tageszeit]

# ============================================================================
# GEG / BEG – Wichtige Kennwerte (Stand 2025/2026)
# ============================================================================

GEG_ANLAGE_4_VALID_FACTORS: Dict[str, Decimal] = {
    "strom": Decimal("1.8"),
    "gas": Decimal("1.1"),
    "fernwaerme": Decimal("0.7"),
    "holz": Decimal("0.2"),
}

BEG_EFFIZIENZHAUS_STUFEN = {
    "40": {"q_p": Decimal("40"), "h_t": Decimal("40")},
    "55": {"q_p": Decimal("55"), "h_t": Decimal("55")},
    "70": {"q_p": Decimal("70"), "h_t": Decimal("70")},
    "85": {"q_p": Decimal("85"), "h_t": Decimal("85")},
    "100": {"q_p": Decimal("100"), "h_t": Decimal("100")},
}

def get_beg_stufe(stufe: str) -> Dict[str, Decimal]:
    if stufe not in BEG_EFFIZIENZHAUS_STUFEN:
        raise ValueError(f"Ungültige BEG-Stufe: {stufe}")
    return BEG_EFFIZIENZHAUS_STUFEN[stufe]

# ============================================================================
# FMEA – Action Priority (AIAG-VDA 2019)
# ============================================================================

def calculate_rpn(severity: int, occurrence: int, detection: int) -> int:
    """Berechnet die Risikoprioritätszahl (deterministisch)."""
    if not (1 <= severity <= 10 and 1 <= occurrence <= 10 and 1 <= detection <= 10):
        raise ValueError("S, O, D müssen zwischen 1 und 10 liegen")
    return severity * occurrence * detection

def get_action_priority(severity: int, occurrence: int, detection: int) -> Literal["H", "M", "L"]:
    """Gibt die Action Priority nach AIAG-VDA 2019 zurück (S, O, D je 1–10)."""
    rpn = severity * occurrence * detection
    if severity >= 9 or rpn >= 200:
        return "H"
    if rpn >= 100 or (severity >= 7 and occurrence >= 4):
        return "M"
    return "L"

# ============================================================================
# NWA / AHP – Minimal-Helper (für Demo)
# ============================================================================

def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}

# ============================================================================
# Validierungs-Helfer für Agenten
# ============================================================================

def validate_compliance_claim(claim: str, norm_id: str, corpus: set) -> bool:
    """Prüft, ob ein Claim wörtlich im lizenzkonformen Korpus vorkommt."""
    return any(norm_id in line and claim in line for line in corpus)

# ============================================================================
# VDI 2221/2222 – Morphologischer Kasten + VDI 2225 Nutzwertanalyse
# ============================================================================

def morphologischer_kasten(
    matrix: Dict[str, List[Any]],
    max_varianten: int = 20,
) -> List[Dict[str, Any]]:
    """VDI 2222 Morphologischer Kasten — generiert Varianten aus dem Loesungsraum.

    Args:
        matrix: {'Dimension': ['Option1', 'Option2', ...], ...}
        max_varianten: maximale Anzahl Kombinationen (Abbruch nach Limit)

    Returns: Liste von Variant-Dicts, je eine Option pro Dimension.
    """
    keys = list(matrix.keys())
    values = [matrix[k] for k in keys]
    varianten: List[Dict[str, Any]] = []
    for combo in itertools.product(*values):
        varianten.append(dict(zip(keys, combo)))
        if len(varianten) >= max_varianten:
            break
    return varianten


def vdi2225_evaluate(
    optionen: Dict[str, Dict[str, float]],
    gewichte: Dict[str, float],
    skala_max: int = 4,
    mindest_score: float = 0.6,
) -> Dict[str, Any]:
    """VDI 2225 Nutzwertanalyse — bewertet Varianten nach gewichteten Kriterien.

    Args:
        optionen:     {'V1': {'kriterium': wert, ...}, 'V2': {...}, ...}
        gewichte:     {'kriterium': gewicht, ...}  (muss auf 1.0 summieren)
        skala_max:    obere Skalengrenze (Default 4 fuer VDI 2225)
        mindest_score: normalisierter Mindest-Score fuer Gate-Passed (0–1)

    Returns dict mit 'best', 'best_score', 'gate_passed', 'scores'.
    """
    total_weight = sum(gewichte.values()) or 1.0
    scores: Dict[str, float] = {}
    for name, kriterien in optionen.items():
        weighted_sum = sum(
            kriterien.get(k, 0) * w for k, w in gewichte.items()
        )
        scores[name] = weighted_sum / (skala_max * total_weight)

    best = max(scores, key=lambda k: scores[k]) if scores else ""
    best_score = scores.get(best, 0.0)
    return {
        "scores": scores,
        "best": best,
        "best_score": round(best_score, 4),
        "gate_passed": best_score >= mindest_score,
        "skala_max": skala_max,
        "mindest_score": mindest_score,
    }


print("✅ governance/registry.py geladen – Layer-1-Compliance-Defense aktiv")