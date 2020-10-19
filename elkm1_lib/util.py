"""Utility functions"""

import ssl


def url_scheme_is_secure(url):
    """Check if the URL is one that requires SSL/TLS."""
    scheme, _dest = url.split("://")
    return scheme == "elks"


def parse_url(url):
    """Parse a Elk connection string """
    scheme, dest = url.split("://")
    host = None
    ssl_context = None
    if scheme == "elk":
        host, port = dest.split(":") if ":" in dest else (dest, 2101)
    elif scheme == "elks":
        host, port = dest.split(":") if ":" in dest else (dest, 2601)
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        ssl_context.verify_mode = ssl.CERT_NONE
    elif scheme == "serial":
        host, port = dest.split(":") if ":" in dest else (dest, 115200)
    else:
        raise ValueError("Invalid scheme '%s'" % scheme)
    return (scheme, host, int(port), ssl_context)


def pretty_const(value):
    """Make a constant pretty for printing in GUI"""
    words = value.split("_")
    pretty = words[0].capitalize()
    for word in words[1:]:
        pretty += " " + word.lower()
    return pretty


def username(elk, user_number):
    """Return name of user."""
    if 0 <= user_number < elk.users.max_elements:
        return elk.users[user_number].name
    if user_number == 201:
        return "*Program*"
    if user_number == 202:
        return "*Elk RP*"
    if user_number == 203:
        return "*Quick arm*"
    return ""
