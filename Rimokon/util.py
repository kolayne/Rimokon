from typing import List, Optional


def escape(where: str, what: List[str]):
    # If there is a backslash in `what`, it must come first
    if '\\' in what:
        what = ['\\'] + [c for c in what if c != '\\']

    for c in what:
        assert len(c) == 1
        where = where.replace(c, '\\' + c)
    return where


def try_decode_otherwise_repr(s: bytes) -> str:
    try:
        return s.decode()
    except UnicodeDecodeError:
        return repr(s)


def cmd_get_action_name(s: Optional[str]) -> Optional[str]:
    """
    Extract action from the command string with optional leading slash
    """
    if s:
        return s.split()[0].lstrip('/').lower()

def cmd_get_rest(s: str) -> str:
    """
    Cuts the first word of the string and the first whitespace symbol
    after it, returns the rest
    """
    return s[len(s.split()[0])+1:]
