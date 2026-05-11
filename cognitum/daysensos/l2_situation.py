"""DaySensOS — L2 Situation RuleEngine: YAML-Regelwerk.

Bestaetigt: YAML-Regelwerk als Primaersystem (VDI 2225 Score 3.60/4.00).
Erkenntnis 4: RF-Classifier nur als optionales Opt-In, NIE als Primaer.
"""
import yaml
from pathlib import Path
from datetime import datetime
from .models import ContextID, SituationResult

RULES_DIR = Path(__file__).parent / "rules"


def load_rules() -> list[dict]:
    """Laedt Kontextregeln aus contexts.yaml."""
    rules_file = RULES_DIR / "contexts.yaml"
    if not rules_file.exists():
        return []
    with open(rules_file) as f:
        data = yaml.safe_load(f)
    return data.get("rules", [])


def evaluate_condition(condition: dict, signals: dict) -> bool:
    """Evaluiert eine einzelne Regel-Bedingung gegen die Sensorsignale."""
    field = condition.get("field")
    op = condition.get("op")
    value = condition.get("value")

    actual = signals.get(field)
    if actual is None:
        return False

    if op == "eq":
        return actual == value
    elif op == "gt":
        return actual > value
    elif op == "lt":
        return actual < value
    elif op == "gte":
        return actual >= value
    elif op == "lte":
        return actual <= value
    elif op == "in":
        return actual in value
    elif op == "contains":
        return value in str(actual)
    return False


def classify_context(signals: dict) -> SituationResult:
    """Klassifiziert den aktuellen Kontext basierend auf YAML-Regeln.

    Regeln werden in Prioritaetsreihenfolge evaluiert.
    Erste Regel die matched gewinnt.
    """
    rules = load_rules()

    for rule in rules:
        conditions = rule.get("conditions", [])
        if not conditions:
            continue

        all_match = all(evaluate_condition(c, signals) for c in conditions)

        if all_match:
            try:
                context = ContextID(rule["context"])
            except ValueError:
                context = ContextID.UNKNOWN

            return SituationResult(
                context_id=context,
                confidence=rule.get("confidence", 0.8),
                rule_matched=rule.get("id", "unknown"),
                timestamp=datetime.utcnow(),
            )

    # Fallback: Zeitbasierte Heuristik
    return _time_based_fallback(signals)


def _time_based_fallback(signals: dict) -> SituationResult:
    """Fallback wenn keine Regel matched: Tageszeit-basierte Heuristik."""
    ts = signals.get("timestamp", "")
    try:
        hour = datetime.fromisoformat(ts).hour
    except (ValueError, TypeError):
        hour = datetime.utcnow().hour

    if 0 <= hour < 6:
        ctx = ContextID.SLEEP
    elif 6 <= hour < 9:
        ctx = ContextID.REST
    elif 9 <= hour < 17:
        ctx = ContextID.LIGHT_WORK
    elif 17 <= hour < 21:
        ctx = ContextID.SOCIAL
    else:
        ctx = ContextID.REST

    return SituationResult(
        context_id=ctx,
        confidence=0.3,
        rule_matched="time_fallback",
        timestamp=datetime.utcnow(),
    )
