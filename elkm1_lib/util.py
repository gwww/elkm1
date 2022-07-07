"""Utility functions"""

from __future__ import annotations

import ssl

TLS_VERSIONS = {
    # Unfortunately M1XEP does not support auto-negotiation for TLS
    # protocol; the user code must figure out the version to use. The
    # simplest way is to configure using the connection URL (smarter would
    # be to try to connect using each of the version, except SSL lib does
    # not report TLS error, it just closes the connection, so no easy way to
    # know a different protocol version should be tried)
    "elks": ssl.TLSVersion.TLSv1,
    "elksv1_0": ssl.TLSVersion.TLSv1,
    "elksv1_2": ssl.TLSVersion.TLSv1_2,
    "elksv1_3": ssl.TLSVersion.TLSv1_3,
}


def url_scheme_is_secure(url: str) -> bool:
    """Check if the URL is one that requires SSL/TLS."""
    scheme, _dest = url.split("://")
    return scheme.startswith("elks")


def parse_url(url: str) -> tuple[str, str, int, ssl.SSLContext | None]:
    """Parse a Elk connection string"""
    scheme, dest = url.split("://")
    host = None
    ssl_context = None
    if scheme == "elk":
        host, port = dest.split(":") if ":" in dest else (dest, "2101")
    elif TLS_VERSIONS.get(scheme):
        host, port = dest.split(":") if ":" in dest else (dest, "2601")
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        if tls := TLS_VERSIONS.get(scheme):
            ssl_context.minimum_version = tls
            ssl_context.maximum_version = tls

        ssl_context.set_ciphers(
            "DEFAULT:!aNULL:!eNULL:!MD5:!3DES:!DES:!RC4:!IDEA:!SEED:!aDSS:!SRP:!PSK"
        )
        scheme = "elks"
    elif scheme == "serial":
        host, port = dest.split(":") if ":" in dest else (dest, "115200")
    else:
        raise ValueError(f"Invalid scheme '{scheme}'")
    return (scheme, host, int(port), ssl_context)


def pretty_const(value: str) -> str:
    """Make a constant pretty for printing in GUI"""
    words = value.split("_")
    pretty = words[0].capitalize()
    for word in words[1:]:
        pretty += " " + word.lower()
    return pretty
