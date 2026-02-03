"""Shared helpers for interpreting keyboard input."""


def is_quit_request(key: int, typing_active: bool = False) -> bool:
    """Return True when the key should trigger an application quit.

    The quit shortcut is bound to ``q``/``Q`` in addition to ``Esc``.
    While typing mode is active, the ``q`` binding is disabled so the
    character can still be entered as text, but ``Esc`` continues to
    function as an immediate exit.
    """

    if key == 27:  # Esc always quits
        return True

    if typing_active:
        return False

    return key in (ord("q"), ord("Q"))
