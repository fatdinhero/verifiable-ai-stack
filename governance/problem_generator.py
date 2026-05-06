"""
governance/problem_generator.py
ProblemGenerator — konvertiert echte Signale in SPALTEN-Engineering-Probleme
Echte Signale priorisiert, LLM-generierte nur als Fallback.
"""
import hashlib as _hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import List, Dict, Set, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from governance.signal_sources import RealSignalFetcher, _llm_call

URGENCY_VALUES = {"low", "medium", "high", "critical"}

# 110 konkrete Fallback-Seeds — werden genutzt wenn Masterplan-Signale < 3
# Domains: healthcare_medtech (15), automotive_adas (15), financial_bfsi (10),
#          legal_compliance (10), manufacturing_industry40 (10),
#          waermepumpe_geg (10), maschinenbau_fmea (10), medtech_iso13485 (10),
#          bauingenieurwesen_din1045 (10), halbleiter_fertigung (10)
_SEED_PROBLEMS = [
    # ── healthcare_medtech (15) ──
    {"problem": "MDR Art. 54/55: Klinische Entwicklungsstrategie fuer implantierbares IoT-Geraet Klasse III nicht validiert — Notified Body Konsultation vor Pivotal-Studie nicht eingeplant", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "FDA 510k Predicate Device Selection: Aehnlichkeitsnachweis zu Predicate-Geraet unvollstaendig — wesentliche Unterschiede in Technologie (KI-basierte Auswertung) und Indikation nicht erklaert", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "Diagnose-Algorithmus-Validierung: KI-Klassifikationsmodell fuer Lungentumor-CT hat AUC 0.82 nur auf internem Testset — externe Validierungsstudie fehlt, generalisierbare Performance nicht belegt", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "DSGVO-konformes Patientendaten-Handling: Einwilligungsworkflow im KIS erfasst keine informierte Einwilligung fuer ML-basierte Diagnoseunterstuetzung — Art. 9 DSGVO (besondere Kategorien) verletzt", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "Interoperabilitaet HL7 FHIR R4: Schnittstelle zwischen Wearable-Vitaldaten und KIS nicht standardkonform implementiert — FHIR-Profile fehlen, manuelle Datenuebertragung fehleranfaellig", "domain": "healthcare_medtech", "urgency": "medium"},
    {"problem": "FDA 21 CFR Part 11 Softwarevalidierung: Elektronische Signaturen im LIMS nicht konform — Audit-Trail-Manipulierbarkeit durch fehlende Hashverifikation, FDA Warning Letter droht", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "ISO 15189 Laborakkreditierung: Messunsicherheitsbudget fuer PCR-Quantifizierung nicht nach GUM-Methode berechnet — DAkkS-Akkreditierungsversagung nach naechstem Ueberwachungsaudit wahrscheinlich", "domain": "healthcare_medtech", "urgency": "medium"},
    {"problem": "Telemedizin-Plattform: Videokonferenz-Infrastruktur erfuellt nicht Art. 9 DSGVO fuer Gesundheitsdaten — Ende-zu-Ende-Verschluesselung nicht durch Penetrationstest nachgewiesen", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "MDR Annex I Grundlegende Sicherheitsanforderungen: Biokompatibilitaetsbewertung nach ISO 10993 fuer Patientenkontaktmaterial unvollstaendig — Zytotoxizitaet und Sensibilisierungspotenzial nicht geprueft", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "Clinical Decision Support System (CDSS): Therapieempfehlungen basieren auf Leitlinien >5 Jahre alt — automatische Aktualisierungs-Pipeline fuer Wissensbasis fehlt, Patientensicherheitsrisiko", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "Arzneimittelinteraktions-Checker im KIS: Datenbankabgleich nur mit nationaler AMDB — Interaktionen mit nicht-verschreibungspflichtigen OTC-Praeparaten ignoriert, kritische Kombination unerkannt", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "MRT-Kompatibilitaet Implantat: MR-Bedingungen (Feldstaerke, SAR-Limit) nicht in DICOM SR eingebettet — Radiologen koennen Sicherheit nicht beurteilen, klinische Verwendung blockiert", "domain": "healthcare_medtech", "urgency": "medium"},
    {"problem": "MDR Transition Legacy-Produkte: 50 Produkte muessen bis Mai 2026 auf MDR umgestellt werden — Prioritaetsmatrix nach Risiko und Umsatz fehlt, Ressourcenplan nicht erstellt", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "Post-Market Clinical Follow-up (PMCF): Registriestudie fuer Gelenkprothese liefert nur 23% Follow-up-Rate — statistische Power fuer primaere Sicherheitsendpunkte unterschritten, PMCF-Bericht ungueltig", "domain": "healthcare_medtech", "urgency": "medium"},
    {"problem": "Cybersecurity medizinische Geraete: VPN-Fernwartungszugang zu Beatmungsgeraet ohne MFA — FDA Cybersecurity Guidance 2023 und IEC 81001-5-1 nicht umgesetzt, Patientengefaehrdung moeglich", "domain": "healthcare_medtech", "urgency": "high"},
    # ── automotive_adas (15) ──
    {"problem": "ISO 26262 ASIL-D: Sicherheitsziel 'Unbeabsichtigtes Bremsen bei >30 km/h verhindern' — Softwarekomponente im Bremsen-ECU nicht nach ASIL-D-Codierrichtlinien (MISRA C) entwickelt", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "SOTIF ISO 21448: Performance-Limitation Kamera-Spurhalteassistent bei Gegenlicht nicht als Triggering Condition dokumentiert — Szenario-Coverage-Nachweis fuer OEM-Freigabe fehlt", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "OTA-Update-Sicherheit: Firmware-Update fuer sicherheitskritisches ADAS-ECU ohne kryptografische Integritaetspruefung (Secure Boot, Code-Signing) — Remote-Manipulation durch Angreifer moeglich", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "Sensor-Fusion-Architektur: Bei LiDAR-Totalausfall faellt Kamera-Radar-Fusionssystem nicht auf definierten sicheren Zustand zurueck — Degradationsstrategie nach ISO 26262 Kl. 8 fehlt", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "AUTOSAR Adaptive Platform SOME/IP: Service-Discovery-Protokoll verursacht bei Burst-Traffic >5000 Requests/s CPU-Last >90% — Echtzeit-Deadline fuer ASIL-B-Funktion Spurhalte-Warnung verletzt", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "Cybersecurity ISO 21434 TARA: Bedrohungsanalyse fuer OBD-II-Schnittstelle fehlt — Remote-Code-Execution-Angriffspfad ueber CAN-Bus nicht bewertet, UN-R155 Typ-Genehmigung gefaehrdet", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "UN-R155 Cybersecurity Management System: CSMS nicht nach UN-R155 auditiert und zertifiziert — Fahrzeugzulassung in EU fuer neue Modelle ab Juli 2024 nicht moeglich", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "HD-Map-Aktualitaet: Map-Update-Frequenz 24h reicht nicht fuer dynamische Baustellen — veraltete Spurmarkierung fuehrt zu ADAS-Systemfehler auf gesperrten Spuren, Haftungsfrage offen", "domain": "automotive_adas", "urgency": "medium"},
    {"problem": "Functional Safety Hardware ASIL-D: Dual-Core-Lockstep-MCU Diagnoseabdeckung DC=90% nicht durch LBIST/MBIST Selbsttest-Nachweis bestaetigt — Hardware-Sicherheitsziel nicht erfuellt", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "V2X-Kommunikation ETSI ITS-G5: C-ITS-Station sendet CAM-Nachrichten ohne Pseudonymisierungs-Zertifikats-Rotation — Fahrzeug ueber 200m Zeitfenster verfolgbar, Datenschutz DSGVO verletzt", "domain": "automotive_adas", "urgency": "medium"},
    {"problem": "Tier-2-Lieferant Radar-Sensor: ISO 26262 Audit fehlt — Sicherheitskonzept des Zulieferers nicht in System-FMEA des OEM integriert, IATF 16949 Kl. 8.4 verletzt", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "HV-Batterie Thermomanagement: Kuehlsystem ohne Thermal-Runaway-Erkennungsalgorithmus — ISO 6469-1 Anforderung elektrische Sicherheit und UN/ECE-R100 Brandschutz nicht erfuellt", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "MISRA C:2012 Compliance: Statische Code-Analyse zeigt 1240 Regelverstoesse — davon 47 als Mandatory eingestuft, ISO 26262 Kl. 6 Konformitaetsnachweis blockiert, Release verzögert", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "Software-Regressionstests: Test-Suite deckt nur 62% der ASIL-C/D Sicherheitsfunktionen ab — ISO 26262 Kl. 6 verlangt vollstaendige Anforderungsabdeckung, Homologations-Freigabe verweigert", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "HiL-Teststand Kalibrierung: Lenkwinkel-Sensor-Modell im Hardware-in-the-Loop-Teststand nicht mit Seriengeraet kalibriert — Testabdeckungsnachweis fuer Systemvalidierung formal ungueltig", "domain": "automotive_adas", "urgency": "medium"},
    # ── financial_bfsi (10) ──
    {"problem": "AML-Compliance EU 6AMLD: Transaction-Monitoring-System hat False-Negative-Rate >15% bei Structured-Payment-Mustern (Smurfing) — ML-Modell veraltet, kein automatisches Retraining-Trigger definiert", "domain": "financial_bfsi", "urgency": "high"},
    {"problem": "Basel III/CRR III IRB-Ansatz: Kreditrisiko-Modell hat Modell-Override-Quote >20% — EBA-Leitlinie EBA/GL/2017/11 zu Model Risk Management nicht umgesetzt, ECB-Pruefung durch JST erwartet", "domain": "financial_bfsi", "urgency": "high"},
    {"problem": "MiFID II Transaction Reporting: Best-Execution-Nachweis nach RTS 27/28 nicht automatisiert — manuelle Aufbereitung fuer 8000 taegl. Transaktionen fehleranfaellig, BaFin-Audit-Findung wahrscheinlich", "domain": "financial_bfsi", "urgency": "high"},
    {"problem": "DORA Art. 11 Business Continuity: RTO von 4h fuer Core Banking System nicht durch Live-Test nachgewiesen — DORA-Meldepflicht fuer schwerwiegende IKT-Vorfaelle nicht implementiert", "domain": "financial_bfsi", "urgency": "high"},
    {"problem": "Kreditrisiko-Scoring EU KI-VO Art. 6: SCHUFA-Score als alleiniges Entscheidungsmerkmal verletzt Hochrisiko-KI-Anforderungen — Erklaerbarkeits-Report fuer abgelehnte Antraege fehlt", "domain": "financial_bfsi", "urgency": "high"},
    {"problem": "PSD2 Strong Customer Authentication: SCA-Exemption fuer <30 EUR Transaktionen ohne Betrugsrate-Tracking implementiert — RTS Art. 18 Mindestanforderungen verletzt, EBA-Pruefung droht", "domain": "financial_bfsi", "urgency": "medium"},
    {"problem": "IFRS 9 Expected Credit Loss: ECL-Staging-Kriterien nicht dokumentiert — automatischer Stage-1-zu-2-Uebertrag bei >30-Tage-Zahlungsverzoegerung fehlt, Rueckstellung-Unterdeckung im Abschluss", "domain": "financial_bfsi", "urgency": "high"},
    {"problem": "Echtzeit Fraud Detection: Betrugserkennungsmodell hat p99-Latenz >200ms — Payment-Clearing-SLA von 150ms verletzt, False-Positive-Rate 2.3% (Ziel <0.5%), Kundenbeschwerden steigen", "domain": "financial_bfsi", "urgency": "high"},
    {"problem": "FRTB Expected Shortfall (ES): ES-Berechnung ohne historische Marktdaten ueber vollstaendigen 10-Jahres-Zyklus — regulatorisches Marktrisiko-Kapital systematisch unterschaetzt, CRR III non-compliant", "domain": "financial_bfsi", "urgency": "high"},
    {"problem": "CSRD ESG-Reporting: Scope-3-Emissionen Kreditportfolio nach PCAF-Standard nicht berechnet — regulatorisches Nachhaltigkeitsreporting 2024 blockiert, Nichterfuellung droht", "domain": "financial_bfsi", "urgency": "medium"},
    # ── legal_compliance (10) ──
    {"problem": "Audit-Trail-Architektur GoBD: Mandanten-Datenbanklog weist Luecken >5min bei Systemfehlern auf — steuerrelevante Buchungen nicht revisionssicher, Betriebspruefungs-Risiko Steuerrueckforderung", "domain": "legal_compliance", "urgency": "high"},
    {"problem": "Consent-Management IAB TCF v2.2: Vendor-spezifische Einschraenkungen im Consent-String werden ignoriert — illegale Datenweitergabe an 3rd-Party-Tracker, EDPB-Klagerisiko wie gegen Google/Meta", "domain": "legal_compliance", "urgency": "high"},
    {"problem": "EU AI Act Art. 13 Transparenz: KI-generierte Vertragsentwuerfe in Legaltech-Tool nicht als KI-Ausgabe gekennzeichnet — Mandantenirrefuehrung und anwaltliche Haftungsfragen nach RDG", "domain": "legal_compliance", "urgency": "high"},
    {"problem": "ESEF-Einreichung XBRL: Jahresabschluss schlaegt BVI-Validierung durch fehlerhafte iXBRL-Taxonomy-Mapping fehl — Veroeffentlichungsfrist Bundesanzeiger nicht eingehalten, Busskeld moeglich", "domain": "legal_compliance", "urgency": "medium"},
    {"problem": "E-Discovery Legal Hold: System erfasst keine Slack- und MS-Teams-Nachrichten — richterlich angeordnete Datensicherung unvollstaendig, Contempt-of-Court-Risiko in US-Verfahren", "domain": "legal_compliance", "urgency": "high"},
    {"problem": "eIDAS QES-Validierung: Qualifizierte Elektronische Signatur prueft OCSP-Sperrstatus nicht — abgelaufene und widerrufene Zertifikate werden als gueltig akzeptiert, Rechtssicherheit Vertraege fraglich", "domain": "legal_compliance", "urgency": "high"},
    {"problem": "DSFA nach Art. 35 DSGVO: Datenschutz-Folgenabschaetzung fuer KI-gestuetzte Vertragsklauselanalyse fehlt — Hochrisiko-Verarbeitung ohne Vorab-Konsultation Aufsichtsbehoerde gestartet", "domain": "legal_compliance", "urgency": "high"},
    {"problem": "Compliance-Monitoring-Automatisierung: EUR-Lex und BaFin-Rundschreiben werden manuell in Policy-Datenbank eingepflegt — 14-Tage-Lag bis zur Implementierung, Compliance-Luecke im Uebergangszeitraum", "domain": "legal_compliance", "urgency": "medium"},
    {"problem": "Vertragsdaten-Anonymisierung NER: Named Entity Recognition fuer Vertragsparteien hat Recall 78% — 22% Namens-Leaks in anonymisierten Trainingsdaten an externen KI-Anbieter weitergegeben", "domain": "legal_compliance", "urgency": "high"},
    {"problem": "Whistleblower-System HinSchG §16: Meldestellen-Plattform speichert IP-Adressen der Melder in Server-Logs — Anonymitaet nicht gewaehlrleistet, HinSchG-Anforderung verletzt, Melder-Identifikation moeglich", "domain": "legal_compliance", "urgency": "high"},
    # ── manufacturing_industry40 (10) ──
    {"problem": "OEE-Optimierung Linie L3: Anlagenverfuegbarkeit 67% (Ziel >85%) — ungeplante Ausfaelle 8h/Woche, Stillstandsursachen nicht systematisch nach RCFA analysiert, Wartungsplan nicht optimiert", "domain": "manufacturing_industry40", "urgency": "high"},
    {"problem": "Predictive Maintenance ML: Vibrations-Anomalie-Erkennung CNC-Fraesmaschine hat False-Alarm-Rate 35% — Alarm-Fatigue bei Instandhaltern, Modell-Rekalibration mit aktuellen Sensordaten fehlt", "domain": "manufacturing_industry40", "urgency": "high"},
    {"problem": "Computer Vision QC: CNN-Defekterkennung Schweissnaht hat mAP 0.76 auf synthetischen Daten — reale In-Line-Detektion zeigt 18% False-Negative bei Porositaet, Kalibrierung auf Serienbedingungen fehlt", "domain": "manufacturing_industry40", "urgency": "high"},
    {"problem": "MES-Integration: SAP MES und Legacy-SCADA kommunizieren ueber proprietaeres Protokoll — kein OPC-UA nach IEC 62541 implementiert, Datensilos verhindern Gesamtanlagen-KPI-Auswertung", "domain": "manufacturing_industry40", "urgency": "medium"},
    {"problem": "Digitaler Zwilling Spritzguss: Simulationsmodell weicht >8% von Ist-Zykluszeiten ab — Materialeigenschaften-Datenbasis nicht aktuell, Optimierungsvorschlaege fuer Zykluszeit-Reduktion fehlerhaft", "domain": "manufacturing_industry40", "urgency": "medium"},
    {"problem": "Energiemanagement ISO 50001: Stromverbrauchsdaten nur stuendlich aggregiert — Lastspitzen-Identifikation fuer Peak-Demand-Management und PV-Sektorenkopplung (§14a EnWG) nicht moeglich", "domain": "manufacturing_industry40", "urgency": "medium"},
    {"problem": "Lieferketten-Resilienz: Single-Source fuer kritische Halbleiter-Baugruppe ohne qualifizierten Second-Source — Produktionsstillstand bei Lieferengpass innerhalb 6 Wochen, Business-Continuity-Plan fehlt", "domain": "manufacturing_industry40", "urgency": "high"},
    {"problem": "Cobot-Sicherheit ISO/TS 15066: Risikobeurteilung Mensch-Roboter-Kollaboration veraltet — neuer erweiterter Arbeitsraum ohne Kraft-Torque-Grenzwert-Validierung in Betrieb, Unfall-Haftungsrisiko", "domain": "manufacturing_industry40", "urgency": "high"},
    {"problem": "Track-and-Trace EU-LebensmittelVO 178/2002 Art. 18: Chargenverfolgung im Werk braucht >4h — gesetzlich geforderte 30-Minuten-Rueckverfolgbarkeit nicht eingehalten, Behoerden-Meldung bei Rueckruf verspaetet", "domain": "manufacturing_industry40", "urgency": "high"},
    {"problem": "Cybersecurity OT/ICS IEC 62443: SPS Siemens S7-1500 ohne Netzwerksegmentierung — direkter IT-zu-OT-Netz-Zugang, Zone-Conduit-Konzept nicht implementiert, BSI-IT-Grundschutz KRITIS verletzt", "domain": "manufacturing_industry40", "urgency": "high"},
    # ── waermepumpe_geg ──
    {"problem": "GEG §71 Pflichterfuellung: Waermepumpe mit JAZ < 2.5 erfuellt Effizienzanforderung nach GEG §71 Abs. 1 nicht — Nachruestpflicht fuer Bestandsgebaeude ab 2026 nicht definiert", "domain": "waermepumpe_geg", "urgency": "high"},
    {"problem": "Hydraulischer Abgleich nach GEG §60a fehlt bei Sanierung — Ruecklauftemperaturen zu hoch fuer Waermepumpen-Betrieb (>45°C), COP faellt auf 1.8", "domain": "waermepumpe_geg", "urgency": "high"},
    {"problem": "Kaeltemittelkreislauf mit R410A muss bis 2027 auf GWP<750-Kaeltemittel (R290 oder R32) umgestellt werden — Retrofit-Pfad und Zertifizierungsanforderungen nicht definiert", "domain": "waermepumpe_geg", "urgency": "medium"},
    {"problem": "GEG §71b Ausnahmeregelung fuer Fernwaerme: Anschluss technisch nicht moeglich — Dokumentationspflicht und behördliches Nachweisverfahren fuer Befreiungsantrag fehlen", "domain": "waermepumpe_geg", "urgency": "medium"},
    {"problem": "Schallschutzanforderungen TA Laerm fuer Ausseneinheit bei Einfamilienhaus-Installation nicht geprueft — Immissionsrichtwert 35 dB(A) nachts moeglicherweise ueberschritten", "domain": "waermepumpe_geg", "urgency": "medium"},
    {"problem": "Waermepumpensteuerung kommuniziert nicht mit Smart-Meter-Gateway nach BSI TR-03109 — §14a EnWG Steuerbarkeit durch Netzbetreiber nicht implementiert, Foerderfaehigkeit gefaehrdet", "domain": "waermepumpe_geg", "urgency": "high"},
    {"problem": "Bivalenzpunkt-Auslegung bei -7°C Aussentemperatur (Normauslegung DIN EN 12831) fuehrt zu 30% Heizleistungsunterdeckung bei Extremfrost-Ereignissen unter -15°C", "domain": "waermepumpe_geg", "urgency": "medium"},
    {"problem": "Legionellenschutz-Temperatur 60°C fuer Trinkwasser nach DVGW W551 erfordert thermischen Desinfektionslauf — Heizstab-Betrieb erhoehт Jahresstromkosten um 40%, JAZ-Nachweis verfaelscht", "domain": "waermepumpe_geg", "urgency": "medium"},
    {"problem": "GEG §71c Solar-Pflicht: Photovoltaik-Pflicht bei Waermepumpeneinbau in Neubauten nicht in Planungsunterlagen beruecksichtigt — Baugenehmigung gefaehrdet", "domain": "waermepumpe_geg", "urgency": "high"},
    {"problem": "Waermepumpen-Foerderantrag BEG WG (BAFA) abgelehnt wegen fehlender hydraulischer Berechnung nach VDI 6001 — Nachbesserungsfrist 4 Wochen nicht eingehalten", "domain": "waermepumpe_geg", "urgency": "high"},
    # ── maschinenbau_fmea ──
    {"problem": "FMEA nach AIAG-VDA 2019 nicht aktualisiert — Design-FMEA und Prozess-FMEA nicht harmonisiert, veraltete RPN-Methode statt AP (Aktionsprioritaet) nach neuer Norm", "domain": "maschinenbau_fmea", "urgency": "high"},
    {"problem": "Fehlermodus 'Spannfutter-Klemmkraft ausserhalb Toleranz' hat AP=H (S=8, A=8, E=5) — keine praeventivenMassnahmen in DFMEA dokumentiert, Sicherheitsrisiko fuer Bediener", "domain": "maschinenbau_fmea", "urgency": "high"},
    {"problem": "MSA (Messsystemanalyse) nach AIAG MSA-4 fuer Koordinatenmessmaschine nicht durchgefuehrt — GRR > 30% vermutet, Teileabnahme statistisch nicht absicherbar", "domain": "maschinenbau_fmea", "urgency": "medium"},
    {"problem": "FMEA-Teamzusammensetzung fehlt Lieferantenvertreter fuer zugekaufte Getriebebaugruppen — Risikouebertragung vertraglich nicht geregelt, IATF 16949 Kl. 8.4 verletzt", "domain": "maschinenbau_fmea", "urgency": "medium"},
    {"problem": "DFMEA fuer Schweissnahtverbindung (EN ISO 5817 Gueteklasse B) fehlt Korrelation mit FEM-Spannungsanalyse — Lebensdauerprognose S-N-Kurve nicht validiert", "domain": "maschinenbau_fmea", "urgency": "high"},
    {"problem": "Prozess-FMEA fuer CNC-Fraesen: Fehlermodus 'Werkzeugbruch unerkannt' hat AP=H ohne Abstellmassnahme — kein Werkzeugbruch-Ueberwachungssystem (Vibrationssensor) implementiert", "domain": "maschinenbau_fmea", "urgency": "high"},
    {"problem": "FMEA-Revisionshistorie nach IATF 16949 Kl. 10.2 nicht vollstaendig — Aenderungsnachweis bei Designaenderung Bauteil REV-C fehlt, Kundenfreigabe ausstaendig", "domain": "maschinenbau_fmea", "urgency": "medium"},
    {"problem": "System-FMEA fuer Hydraulikanlage nach DIN EN 4413 nicht auf neue Betriebsdruecke (350 bar) angepasst — sicherheitskritische Fehlermodi Leitungsbersten nicht neu bewertet", "domain": "maschinenbau_fmea", "urgency": "high"},
    {"problem": "Funktionale Sicherheit ISO 13849: PLr-Berechnung fuer Sicherheitsfunktion SF-01 (Notaus) nicht mit FMEA-Ergebnis abgeglichen — MTTFd-Wert des Sicherheitsrelais fehlt", "domain": "maschinenbau_fmea", "urgency": "high"},
    {"problem": "FMEA-Massnahmenverfolgung: 47 offene Massnahmen seit >6 Monaten nicht abgeschlossen — PDCA-Zyklus unterbrochen, Tier-1-Kundenaudit mit Major-Finding zu erwarten", "domain": "maschinenbau_fmea", "urgency": "high"},
    # ── medtech_iso13485 ──
    {"problem": "Risikomanagementsystem nach ISO 14971:2019 nicht mit QM nach ISO 13485 Kl. 7.1 verknuepft — Risiko-Massnahmen nicht in Produktspezifikation rueckgefuehrt", "domain": "medtech_iso13485", "urgency": "high"},
    {"problem": "Design-Validierung nach ISO 13485 Kl. 7.3.7 fehlt fuer Software-Update V2.3 — klinische Zweckbestimmung nach MDR Art. 5 nicht re-validiert, CE-Konformitaet fraglich", "domain": "medtech_iso13485", "urgency": "high"},
    {"problem": "Lieferanten-Qualifikation nach ISO 13485 Kl. 7.4: Kritischer Sensor-IC-Lieferant nur mit Self-Declaration qualifiziert — fuer Klasse IIb MDR-Produkt ist Auditnachweis Pflicht", "domain": "medtech_iso13485", "urgency": "high"},
    {"problem": "Software-Lebenszyklus-Dokumentation nach IEC 62304 Kl. 5.1 fehlt fuer Embedded Firmware — Software Safety Class nicht formal bestimmt, Risikobewertung unvollstaendig", "domain": "medtech_iso13485", "urgency": "high"},
    {"problem": "CAPA-System nach ISO 13485 Kl. 8.5.2: Ursachenanalyse fuer Feldproblem (Kalibrierungsfehler) basiert auf 5-Why ohne statistische Auswertung — systemischer Fehler moeglicherweise nicht erkannt", "domain": "medtech_iso13485", "urgency": "medium"},
    {"problem": "Post-Market Surveillance nach MDR Art. 83: Beschwerdeauswertung fliesst nicht in PMCF-Plan (MDR Annex XIV) ein — Periodic Safety Update Report (PSUR) unvollstaendig", "domain": "medtech_iso13485", "urgency": "high"},
    {"problem": "UDI-Kennzeichnung nach MDR Art. 27 nicht vollstaendig implementiert — Device Identifier (DI) und Production Identifier (PI) auf Verpackungsebene nicht gesondert ausgewiesen", "domain": "medtech_iso13485", "urgency": "medium"},
    {"problem": "Sterilisationsvalidierung nach ISO 11135 (Ethylenoxid) nicht auf neue Verpackungsgroesse extended — Bioburden-Worst-Case nicht re-evaluiert, Chargenzulassung blockiert", "domain": "medtech_iso13485", "urgency": "high"},
    {"problem": "Klinische Bewertung nach MDR Art. 61 veraltet (>3 Jahre ohne Update) — PMCF-Aktivitaetsnachweis fehlt fuer Verlaengerung der Notified-Body-Zertifizierung", "domain": "medtech_iso13485", "urgency": "high"},
    {"problem": "Notified Body Audit Finding: DHF (Design History File) nicht vollstaendig — Fertigungsprozess-Validierungsberichte fuer Spritzguss-Gehaeuseteil fehlen im Technischen Dossier", "domain": "medtech_iso13485", "urgency": "high"},
    # ── bauingenieurwesen_din1045 ──
    {"problem": "Beton-Druckfestigkeit C25/30 nach DIN 1045-1 fuer Stahlbetondecke unterschritten (Pruefergebnis 22.4 N/mm²) — Standsicherheitsnachweis ungueltig, Ursache Nachbehandlungsfehler", "domain": "bauingenieurwesen_din1045", "urgency": "high"},
    {"problem": "Bewehrungsueberdeckung cnom = 35mm nach DIN 1045 Tab. 4.4 (Expositionsklasse XC3) unterschritten auf 18mm Messung — Korrosionsschutz nicht gewaehrleistet, Karbonisierungsrisiko innerhalb 20 Jahren", "domain": "bauingenieurwesen_din1045", "urgency": "high"},
    {"problem": "Expositionsklasse XA2 (chemischer Angriff, Sulfatgehalt >600 mg/l) fuer Fundamentplatte nicht beruecksichtigt — Betonrezeptur ohne sulfatbestaendigen Zement (HS-Zement CEM III) geplant", "domain": "bauingenieurwesen_din1045", "urgency": "high"},
    {"problem": "Rissbreite wk > 0.3mm (Grenzwert DIN 1045 Expositionsklasse XC2) in Bodenplatte nach 28-Tage-Messung — Nachweis Gebrauchstauglichkeit fehlt, Mindestbewehrung zu ueberarbeiten", "domain": "bauingenieurwesen_din1045", "urgency": "medium"},
    {"problem": "Vorspannung nach DIN 1045-1 Kl. 8.10: Spannglied-Schlupfverlust δsl nicht mit gemessener Vorspannkraft abgeglichen — Tragsicherheitsnachweis mit fehlerhafter Vorspannkraft gefuehrt", "domain": "bauingenieurwesen_din1045", "urgency": "high"},
    {"problem": "Schubnachweis nach DIN EN 1992-1-1 (Eurocode 2) fuer Unterzug UZ-3: Querkraft VEd = 890 kN ueberschreitet VRd,max = 756 kN — Querkraftbuegel-Verstaerkung erforderlich", "domain": "bauingenieurwesen_din1045", "urgency": "high"},
    {"problem": "Bewehrungsstoss Wand-Decken-Anschluss nach DIN 1045 Detail 31: Stosslaenge ls = 28ds statt erforderlicher 40ds fuer BSt 500S — Kraftuebertragung nicht sichergestellt", "domain": "bauingenieurwesen_din1045", "urgency": "high"},
    {"problem": "Brandschutznachweis nach DIN 4102-4 fuer Stahlbetontraeger: Mindestachsabstand 45mm fuer R90 nicht eingehalten (Ist: 28mm) — Bekleidungsdicke in Werkplanung nicht definiert", "domain": "bauingenieurwesen_din1045", "urgency": "high"},
    {"problem": "DIN 1045 Robustheitsanforderungen Kl. 5.3: Progressiver Kollaps bei Stutzenausfall nicht nachgewiesen fuer Gebaeudeklasse 3 (mehr als 4 Geschosse, oeffentlich genutzt)", "domain": "bauingenieurwesen_din1045", "urgency": "high"},
    {"problem": "Betonierprotokoll nach DIN 1045-3 fehlt fuer Abschnitt B3 — Frischbetontemperatur, w/z-Wert und Einbauzeit nicht dokumentiert, Bauteilabnahme durch Pruefingenieur verweigert", "domain": "bauingenieurwesen_din1045", "urgency": "medium"},
    # ── halbleiter_fertigung ──
    {"problem": "Lithografie-Ausbeute bei 28nm-Knoten: 3-Sigma CD-Streuung ΔCD = ±4.2nm ueberschreitet Toleranzband ±3nm — OPC-Korrekturmodell veraltet, Requalifizierung Scanner erforderlich", "domain": "halbleiter_fertigung", "urgency": "high"},
    {"problem": "Ionenimplantation As+ bei 80keV: Dosis-Uniformitaet >2.5% (Ziel <1.5%) durch Faraday-Cup Beam-Deflection-Fehler — Maskendefekte auf 15% der Wafer in Lot HV-2024-N31", "domain": "halbleiter_fertigung", "urgency": "high"},
    {"problem": "CMP Kupfer-Erosion >30nm auf Teststruktur MIT-945 — Slurry-Selektivitaet zu hoch (>25:1 Cu:Barrier), Wannen-Effekt und Dishing auf Metall-4-Ebene", "domain": "halbleiter_fertigung", "urgency": "high"},
    {"problem": "Gate-Oxid-Integritaet TDDB-Test (VG=5.5V, 125°C): Weibull-Steigung beta=1.4 < Ziel 2.0 — fruehzeitige Ausfallmechanismen bei 5% der Dies, Prozessqualifikation ungueltig", "domain": "halbleiter_fertigung", "urgency": "high"},
    {"problem": "Wafer-Bow >150 µm nach Rueckseitenduennung auf 100 µm Zieldicke — Warping verursacht Chuck-Adhaesionsfehler beim Die-Bonding, Ausschussrate 8% auf Lot FE-2024-K19", "domain": "halbleiter_fertigung", "urgency": "medium"},
    {"problem": "Epitaxial-Wachstum SiGe (20% Ge): Schichtdicken-Uniformitaet >3.5% (1-Sigma) ueber 300mm Wafer — Hot-Spots im RTP-Ofen identifiziert, Suszeptor-Tausch und Requalifizierung noetig", "domain": "halbleiter_fertigung", "urgency": "medium"},
    {"problem": "Metallisierung Via-Fill (AR=5:1): TiN-Barrierenschicht zeigt Delamination nach Sputterservice — Sputterrate-Uniformitaet nicht neu eingestellt, Via-Widerstand +40% gegenueber Spec", "domain": "halbleiter_fertigung", "urgency": "high"},
    {"problem": "SRAM Bitfehler-Rate (BFAR) > 1000 FIT/Mb bei -40°C — Soft-Error-Rate durch kosmische Strahlung nicht modelliert, ECC-Anforderung AEC-Q100 Grade 0 fuer Automotive nicht erfuellt", "domain": "halbleiter_fertigung", "urgency": "high"},
    {"problem": "Wafer-Test EWS parametrischer Yield-Drop: VT-Streuung Lot N47 ΔVT = 85mV (Ziel ±30mV) — Poly-Silizid Prozess-Drift nach Wartung Diffusionsofen OF-12 verursacht Threshold-Shift", "domain": "halbleiter_fertigung", "urgency": "high"},
    {"problem": "Reinraumkontamination ISO Klasse 5: Partikelzaehlung 0.1 µm > 10.000/m³ nach Deckenfilter-Wartung — Qualifizierungsfrist 48h ueberschritten, SEMI E10 Notfallprotokoll nicht aktiviert", "domain": "halbleiter_fertigung", "urgency": "high"},
    # ── healthcare_medtech (10x) ──
    {"problem": "KI-Diagnose-Modell (CNN) fuer Hautkrebs-Detektion: Validierungsset hat demographischen Bias (95% heller Hautton) — FDA 510k gefaehrdet, Retrospektivstudie auf diversen Kohorten fehlt", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "MDR Art.120 Legacy-Device: CE-Zertifikat laeuft 2025 ab — Klinische Bewertung nach MDR Annex XIV fuer SaMD Klasse IIa nicht gestartet, Notified-Body-Slot-Voranmeldung bis Q2 versaeumt", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "DSGVO Art.9 Gesundheitsdaten: Pseudonymisierungs-Pipeline fuer Patientendaten im ML-Training nicht auditiert — Re-Identifikationsrisiko durch Seltene-Krankheits-Kohorte nicht bewertet", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "ISO 14971:2019 Benefit-Risk-Analyse fuer autonome Therapieempfehlung des KI-Systems nicht abgeschlossen — Restrisiko-Akzeptanzkriterium fehlt, klinischer Studienstart blockiert", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "FDA 21 CFR Part 11 Audit Trail: Elektronische Signaturen im klinischen Datenmanagementsystem nicht CFR-konform — FDA-Inspektion Warning Letter erwartet, Systembetrieb gefaehrdet", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "IEC 62304 Software Safety Class C: Change-Control fuer Algorithmus-Update V3.1 nicht dokumentiert — Regressionstest-Abdeckung 67% statt 95% fuer SC-C, Marktfreigabe gesperrt", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "HL7 FHIR R4 Interoperabilitaet: Diagnose-KI-Endpoint nicht SMART-on-FHIR-konform — OAuth2-Consent-Scope-Mismatch blockiert Integration in Krankenhaus-HIS", "domain": "healthcare_medtech", "urgency": "medium"},
    {"problem": "PMCF-Studie fehlt: Realworld-Evidence nach MDR Annex XIV Part B nicht gestartet — Periodic Safety Update Report (PSUR) fuer Notified Body ueberfaellig, Zertifikat-Suspendierung droht", "domain": "healthcare_medtech", "urgency": "high"},
    {"problem": "ICD-11-Migration: Diagnose-Output des KI-Modells noch auf ICD-10 — 70.000-Code-Mapping-Tabelle fehlt, Abrechnungskompatibilitaet ab 2025 nicht sichergestellt", "domain": "healthcare_medtech", "urgency": "medium"},
    {"problem": "XAI-Anforderung fuer Radiologie-KI: Grad-CAM-Heatmaps nicht klinisch validiert — Radiologen-Akzeptanz-Studie fehlt, EU AI Act Art.13 High-Risk-Anforderung nicht erfuellt", "domain": "healthcare_medtech", "urgency": "high"},
    # ── automotive_adas (10x) ──
    {"problem": "ISO 26262 ASIL-D: Sensor-Fusion (Kamera+LiDAR+Radar) fuer automatisches Notbremssystem ohne FMEDA — Sicherheitsziel SG-02 Verletzungsrisiko nicht quantifiziert, Typgenehmigung blockiert", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "SOTIF ISO 21448: Kamerabasiertes Spurhalte-System zeigt 3% False-Negative-Rate bei Regenmarkierungen — Triggering-Condition-Analyse und 1-Mio-Szenario-Validierungskorpus fehlen", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "OTA-Update UNECE R156: Software-Update-Management-System (SUMS) nicht zertifiziert — Rollback-Mechanismus und Integritaetspruefung nicht implementiert, Typgenehmigung entzogen", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "AUTOSAR Adaptive Platform: Perception-Stack-Deadline 100ms, Ist 140ms auf NVIDIA Orin — Task-Scheduling nicht optimiert, ASIL-D-Anforderung fuer autonomes Fahren verletzt", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "Radar-Kamera-Kalibrierung: Extrinsische Parameter driften nach Temperaturzyklus -40 bis +85 Grad um 0.8 Grad — Online-Kalibrierungsausgleich fehlt, Fusionsqualitaet bei Extremtemperaturen unzuverlaessig", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "ISO 21434 TARA fuer V2X-Kommunikation veraltet — PKI-Zertifikatsmanagement und Revokation bei kompromittierten Fahrzeugzertifikaten nicht definiert, Cybersecurity-Audit-Finding", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "ASIL-Dekomposition: Redundante Bremsanforderung ASIL-D auf zwei ASIL-B-Kanaele aufgeteilt — Dependent Failure Analysis fuer Unabhaengigkeitsnachweis des Zulieferteils fehlt", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "RL-basierter Spurwechsel-Agent: 99% im Simulator, 87% auf Realstrecke — Sim-to-Real-Gap durch unzureichende Domain-Randomization und fehlende Adversarial-Weather-Szenarien", "domain": "automotive_adas", "urgency": "medium"},
    {"problem": "LiDAR-Spinning-Unit Lebensdauer: 2000h-Spec, Flottentest zeigt 1600h-Ausfall — kein Predictive-Maintenance-Modell fuer Sensorverschleiss, Rueckrufrisiko fuer 12.000 Fahrzeuge", "domain": "automotive_adas", "urgency": "high"},
    {"problem": "NCAP 2026: Fussgaenger-Erkennung bei Dunkelheit ohne IR — YOLO-Detektor erreicht nur 71 mAP bei Nacht statt Ziel 85 mAP, NCAP 5-Sterne-Rating gefaehrdet", "domain": "automotive_adas", "urgency": "high"},
    # ── financial_bfsi (10x) ──
    {"problem": "AML-Screening Falsch-Positiv-Rate 8.3%: 4.200 False-Positive-Alerts/Tag ueberlasten Compliance-Team — ML-Modell-Abloesung nach EBA-Guidelines nicht validiert, Regulatorische Beanstandung droht", "domain": "financial_bfsi", "urgency": "high"},
    {"problem": "Basel III FRTB Sensitivitaetsbasierter Ansatz fuer Market-Risk-RWA nicht implementiert — Einfuehrung Jan 2026 erfordert Neuarchitektur des Risikorechners, 8-Monate-Zeitplan unrealistisch", "domain": "financial_bfsi", "urgency": "high"},
    {"problem": "MiFID II Transaction Reporting: 1.2% fehlerhafte LEI-Codes in ESMA-Meldungen — Bussgeldschwelle bei 5% naehert sich, automatische Datenqualitaets-Validierungs-Pipeline fehlt", "domain": "financial_bfsi", "urgency": "high"},
    {"problem": "Kreditrisiko-Scorecard: Gini-Koeffizient faellt von 0.61 auf 0.42 im Out-of-Time-Sample (2021 vs 2024) — COVID-Datendrift nicht korrigiert, EBA-konforme Modell-Validierung fehlt", "domain": "financial_bfsi", "urgency": "high"},
    {"problem": "PSD2 SCA-Exemption-Logik fuer Trusted-Beneficiaries nicht korrekt implementiert — 23% legitimer Transaktionen geblockt, Kundenbeschwerden +40%, Regulatorische Eskalation durch FCA", "domain": "financial_bfsi", "urgency": "medium"},
    {"problem": "DORA ICT-Drittanbieter-Register unvollstaendig — Cloud-Provider-Kritikalitaet nach Art.28 DORA nicht klassifiziert, Konzern-DORA-Audit findet Major-Finding, 20-Mio-EUR-Bussgelder-Risiko", "domain": "financial_bfsi", "urgency": "high"},
    {"problem": "Liquidity Coverage Ratio (LCR) Intraday-Berechnung: 4h Batch-Verzoegerung erfuellt ECB-Echtzeitanforderung fuer Stresstest-Szenarien nicht, aufsichtsrechtliche Eskalation absehbar", "domain": "financial_bfsi", "urgency": "high"},
    {"problem": "OFAC-Sanctions-Screening: 24h-Listen-Aktualisierungszyklus zu langsam fuer Echtzeit-Korrespondenzbank-Transaktionen — US-Correspondent-Banking-Beziehung bei naechster Audit gefaehrdet", "domain": "financial_bfsi", "urgency": "high"},
    {"problem": "ESG-SFDR Level 2: Principal-Adverse-Impact-Indikatoren fuer Kreditportfolio nicht berechenbar — Emissionsdaten fuer 68% der Unternehmenskredite fehlen, RTS-Deadline Juni ueberschritten", "domain": "financial_bfsi", "urgency": "high"},
    {"problem": "Fed SR 11-7 Model-Risk: KI-Kreditentscheidungsmodell ohne unabhaengige Modell-Validierung — Konzern-Risikopruefung blockiert Produktivnahme, regulatorisches Moratorium droht", "domain": "financial_bfsi", "urgency": "high"},
    # ── manufacturing_industry40 (10x) ──
    {"problem": "OEE-Engpass Presswerk: Verfuegbarkeit 71% statt Ziel 85% durch ungeplante Stillstaende — Vibrationsanomalien am Exzenterpressenantrieb bekannt, Predictive-Maintenance-Modell nicht deployed", "domain": "manufacturing_industry40", "urgency": "high"},
    {"problem": "MES-ERP-Integration: Fertigungsauftrag-Rueckmeldungen 4h verzoegert — SAP-PP-IDOC-Schnittstelle nicht auf OData REST migriert, Produktionsplanung auf veralteten Daten, OEE-Kalkulation falsch", "domain": "manufacturing_industry40", "urgency": "high"},
    {"problem": "Computer-Vision-QC: CNN-Sichtpruefung fuer Schweissnahtdefekte mit 6% False-Negative — Defektklasse Poren-unter-0.5mm im Trainingsset unterrepraesentiert, Rueckrufkosten 2.1 Mio EUR potentiell", "domain": "manufacturing_industry40", "urgency": "high"},
    {"problem": "IIoT-Sensor-Onboarding: 340 neue Vibrationssensoren erzeugen 4 TB/Tag — MQTT-Broker-Kapazitaet erschoepft, Edge-Computing-Architektur und Datenpipeline fuer Predictive Maintenance fehlen", "domain": "manufacturing_industry40", "urgency": "medium"},
    {"problem": "Digitaler Zwilling Spritzguss: Moldflow-Simulation weicht 12% von realen Zykluszeiten ab — Materialdatenbank nicht mit aktuellen Chargen-Rheologiedaten aktualisiert, Parameteroptimierung unzuverlaessig", "domain": "manufacturing_industry40", "urgency": "medium"},
    {"problem": "Predictive Quality XGBoost: Feature-Engineering auf PLC-Daten nicht standardisiert — Modell kann auf neue Maschinengeneration (Siemens S7-1500 statt S7-300) nicht uebertragen werden", "domain": "manufacturing_industry40", "urgency": "medium"},
    {"problem": "Energie-Monitoring ISO 50001: Druckluft-Leckagerate 23% des Gesamtverbrauchs — kein automatisches Leckage-Ortungssystem, manuelle Begehung alle 6 Monate, ISO-50001-Audit-Major-Finding", "domain": "manufacturing_industry40", "urgency": "medium"},
    {"problem": "Cobots ISO/TS 15066: Geschwindigkeits-Kraftbegrenzung fuer Mensch-Roboter-Kollaboration nicht nach Risikobeurteilung konfiguriert — CE-Kennzeichnung ungueltig, BG-ETEM-Betriebsverbot", "domain": "manufacturing_industry40", "urgency": "high"},
    {"problem": "Rueckwaertsverfolgbarkeit Chargennummer: Serialisierung nur bis Tier-1-Lieferant — fuer FDA 21 CFR Part 820 Medical-Device-Manufacturing ist Tier-2-Traceability Pflicht, FDA-483-Observation", "domain": "manufacturing_industry40", "urgency": "high"},
    {"problem": "5G-URLLC Private Network: Latenz P99 4.7ms statt geforderter 1ms fuer Roboter-Echtzeit-Steuerung — Netzwerk-Slicing-Konfiguration fuer 200-Geraete-Fertigungshalle nicht optimiert", "domain": "manufacturing_industry40", "urgency": "high"},
]

_DOMAIN_PROMPTS = {
    "healthcare_medtech":       "Healthcare/MedTech Engineering: MDR-Konformitaet, FDA 510k, Diagnose-Algorithmus-Validierung, DSGVO Patientendaten, ISO 14971",
    "automotive_adas":          "Automotive/ADAS: ISO 26262 FuSa, SOTIF ISO 21448, OTA-Update-Sicherheit, Sensor-Fusion-Architektur, AUTOSAR Adaptive",
    "financial_bfsi":           "Financial/BFSI: AML-Compliance 6AMLD, Basel III CRR III, MiFID II Reporting, Fraud Detection, DORA, IFRS 9",
    "legal_compliance":         "Legal/Compliance Engineering: Audit-Trail GoBD, Consent-Management TCF, EU AI Act Transparenz, ESEF XBRL, eIDAS QES",
    "manufacturing_industry40": "Manufacturing/Industry 4.0: OEE-Optimierung, Predictive Maintenance, Computer Vision QC, MES OPC-UA, IEC 62443 OT-Security",
    "waermepumpe_geg":          "Waermepumpen-Engineering: GEG §71 JAZ-Nachweis, Hydraulischer Abgleich, Kaeltemittel GWP<750, §14a EnWG, BEG-Foerderung BAFA",
    "maschinenbau_fmea":        "Maschinenbau FMEA: AIAG-VDA 2019 AP-Methode, IATF 16949, MSA GRR, ISO 13849 PLr, CNC-Prozess-FMEA",
    "medtech_iso13485":         "MedTech QMS: ISO 13485, ISO 14971, MDR CE-Kennzeichnung, IEC 62304 Software-Lebenszyklus, PMCF, UDI-Kennzeichnung",
    "bauingenieurwesen_din1045": "Bauingenieurwesen Stahlbeton: DIN 1045 Expositionsklassen, Eurocode 2 Schubnachweis, Rissbreitennachweis, DIN 4102 Brandschutz",
    "halbleiter_fertigung":     "Halbleiterfertigung: Lithografie CD-Uniformitaet, CMP Erosion, Ionenimplantation, Reinraum SEMI E10, AEC-Q100 Automotive",
}


def _signal_to_problem(signal: dict) -> dict:
    """Konvertiert ein Signal via LLM in ein strukturiertes Engineering-Problem."""
    title = signal.get("title", "")
    body = signal.get(
        "problem",
        signal.get("description", signal.get("body", ""))
    )
    source = signal.get("source", "unknown")
    domain = signal.get("domain", "engineering")

    prompt = (
        f"Signal aus Quelle '{source}':\n"
        f"Titel: {title}\n"
        f"Details: {str(body)[:400]}\n\n"
        "Konvertiere diesen Issue/Signal in ein praezises Engineering-Problem "
        "fuer SPALTEN-Analyse (COGNITUM/DaySensOS). "
        'Antworte NUR mit validem JSON: '
        '{"problem": "...", "domain": "...", "urgency": "medium"}'
    )

    response = _llm_call(prompt, timeout=90)

    # JSON aus LLM-Antwort extrahieren
    parsed = None
    m = re.search(r'\{[^{}]+\}', response, re.DOTALL)
    if m:
        try:
            parsed = json.loads(m.group())
        except json.JSONDecodeError:
            pass

    if parsed:
        urgency = parsed.get("urgency", "medium")
        if urgency not in URGENCY_VALUES:
            urgency = "medium"
        return {
            "problem": parsed.get("problem") or title or body[:100],
            "domain":  parsed.get("domain")  or domain,
            "urgency": urgency,
            "source":  source,
            "raw_signal": signal,
            "sig_key":  (title or str(body))[:120],
        }

    # Fallback: kein gueltiges JSON
    raw_problem = f"{title}: {str(body)[:100]}" if title else str(body)[:150]
    return {
        "problem": raw_problem.strip() or "Unbekanntes Problem",
        "domain":  domain,
        "urgency": "medium",
        "source":  source,
        "raw_signal": signal,
        "sig_key":  (title or str(body))[:120],
    }


_DOMAIN_CYCLE = list(_DOMAIN_PROMPTS.keys())


def _generate_llm_problem(index: int, domain: str = None) -> dict:
    """Generiert ein LLM-synthetisches Engineering-Problem mit Domain-Schwerpunkt als Fallback."""
    target_domain = domain or _DOMAIN_CYCLE[index % len(_DOMAIN_CYCLE)]
    domain_context = _DOMAIN_PROMPTS.get(target_domain, "COGNITUM/DaySensOS Engineering")

    prompt = (
        f"Generiere Engineering-Problem #{index} mit Schwerpunkt: {domain_context}. "
        "Sei spezifisch, technisch praezise und konkret — keine generischen Aussagen. "
        'Antworte NUR mit validem JSON: '
        f'{{"problem": "...", "domain": "{target_domain}", "urgency": "medium"}}'
    )
    response = _llm_call(prompt, timeout=90)

    m = re.search(r'\{[^{}]+\}', response, re.DOTALL)
    if m:
        try:
            p = json.loads(m.group())
            urgency = p.get("urgency", "medium")
            if urgency not in URGENCY_VALUES:
                urgency = "medium"
            return {
                "problem": p.get("problem", response[:150]),
                "domain":  p.get("domain", target_domain),
                "urgency": urgency,
                "source":  "llm_generated",
            }
        except json.JSONDecodeError:
            pass

    return {
        "problem": response[:200] if not response.startswith("[SIMULATION]") else
                   f"COGNITUM {target_domain} Problem #{index}: Sensor-Consent-Validierung",
        "domain":  target_domain,
        "urgency": "medium",
        "source":  "llm_generated",
    }


import random as _random


def _prob_hash(text: str) -> str:
    return _hashlib.sha256(text[:120].encode("utf-8")).hexdigest()[:20]


class ProblemGenerator:
    def __init__(self):
        self.fetcher = RealSignalFetcher()
        self._seed_index = 0

    def generate(self, n: int = 5, skip_hashes: Optional[Set[str]] = None) -> List[dict]:
        """
        Generiert n Engineering-Probleme.
        1. fetch_all() — scannt ALLE Signale nach noch nicht gesehenen (skip_hashes-Prefilter)
        2. Seed-Fallback wenn frische Real-Signale erschoepft
        3. LLM-Fallback mit Domain-Rotation wenn Seed-Pool erschoepft
        4. Echte Signale werden priorisiert
        """
        skip_hashes = skip_hashes or set()

        # 1. Echte Signale holen
        signals = self.fetcher.fetch_all(repos=["fatdinhero/cognitum"])
        masterplan_signals = [s for s in signals if s.get("source") == "masterplan"]
        print(
            f"  ProblemGenerator: {len(signals)} Signale gesamt "
            f"({len(masterplan_signals)} Masterplan)"
        )

        problems: List[dict] = []

        # 2. Signale konvertieren — Prefilter via sig_key-Hash (LLM-Call sparen)
        for sig in signals:
            if len(problems) >= n:
                break
            # Schnell-Check via Signal-Key (kanonisch, deterministisch)
            sig_key = (sig.get("title") or sig.get("problem", ""))[:120]
            sig_h   = _prob_hash(sig_key)
            if sig_h in skip_hashes:
                continue
            p = _signal_to_problem(sig)
            if not p.get("problem"):
                continue
            # Auch LLM-konvertierten Hash pruefen (Rueckwaertskompatibilitaet)
            final_h = _prob_hash(p["problem"])
            if final_h in skip_hashes:
                continue
            problems.append(p)

        fresh_real = len(problems)

        # 3. Seed-Fallback — wenn frische Real-Signale nicht ausreichen
        remaining = n - len(problems)
        if remaining > 0:
            print(f"  Seed-Fallback: {remaining} Probleme (fresh_real={fresh_real})")
            seed_pool = list(_SEED_PROBLEMS)
            _random.shuffle(seed_pool)
            for seed in seed_pool:
                if remaining <= 0:
                    break
                seed_text = seed.get("problem", "")
                if _prob_hash(seed_text) in skip_hashes:
                    continue
                p = {**seed, "source": "seed_fallback"}
                problems.append(p)
                remaining -= 1

        # 4. LLM-Fallback — wenn Seeds auch erschoepft
        remaining = n - len(problems)
        if remaining > 0:
            print(f"  LLM-Fallback: {remaining} synthetische Probleme")
            for i in range(remaining):
                domain = _DOMAIN_CYCLE[(self._seed_index + i) % len(_DOMAIN_CYCLE)]
                p = _generate_llm_problem(len(problems) + i + 1, domain=domain)
                problems.append(p)
            self._seed_index = (self._seed_index + remaining) % len(_DOMAIN_CYCLE)

        # 5. Priorisierung: echte Signale zuerst
        def _priority(p: dict) -> int:
            src = p.get("source", "")
            if src in ("masterplan", "github", "gitlab"):
                return 0
            if src == "seed_fallback":
                return 1
            return 2

        problems.sort(key=_priority)
        return problems[:n]
