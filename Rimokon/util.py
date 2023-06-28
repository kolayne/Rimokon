from typing import Optional


def cmd_get_action_name(s: Optional[str]) -> Optional[str]:
    """
    Extract action name from a command string with, optionally, leading spaces followed by leading slashes.
    """
    if s:
        s = s.lstrip().lstrip('/')
        if s == '' or s[0].isspace():
            return ''  # Empty action name
        else:
            return s.split()[0].lower()

def cmd_get_rest(s: str, cut_first_whitespace: bool = True) -> str:
    """
    Cut the first word of the string and, optionally, the first whitespace symbol after it (default).
    Return the rest.
    """
    s = s.lstrip()
    try:
        i = len(s.split()[0])
    except IndexError:
        # Don't know if this can ever happen (white-space only message in Telegram??) but just in case
        return ''

    if cut_first_whitespace:
        i += 1
    return s[i:]
