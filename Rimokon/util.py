# TODO: Move these to __main__.py


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
