from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from llmjson._types import TokenType


@dataclass
class ContextFrame:
    schema_node: dict
    ctx_type:    str
    state:       str
    current_key: str = ""
    key_buffer:  str = ""
    num_chars:   int = 0
    str_chars:   int = 0


class JSONContextTracker:
    OBJ_START       = "obj_start"
    OBJ_IN_KEY      = "obj_in_key"
    OBJ_AFTER_KEY   = "obj_after_key"
    OBJ_AFTER_COLON = "obj_after_colon"
    OBJ_AFTER_VALUE = "obj_after_value"

    ARR_START       = "arr_start"
    ARR_AFTER_ITEM  = "arr_after_item"

    SC_STRING       = "sc_string"
    SC_NUMBER       = "sc_number"
    SC_LITERAL      = "sc_literal"

    INITIAL         = "initial"
    RUNNING         = "running"
    DONE            = "done"

    def __init__(self, schema: dict):
        self.root_schema  = schema
        self.stack:  list[ContextFrame] = []
        self.status: str  = self.INITIAL
        self._escape: bool = False

    def update(self, decoded_text: str) -> None:
        for ch in decoded_text:
            self._step(ch)

    def get_valid_types(self) -> set[TokenType]:
        if self.status == self.DONE:
            return {TokenType.END}

        if self.status == self.INITIAL:
            return self._start_types(self.root_schema)

        if not self.stack:
            return {TokenType.RBRACE}

        f = self.stack[-1]

        if f.ctx_type == "object":
            if f.state == self.OBJ_START:
                return {TokenType.STRING_KEY, TokenType.STRING, TokenType.RBRACE}
            if f.state == self.OBJ_IN_KEY:
                return {TokenType.STRING, TokenType.STRING_KEY}
            if f.state == self.OBJ_AFTER_KEY:
                return {TokenType.COLON}
            if f.state == self.OBJ_AFTER_COLON:
                prop = f.schema_node.get("properties", {}).get(f.current_key, {})
                return self._start_types(prop)
            if f.state == self.OBJ_AFTER_VALUE:
                return {TokenType.COMMA, TokenType.RBRACE}

        elif f.ctx_type == "array":
            items = f.schema_node.get("items", {})
            if f.state == self.ARR_START:
                return self._start_types(items) | {TokenType.RBRACKET}
            if f.state == self.ARR_AFTER_ITEM:
                return {TokenType.COMMA, TokenType.RBRACKET}

        elif f.ctx_type == "scalar":
            if f.state == self.SC_STRING:
                if f.str_chars >= 80:
                    return {TokenType.STRING}
                return {TokenType.STRING, TokenType.STRING_KEY}
            if f.state == self.SC_NUMBER:
                if f.num_chars >= 25:
                    return {TokenType.COMMA, TokenType.RBRACE, TokenType.RBRACKET}
                return {TokenType.NUMBER, TokenType.COMMA,
                        TokenType.RBRACE, TokenType.RBRACKET}
            if f.state == self.SC_LITERAL:
                return {TokenType.TRUE, TokenType.FALSE, TokenType.NULL,
                        TokenType.STRING_KEY, TokenType.COMMA,
                        TokenType.RBRACE, TokenType.RBRACKET}

        return {TokenType.STRING, TokenType.RBRACE}

    def is_complete(self) -> bool:
        return self.status == self.DONE

    def debug(self) -> dict:
        return {
            "status":      self.status,
            "stack_depth": len(self.stack),
            "top_state":   self.stack[-1].state if self.stack else None,
            "top_key":     self.stack[-1].current_key if self.stack else None,
        }

    def _step(self, ch: str) -> None:
        if self.status == self.DONE:
            return

        if self.status == self.INITIAL:
            self._push_value(ch, self.root_schema)
            if self.stack:
                self.status = self.RUNNING
            return

        if not self.stack:
            self.status = self.DONE
            return

        f = self.stack[-1]

        if f.ctx_type == "object":
            self._obj_step(f, ch)
        elif f.ctx_type == "array":
            self._arr_step(f, ch)
        elif f.ctx_type == "scalar":
            self._scalar_step(f, ch)

    def _obj_step(self, f: ContextFrame, ch: str) -> None:
        if f.state == self.OBJ_START:
            if ch in ' \t\n\r':
                return
            if ch == '"':
                f.state = self.OBJ_IN_KEY
                f.key_buffer = ""
            elif ch == '}':
                self._pop()

        elif f.state == self.OBJ_IN_KEY:
            if self._escape:
                f.key_buffer += ch
                self._escape = False
            elif ch == '\\':
                self._escape = True
            elif ch == '"':
                f.current_key = f.key_buffer
                f.state = self.OBJ_AFTER_KEY
            else:
                f.key_buffer += ch

        elif f.state == self.OBJ_AFTER_KEY:
            if ch == ':':
                f.state = self.OBJ_AFTER_COLON

        elif f.state == self.OBJ_AFTER_COLON:
            if ch in ' \t\n\r':
                return
            prop = f.schema_node.get("properties", {}).get(f.current_key, {})
            self._push_value(ch, prop)

        elif f.state == self.OBJ_AFTER_VALUE:
            if ch in ' \t\n\r':
                return
            if ch == ',':
                f.state = self.OBJ_START
            elif ch == '}':
                self._pop()

    def _arr_step(self, f: ContextFrame, ch: str) -> None:
        items = f.schema_node.get("items", {})

        if f.state == self.ARR_START:
            if ch in ' \t\n\r':
                return
            if ch == ']':
                self._pop()
            else:
                self._push_value(ch, items)

        elif f.state == self.ARR_AFTER_ITEM:
            if ch in ' \t\n\r':
                return
            if ch == ',':
                f.state = self.ARR_START
            elif ch == ']':
                self._pop()

    def _scalar_step(self, f: ContextFrame, ch: str) -> None:
        if f.state == self.SC_STRING:
            if self._escape:
                self._escape = False
            elif ch == '\\':
                self._escape = True
            elif ch == '"':
                self._pop()
            else:
                f.str_chars += 1

        elif f.state == self.SC_NUMBER:
            if ch in ',}] \t\n\r':
                self._pop()
                self._step(ch)
            else:
                f.num_chars += 1

        elif f.state == self.SC_LITERAL:
            if not ch.isalpha():
                self._pop()
                self._step(ch)

    def _push_value(self, ch: str, schema: dict) -> None:
        if ch in ' \t\n\r':
            return

        if ch == '{':
            self.stack.append(ContextFrame(schema, "object", self.OBJ_START))
        elif ch == '[':
            self.stack.append(ContextFrame(schema, "array", self.ARR_START))
        elif ch == '"':
            self.stack.append(ContextFrame(schema, "scalar", self.SC_STRING))
        elif ch in '-0123456789':
            self.stack.append(ContextFrame(schema, "scalar", self.SC_NUMBER))
        elif ch in 'tfn':
            self.stack.append(ContextFrame(schema, "scalar", self.SC_LITERAL))

    def _pop(self) -> None:
        if not self.stack:
            self.status = self.DONE
            return

        self.stack.pop()

        if not self.stack:
            self.status = self.DONE
            return

        parent = self.stack[-1]

        if parent.ctx_type == "object":
            if parent.state == self.OBJ_AFTER_COLON:
                parent.state = self.OBJ_AFTER_VALUE

        elif parent.ctx_type == "array":
            if parent.state == self.ARR_START:
                parent.state = self.ARR_AFTER_ITEM

    def _start_types(self, schema: dict) -> set[TokenType]:
        t = schema.get("type", "any")

        if t == "object" or "properties" in schema:
            return {TokenType.LBRACE}
        if t == "array" or "items" in schema:
            return {TokenType.LBRACKET}
        if t == "string":
            return {TokenType.STRING}
        if t in ("integer", "number"):
            return {TokenType.NUMBER}
        if t == "boolean":
            return {TokenType.TRUE, TokenType.FALSE}
        if t == "null":
            return {TokenType.NULL}
        if "anyOf" in schema or "oneOf" in schema:
            out: set[TokenType] = set()
            for branch in schema.get("anyOf", schema.get("oneOf", [])):
                out |= self._start_types(branch)
            return out

        return {
            TokenType.LBRACE, TokenType.LBRACKET, TokenType.STRING,
            TokenType.NUMBER, TokenType.TRUE, TokenType.FALSE, TokenType.NULL,
        }
