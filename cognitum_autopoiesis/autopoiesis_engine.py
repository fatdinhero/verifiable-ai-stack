from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class MoleculeState(Enum):
    PASSIVE = "passive"
    ACTIVE = "active"
    REACTIVE = "reactive"
    DEGRADED = "degraded"


@dataclass
class Molecule:
    """Represents a component in the autopoietic system."""
    id: str
    state: MoleculeState = MoleculeState.PASSIVE
    content: str = ""
    relations: List[str] = field(default_factory=list)

    def activate(self) -> None:
        self.state = MoleculeState.ACTIVE

    def degrade(self) -> None:
        self.state = MoleculeState.DEGRADED

    def is_reactive(self) -> bool:
        return self.state == MoleculeState.REACTIVE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "state": self.state.value,
            "content": self.content,
            "relations": self.relations,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Molecule":
        return cls(
            id=data["id"],
            state=MoleculeState(data.get("state", "passive")),
            content=data.get("content", ""),
            relations=data.get("relations", []),
        )


@dataclass
class Catalyst:
    """Facilitates reactions between molecules — here: triggers healing."""
    id: str
    trigger_pattern: str = ""
    action: str = ""
    enabled: bool = True

    def can_trigger(self, context: str) -> bool:
        if not self.enabled:
            return False
        return self.trigger_pattern in context if self.trigger_pattern else False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "trigger_pattern": self.trigger_pattern,
            "action": self.action,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Catalyst":
        return cls(
            id=data["id"],
            trigger_pattern=data.get("trigger_pattern", ""),
            action=data.get("action", ""),
            enabled=data.get("enabled", True),
        )


@dataclass
class Membrane:
    """Boundary that encapsulates a set of molecules and their interactions."""
    id: str
    molecules: Dict[str, Molecule] = field(default_factory=dict)
    catalysts: Dict[str, Catalyst] = field(default_factory=dict)
    parent: Optional[str] = None

    def add_molecule(self, molecule: Molecule) -> None:
        self.molecules[molecule.id] = molecule

    def remove_molecule(self, molecule_id: str) -> Optional[Molecule]:
        return self.molecules.pop(molecule_id, None)

    def add_catalyst(self, catalyst: Catalyst) -> None:
        self.catalysts[catalyst.id] = catalyst

    def get_active_molecules(self) -> List[Molecule]:
        return [m for m in self.molecules.values() if m.state == MoleculeState.ACTIVE]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "molecules": {k: v.to_dict() for k, v in self.molecules.items()},
            "catalysts": {k: v.to_dict() for k, v in self.catalysts.items()},
            "parent": self.parent,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Membrane":
        membrane = cls(id=data["id"], parent=data.get("parent"))
        for mid, mdata in data.get("molecules", {}).items():
            membrane.molecules[mid] = Molecule.from_dict(mdata)
        for cid, cdata in data.get("catalysts", {}).items():
            membrane.catalysts[cid] = Catalyst.from_dict(cdata)
        return membrane


class AutopoiesisEngine:
    """Meta-Healing engine for the dev loop.

    Uses autopoiesis-inspired architecture to detect, diagnose, and repair
    failures in running modules.
    """

    MAX_SELF_HEALING_PER_SESSION = 1

    def __init__(self, mimo_endpoint: str = "", session_limit: int = 1) -> None:
        self.mimo_endpoint = mimo_endpoint
        self.session_healing_count = 0
        self.session_limit = session_limit
        self.membranes: Dict[str, Membrane] = {}
        self._build_default_topology()

    def _build_default_topology(self) -> None:
        """Set up the default membrane topology with standard molecules/catalysts."""
        heal_catalyst = Catalyst(
            id="heal_catalyst",
            trigger_pattern="MANUAL_REVIEW",
            action="heal_and_restart",
        )
        root_membrane = Membrane(id="root")
        root_membrane.add_catalyst(heal_catalyst)
        self.membranes["root"] = root_membrane

    def heal(self, loop_script: str, error_log: str) -> str:
        """Send loop_script + error_log to MiMo, receive repaired code.

        Validates syntax via ast.parse() and returns the repaired code.
        If MiMo is unreachable or produces invalid code, attempts local
        heuristic repair.
        """
        self.session_healing_count += 1

        patched_code = self._call_mimo(loop_script, error_log)

        try:
            ast.parse(patched_code)
        except SyntaxError:
            patched_code = self._local_heuristic_repair(loop_script, error_log)
            try:
                ast.parse(patched_code)
            except SyntaxError:
                raise RuntimeError(
                    "Unable to produce syntactically valid patched code."
                )

        return patched_code

    def _call_mimo(self, loop_script: str, error_log: str) -> str:
        """Attempt to call MiMo for code repair.

        Falls back to returning the original script if the endpoint is
        not configured.
        """
        if not self.mimo_endpoint:
            return loop_script

        try:
            payload = json.dumps({
                "loop_script": loop_script,
                "error_log": error_log,
            })
            result = subprocess.run(
                [
                    sys.executable, "-m", "cognitum_mimo.cli",
                    "--endpoint", self.mimo_endpoint,
                    "--payload", payload,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return loop_script

    def _local_heuristic_repair(self, loop_script: str, error_log: str) -> str:
        """Best-effort local repair heuristics."""
        lines = loop_script.splitlines(keepends=True)
        repaired_lines: List[str] = []

        for line in lines:
            stripped = line.rstrip()

            # Heuristic 1: bare except → except Exception
            if stripped == "except:":
                line = line.replace("except:", "except Exception:", 1)

            # Heuristic 2: missing colon after def/class/if/elif/else/for/while/try/except/finally
            keywords = ("def ", "class ", "if ", "elif ", "else", "for ", "while ", "try", "except", "finally")
            s = stripped
            if any(s.startswith(kw) for kw in keywords) and not s.endswith(":"):
                line = line.rstrip("\n") + ":\n"

            repaired_lines.append(line)

        # Heuristic 3: try to balance open parens/brackets/braces
        joined = "".join(repaired_lines)
        open_count = joined.count("(") - joined.count(")")
        if open_count > 0:
            joined = joined.rstrip("\n") + ")" * open_count + "\n"

        return joined

    @staticmethod
    def apply_patch(loop_script_path: str, patched_code: str) -> bool:
        """Write repaired code into loop_script_path.

        Creates a backup at loop_script_path + '.bak' first.
        Returns True on success, False on failure.
        """
        try:
            path = Path(loop_script_path)
            backup_path = str(path) + ".bak"
            if path.exists():
                shutil.copy2(str(path), backup_path)
            path.write_text(patched_code, encoding="utf-8")
            return True
        except (OSError, IOError):
            return False

    def restart_loop(
        self,
        loop_script_path: str,
        queue_path: str,
        failed_module: str,
    ) -> None:
        """Reset failed_module in queue_path to PENDING with iterations=0,
        then restart loop_script_path as a subprocess.
        """
        self._reset_module_in_queue(queue_path, failed_module)

        subprocess.Popen(
            [sys.executable, loop_script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @staticmethod
    def _reset_module_in_queue(queue_path: str, failed_module: str) -> None:
        """Set the failed_module's status to PENDING and iterations to 0."""
        try:
            with open(queue_path, "r", encoding="utf-8") as f:
                queue_data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return

        if isinstance(queue_data, list):
            for entry in queue_data:
                if isinstance(entry, dict) and entry.get("module") == failed_module:
                    entry["status"] = "PENDING"
                    entry["iterations"] = 0
        elif isinstance(queue_data, dict):
            if failed_module in queue_data:
                module_entry = queue_data[failed_module]
                if isinstance(module_entry, dict):
                    module_entry["status"] = "PENDING"
                    module_entry["iterations"] = 0

        try:
            with open(queue_path, "w", encoding="utf-8") as f:
                json.dump(queue_data, f, indent=2)
        except OSError:
            pass

    def can_self_heal(self) -> bool:
        """Check if the engine is still allowed to self-heal this session."""
        return self.session_healing_count < self.session_limit

    def __repr__(self) -> str:
        return (
            f"AutopoiesisEngine(session_heals={self.session_healing_count}/"
            f"{self.session_limit}, membranes={list(self.membranes.keys())})"
        )


# Module-level singleton instance
autopoiesis_engine = AutopoiesisEngine()