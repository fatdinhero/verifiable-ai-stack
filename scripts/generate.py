#!/usr/bin/env python3
"""COGNITUM Masterplan-Generator. Validiert + rendert alle Artefakte."""
import sys, yaml, argparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined, UndefinedError
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "validation"))
from masterplan_schema import Masterplan

env = Environment(loader=FileSystemLoader(str(ROOT / "templates")),
    trim_blocks=True, lstrip_blocks=True, undefined=StrictUndefined)

def load_and_validate(p):
    with open(p) as f: raw = yaml.safe_load(f)
    try:
        mp = Masterplan(**raw)
        print(f"✅ masterplan.yaml validiert (v{mp.version})")
        return mp.model_dump()
    except ValidationError as e:
        print("❌ Validation-Fehler:")
        for err in e.errors(): print(f"   - {err['loc']}: {err['msg']}")
        sys.exit(1)

def render(tpl, out, ctx):
    t = env.get_template(tpl)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(t.render(**ctx), encoding="utf-8")
    print(f"   ✅ {out}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", nargs="+", default=["all"],
        choices=["claude_md","agents_md","crews","modelfiles","docs","all"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--validate-only", action="store_true")
    args = ap.parse_args()
    mp = load_and_validate(ROOT / "governance" / "masterplan.yaml")
    if args.validate_only: return
    t = args.targets
    ctx = {"masterplan": mp}
    def r(tpl, out, extra=None):
        c = {**ctx}
        if extra: c.update(extra)
        if not args.dry_run: render(tpl, out, c)
        else: print(f"   [DRY-RUN] {out}")
    if "all" in t or "claude_md" in t: r("CLAUDE.md.j2", ROOT/"CLAUDE.md")
    if "all" in t or "agents_md" in t: r("AGENTS.md.j2", ROOT/"AGENTS.md")
    if "all" in t or "crews" in t: r("agents.yaml.j2", ROOT/"crews"/"agents.yaml")
    if "all" in t or "modelfiles" in t:
        for mod in mp.get("modules",[]):
            r("Modelfile.j2", ROOT/"ollama"/"modelfiles"/f"{mod['id'].lower()}.Modelfile", {"module": mod})
    if "all" in t or "docs" in t: r("masterplan-doc.md.j2", ROOT/"docs"/"masterplan.md")
    print("\n✅ Generierung abgeschlossen." if not args.dry_run else "\n✅ Dry-Run abgeschlossen.")

if __name__ == "__main__": main()
