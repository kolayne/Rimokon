from typing import Optional


def cmd_get_action_name(s: Optional[str]) -> Optional[str]:
    """
    Extract action name from a command string with, optionally, leading spaces followed by leading slashes.
    """
    if s:
        return s.lstrip().lstrip('/').split()[0].lower()

def cmd_get_rest(s: str, cut_first_whitespace: bool = True) -> str:
    """
    Cut the first word of the string and, optionally, the first whitespace symbol after it (default).
    Return the rest.
    """
    s = s.lstrip()
    i = len(s.split()[0])

    if cut_first_whitespace:
        i += 1
    return s[i:]
