"""
governance/registry.py
Layer-1-Compliance-Defense: Deterministische Lookups fuer Engineering-Werte.
LLM darf diese Werte NUR referenzieren, niemals berechnen.

Quellen (lizenzkonform):
- TA Laerm: verwaltungsvorschriften-im-internet.de
- GEG/BEG: KfW-Merkblaetter, gesetze-im-internet.de
- FMEA AP: AIAG-VDA 2019 (oeffentlich zugaengliche Tabellen)
"""
from decimal import Decimal
from typing import Dict, Optional

# TA Laerm Immissionsrichtwerte (dB(A))
TA_LAERM: Dict[str, Dict[str, Decimal]] = {
    "industrie":    {"tag": Decimal("70"), "nacht": Decimal("70")},
    "gewerbe":      {"tag": Decimal("65"), "nacht": Decimal("50")},
    "urban":        {"tag": Decimal("63"), "nacht": Decimal("45")},
    "misch":        {"tag": Decimal("60"), "nacht": Decimal("45")},
    "wohn":         {"tag": Decimal("55"), "nacht": Decimal("40")},
    "reines_wohn":  {"tag": Decimal("50"), "nacht": Decimal("35")},
}

def get_ta_laerm(zonen_typ: str, tageszeit: str) -> Decimal:
    if zonen_typ not in TA_LAERM:
        raise ValueError(f"Ungueltiger Zonen-Typ: {zonen_typ}. Erlaubt: {list(TA_LAERM.keys())}")
    if tageszeit not in ("tag", "nacht"):
        raise ValueError(f"Ungueltige Tageszeit: {tageszeit}. Erlaubt: tag, nacht")
    return TA_LAERM[zonen_typ][tageszeit]

# GEG Anlage 4 Primaerenergiefaktoren
GEG_PRIMAERENERGIE: Dict[str, Decimal] = {
    "strom": Decimal("1.8"),
    "gas": Decimal("1.1"),
    "fernwaerme": Decimal("0.7"),
    "holz": Decimal("0.2"),
}

# BEG Effizienzhaus-Stufen
BEG_STUFEN: Dict[str, Dict[str, Decimal]] = {
    "40":  {"q_p": Decimal("40"),  "h_t": Decimal("55")},
    "55":  {"q_p": Decimal("55"),  "h_t": Decimal("70")},
    "70":  {"q_p": Decimal("70"),  "h_t": Decimal("85")},
    "85":  {"q_p": Decimal("85"),  "h_t": Decimal("100")},
    "100": {"q_p": Decimal("100"), "h_t": Decimal("115")},
}

# FMEA: RPZ + Action Priority (AIAG-VDA 2019)
def calculate_rpn(severity: int, occurrence: int, detection: int) -> int:
    for name, val in [("severity", severity), ("occurrence", occurrence), ("detection", detection)]:
        if not (1 <= val <= 10):
            raise ValueError(f"{name} muss zwischen 1 und 10 liegen, ist {val}")
    return severity * occurrence * detection

def get_action_priority(severity: int, occurrence: int, detection: int) -> str:
    rpn = calculate_rpn(severity, occurrence, detection)
    if severity >= 9:
        return "H"
    if severity >= 7 and occurrence >= 4:
        return "H"
    if rpn >= 200:
        return "H"
    if rpn >= 80 or (severity >= 5 and occurrence >= 4):
        return "M"
    return "L"

# NWA-Helfer
def run_nwa(kriterien: Dict[str, float], gewichte: Dict[str, float],
            optionen: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    total_w = sum(gewichte.values())
    norm_g = {k: v / total_w for k, v in gewichte.items()}
    ergebnis = {}
    for option_name, bewertungen in optionen.items():
        score = sum(bewertungen.get(k, 0) * norm_g.get(k, 0) for k in norm_g)
        ergebnis[option_name] = round(score, 4)
    return ergebnis

# ============================================================================
# VDI 2225 — Bewertung technischer Loesungen
# ============================================================================

def vdi2225_score(bewertungen: Dict[str, int], gewichte: Dict[str, float],
                  skala_max: int = 4) -> float:
    """VDI 2225 gewichteter Gesamtnutzen. Punkte 0..skala_max, Gewichte werden normiert."""
    total_w = sum(gewichte.values())
    if total_w == 0:
        raise ValueError("Gewichte duerfen nicht alle 0 sein")
    norm_g = {k: v / total_w for k, v in gewichte.items()}
    raw = sum(bewertungen.get(k, 0) * norm_g.get(k, 0) for k in norm_g)
    return round(raw / skala_max, 4)  # Normiert auf 0..1

def vdi2225_evaluate(optionen: Dict[str, Dict[str, int]],
                     gewichte: Dict[str, float],
                     skala_max: int = 4,
                     mindest_score: float = 0.6) -> Dict[str, any]:
    """Vollstaendige VDI 2225 Bewertung aller Optionen mit Gate-Logik."""
    scores = {}
    for name, bew in optionen.items():
        scores[name] = vdi2225_score(bew, gewichte, skala_max)
    best_name = max(scores, key=scores.get)
    return {
        "scores": scores,
        "best": best_name,
        "best_score": scores[best_name],
        "gate_passed": scores[best_name] >= mindest_score,
    }

# ============================================================================
# VDI 2221 — Morphologischer Kasten (Zwicky-Box)
# ============================================================================

def morphologischer_kasten(matrix: Dict[str, list],
                           max_varianten: int = 8,
                           ausschluss: Optional[Dict[str, list]] = None) -> list:
    """Erzeugt Loesungsvarianten aus einem morphologischen Kasten.
    
    Args:
        matrix: Funktionen -> Liste von Teilloesungen
        max_varianten: Maximale Anzahl Kombinationen
        ausschluss: Optional {funktion: [unerwuenschte_teilloesungen]}
    Returns:
        Liste von Dicts {funktion: gewaehlte_teiloesung}
    """
    import itertools
    funktionen = list(matrix.keys())
    teilloesungen = [matrix[f] for f in funktionen]
    varianten = []
    for kombi in itertools.product(*teilloesungen):
        loesung = dict(zip(funktionen, kombi))
        # Ausschlussregeln anwenden
        if ausschluss:
            skip = False
            for funk, verboten in ausschluss.items():
                if funk in loesung and loesung[funk] in verboten:
                    skip = True
                    break
            if skip:
                continue
        varianten.append(loesung)
        if len(varianten) >= max_varianten:
            break
    return varianten
