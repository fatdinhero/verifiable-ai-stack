from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class RuleResult:
    rule_id: str
    norm: str
    description: str
    passed: bool
    value: Any
    threshold: str
    source: str
    confidence: float


@dataclass
class Rule:
    rule_id: str
    norm: str
    description: str
    param_key: str
    threshold: str
    check: Callable[[Any], bool]
    source: str
    confidence: float = 1.0

    def evaluate(self, params: dict[str, Any]) -> RuleResult:
        value = params.get(self.param_key)
        if value is None:
            return RuleResult(
                rule_id=self.rule_id,
                norm=self.norm,
                description=self.description,
                passed=False,
                value=None,
                threshold=self.threshold,
                source=self.source,
                confidence=0.0,
            )
        return RuleResult(
            rule_id=self.rule_id,
            norm=self.norm,
            description=self.description,
            passed=self.check(value),
            value=value,
            threshold=self.threshold,
            source=self.source,
            confidence=self.confidence,
        )


RULES: list[Rule] = [
    # ── GEG §71 ────────────────────────────────────────────────────────────
    Rule(
        rule_id="GEG-71-01",
        norm="GEG §71",
        description="Mindestabstand zur Grundstücksgrenze",
        param_key="abstand_m",
        threshold="≥ 3 m",
        check=lambda v: v >= 3,
        source="GEG §71 Abs. 1 — Bundesgesetzblatt 2023",
    ),
    Rule(
        rule_id="GEG-71-02",
        norm="GEG §71",
        description="Tagespegel Schallimmission",
        param_key="tagpegel_db",
        threshold="≤ 50 dB(A)",
        check=lambda v: v <= 50,
        source="GEG §71 Abs. 2 i.V.m. TA Lärm Nr. 6.1",
    ),
    Rule(
        rule_id="GEG-71-03",
        norm="GEG §71",
        description="Nachtpegel Schallimmission",
        param_key="nachtpegel_db",
        threshold="≤ 35 dB(A)",
        check=lambda v: v <= 35,
        source="GEG §71 Abs. 2 i.V.m. TA Lärm Nr. 6.4",
    ),
    # ── GEG §72 ────────────────────────────────────────────────────────────
    Rule(
        rule_id="GEG-72-01",
        norm="GEG §72",
        description="Jahresarbeitszahl Wärmepumpe",
        param_key="jaz",
        threshold="≥ 3.5",
        check=lambda v: v >= 3.5,
        source="GEG §72 Abs. 1 i.V.m. DIN EN 14511",
    ),
    # ── GEG §74 ────────────────────────────────────────────────────────────
    Rule(
        rule_id="GEG-74-01",
        norm="GEG §74",
        description="Vollständige Anlagendokumentation vorhanden",
        param_key="dokumentation_vollstaendig",
        threshold="== True",
        check=lambda v: v is True,
        source="GEG §74 — Dokumentationspflicht",
    ),
    # ── KfW-BEG ────────────────────────────────────────────────────────────
    Rule(
        rule_id="KFW-BEG-01",
        norm="KfW-BEG",
        description="Vorlauftemperatur Wärmepumpe",
        param_key="vorlauftemp_c",
        threshold="≤ 55 °C",
        check=lambda v: v <= 55,
        source="KfW-BEG Technische Mindestanforderungen 2024 — Nr. 3.1",
    ),
    Rule(
        rule_id="KFW-BEG-02",
        norm="KfW-BEG",
        description="Heizstabanteil an Jahresenergie",
        param_key="heizstab_prozent",
        threshold="< 5 %",
        check=lambda v: v < 5,
        source="KfW-BEG Technische Mindestanforderungen 2024 — Nr. 3.2",
    ),
    Rule(
        rule_id="KFW-BEG-03",
        norm="KfW-BEG",
        description="Wärmebrücken-Zuschlag",
        param_key="waermebruecken_w_mk",
        threshold="< 0.2 W/(m²·K)",
        check=lambda v: v < 0.2,
        source="KfW-BEG Technische Mindestanforderungen 2024 — Nr. 4.1",
    ),
    # ── TA Lärm ────────────────────────────────────────────────────────────
    Rule(
        rule_id="TALARM-01",
        norm="TA Lärm",
        description="Immissionsrichtwert Mischgebiet Tag",
        param_key="mischgebiet_db",
        threshold="≤ 55 dB(A)",
        check=lambda v: v <= 55,
        source="TA Lärm Nr. 6.1 Buchstabe c",
    ),
    Rule(
        rule_id="TALARM-02",
        norm="TA Lärm",
        description="Immissionsrichtwert Wohngebiet Nacht",
        param_key="wohngebiet_nacht_db",
        threshold="≤ 35 dB(A)",
        check=lambda v: v <= 35,
        source="TA Lärm Nr. 6.1 Buchstabe d i.V.m. Nr. 6.4",
    ),
    # ── VDI 4645 ───────────────────────────────────────────────────────────
    Rule(
        rule_id="VDI-4645-01",
        norm="VDI 4645",
        description="Wandabstand Wärmepumpe",
        param_key="wandabstand_m",
        threshold="≥ 0.5 m",
        check=lambda v: v >= 0.5,
        source="VDI 4645:2018 — Abschnitt 7.3",
    ),
    Rule(
        rule_id="VDI-4645-02",
        norm="VDI 4645",
        description="Abstand Ansaug- und Blasöffnung",
        param_key="oeffnungsabstand_m",
        threshold="≥ 2 m",
        check=lambda v: v >= 2,
        source="VDI 4645:2018 — Abschnitt 7.4",
    ),
]
