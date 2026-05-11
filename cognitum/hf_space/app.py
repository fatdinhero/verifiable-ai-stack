"""
CNA CLI — Gradio Interface
agentsprotocol.org
"""
import os
import sys

# cognitum/ lives next to app.py — no external package needed
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
import yaml
import gradio as gr

from cognitum.cna.rules import RULES
from cognitum.cna.reporter import report_json, report_markdown

_example_path = Path(os.path.dirname(__file__)) / "example_params.yaml"
DEFAULT_YAML = _example_path.read_text(encoding="utf-8") if _example_path.exists() else ""

TITLE = "CNA CLI — Compliance Norm Analyzer | agentsprotocol.org"
DESCRIPTION = (
    "Prüft technische Parameter gegen **GEG §71-74**, **KfW-BEG**, **TA Lärm**, **VDI 4645**"
)


def run_check(yaml_input: str) -> tuple[str, str]:
    try:
        params = yaml.safe_load(yaml_input) or {}
    except yaml.YAMLError as exc:
        msg = f"YAML-Fehler: {exc}"
        return msg, msg

    results = [rule.evaluate(params) for rule in RULES]
    return report_json(results), report_markdown(results)


with gr.Blocks(title=TITLE) as demo:
    gr.Markdown(f"# {TITLE}\n\n{DESCRIPTION}")

    yaml_input = gr.Textbox(
        label="Parameter (YAML)",
        value=DEFAULT_YAML,
        lines=20,
        placeholder="YAML-Parameter hier einfügen…",
    )

    btn = gr.Button("Normen prüfen", variant="primary")

    with gr.Row():
        json_out = gr.Code(
            label="JSON-Report",
            language="json",
            lines=30,
        )
        md_out = gr.Markdown(label="Markdown-Tabelle")

    btn.click(fn=run_check, inputs=yaml_input, outputs=[json_out, md_out])

    gr.HTML(
        '<div style="text-align:center;margin-top:24px;">'
        '<a href="https://saskiaspohrmann.gumroad.com" target="_blank"'
        ' style="display:inline-block;padding:12px 28px;background:#ff90e8;'
        "color:#000;font-weight:bold;border-radius:8px;text-decoration:none;"
        'font-size:1rem;">'
        "🛒 Vollversion kaufen — saskiaspohrmann.gumroad.com"
        "</a></div>"
    )

if __name__ == "__main__":
    demo.launch()
