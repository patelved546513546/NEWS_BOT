"""
Minimal compatibility shim for Python 3.13+ where stdlib cgi was removed.
feedparser still imports cgi.parse_header, so we provide it locally.
"""

from email.message import Message


def parse_header(line):
    """Parse a Content-type like header.

    Returns:
        tuple[str, dict]: (main_value, params)
    """
    if not line:
        return "", {}

    msg = Message()
    msg["content-type"] = line

    main_value = msg.get_content_type()
    params = dict(msg.get_params(header="content-type", unquote=True) or [])

    params.pop("", None)
    params.pop(main_value, None)

    return main_value, params
