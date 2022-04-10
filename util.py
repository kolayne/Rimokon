from typing import List


def escape(where: str, what: List[str]):
    for c in what:
        assert len(c) == 1
        where = where.replace(c, '\\' + c)
    return where


def try_decode_otherwise_repr(s: bytes) -> str:
    try:
        return s.decode()
    except UnicodeDecodeError:
        return repr(s)
