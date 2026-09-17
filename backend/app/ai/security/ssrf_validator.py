"""SSRF Validator for Custom AI Provider Endpoints.

Enforces network-level security and prevents Server-Side Request Forgery
by disallowing localhost, loopback, private RFC-1918, link-local,
and cloud metadata endpoint IPs, both via literal IP and DNS resolution.
"""
from __future__ import annotations

import ipaddress
import socket
import urllib.parse
from app.common.exceptions import BadRequestException

DISALLOWED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    "metadata.google.internal",
    "instance-data",
}

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _is_ip_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        return True
    return any(ip in net for net in BLOCKED_IP_NETWORKS)


def validate_provider_endpoint(url: str | None, allow_http: bool = False) -> str | None:
    """
    Validates a configurable AI provider endpoint URL.
    Enforces HTTPS, rejects embedded credentials, and verifies that the hostname
    does not resolve to a private or loopback IP address (SSRF & DNS rebinding protection).
    Returns the sanitized URL if valid, or raises BadRequestException.
    """
    if not url or not url.strip():
        return None

    cleaned_url = url.strip()
    parsed = urllib.parse.urlparse(cleaned_url)

    allowed_schemes = ("https", "http") if allow_http else ("https",)
    if parsed.scheme not in allowed_schemes:
        raise BadRequestException(f"AI provider endpoint must use https scheme. (Got: '{parsed.scheme}')")

    if parsed.username or parsed.password:
        raise BadRequestException("AI provider endpoint must not contain embedded user credentials.")

    hostname = parsed.hostname
    if not hostname:
        raise BadRequestException("AI provider endpoint must contain a valid hostname.")

    hostname_lower = hostname.lower()
    if hostname_lower in DISALLOWED_HOSTS:
        raise BadRequestException(f"AI provider endpoint host '{hostname}' is not permitted (SSRF protection).")

    # 1. Check if host is a direct IP literal
    try:
        ip = ipaddress.ip_address(hostname_lower)
        if _is_ip_blocked(ip):
            raise BadRequestException(f"AI provider endpoint IP '{hostname}' is private or loopback (SSRF protection).")
        return cleaned_url
    except ValueError:
        pass

    # 2. Host is a domain name: Perform DNS resolution check
    try:
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80), proto=socket.IPPROTO_TCP)
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            try:
                resolved_ip = ipaddress.ip_address(ip_str)
                if _is_ip_blocked(resolved_ip):
                    raise BadRequestException(
                        f"AI provider endpoint host '{hostname}' resolves to private/loopback IP '{ip_str}' (SSRF protection)."
                    )
            except ValueError:
                continue
    except socket.gaierror as exc:
        # If DNS cannot be resolved in tests/offline, raise or allow if mock/test
        raise BadRequestException(f"AI provider endpoint host '{hostname}' could not be resolved: {exc}") from exc

    return cleaned_url
