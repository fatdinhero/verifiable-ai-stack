from __future__ import annotations

from enum import Enum, auto


class TokenType(Enum):
    LBRACE     = auto()   # {
    RBRACE     = auto()   # }
    LBRACKET   = auto()   # [
    RBRACKET   = auto()   # ]
    COLON      = auto()   # :
    COMMA      = auto()   # ,
    STRING     = auto()   # "..."
    NUMBER     = auto()   # 0-9, -, .
    TRUE       = auto()   # true
    FALSE      = auto()   # false
    NULL       = auto()   # null
    STRING_KEY = auto()   # "key" (property name context)
    END        = auto()   # end of sequence
