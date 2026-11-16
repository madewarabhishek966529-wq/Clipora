"""SSRF & Security Shield: safe DNS resolution and URL validation."""

import ipaddress
import socket
from urllib.parse import urlparse
from clipora.core.errors import SSRFError

# Disallowed IPv4 networks
BLOCKED_IPV4_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),          # Current network
    ipaddress.ip_network("10.0.0.0/8"),         # RFC1918 private
    ipaddress.ip_network("100.64.0.0/10"),      # Shared Address Space (CGNAT)
    ipaddress.ip_network("127.0.0.0/8"),        # Loopback
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local & Cloud metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),      # RFC1918 private
    ipaddress.ip_network("192.0.0.0/24"),       # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),       # TEST-NET-1
    ipaddress.ip_network("192.88.99.0/24"),     # 6to4 Relay Anycast
    ipaddress.ip_network("192.168.0.0/16"),     # RFC1918 private
    ipaddress.ip_network("198.18.0.0/15"),      # Network benchmark tests
    ipaddress.ip_network("198.51.100.0/24"),    # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),     # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),        # Multicast
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved for future use
    ipaddress.ip_network("255.255.255.255/32"), # Broadcast
]

# Disallowed IPv6 networks
BLOCKED_IPV6_NETWORKS = [
    ipaddress.ip_network("::/128"),             # Unspecified
    ipaddress.ip_network("::1/128"),           # Loopback
    ipaddress.ip_network("fc00::/7"),          # Unique Local Address (ULA)
    ipaddress.ip_network("fe80::/10"),         # Link-local unicast
    ipaddress.ip_network("ff00::/8"),          # Multicast
    ipaddress.ip_network("2001:db8::/32"),     # Documentation
]

def is_ip_address_allowed(ip_str: str) -> bool:
    """Return True if an IP address string is public and routable, False if private/reserved/loopback."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False

    if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        return False

    if isinstance(ip, ipaddress.IPv4Address):
        for net in BLOCKED_IPV4_NETWORKS:
            if ip in net:
                return False
    elif isinstance(ip, ipaddress.IPv6Address):
        for net in BLOCKED_IPV6_NETWORKS:
            if ip in net:
                return False

    return True

def resolve_and_validate_host(hostname: str) -> list[str]:
    """Resolve a hostname via DNS and ensure all resolved IP addresses are safe.
    
    Raises:
        SSRFError if hostname resolves to private, loopback, or metadata addresses.
    """
    if not hostname:
        raise SSRFError("Empty hostname provided.")

    # Check if host is already an IP address
    try:
        ipaddress.ip_address(hostname)
        if not is_ip_address_allowed(hostname):
            raise SSRFError(f"Target IP address '{hostname}' is blocked (private/loopback/cloud metadata).")
        return [hostname]
    except ValueError:
        pass

    try:
        # Resolve hostname for both IPv4 and IPv6
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise SSRFError(f"Failed to resolve hostname '{hostname}': {e}") from e

    resolved_ips: list[str] = []
    for entry in addr_info:
        sockaddr = entry[4]
        ip_str = sockaddr[0]
        if not is_ip_address_allowed(ip_str):
            raise SSRFError(f"Host '{hostname}' resolved to blocked IP '{ip_str}' (private/loopback/cloud metadata).")
        resolved_ips.append(ip_str)

    if not resolved_ips:
        raise SSRFError(f"Host '{hostname}' did not resolve to any usable IP addresses.")

    return resolved_ips

def validate_url_ssrf_safe(url: str, allowed_schemes: tuple[str, ...] = ("http", "https")) -> str:
    """Validate that a URL is well-formed, uses an allowed scheme, and does not point to internal/private targets.
    
    Returns:
        The validated URL string if safe.
    Raises:
        SSRFError if the URL fails safety checks.
    """
    if not url or not isinstance(url, str):
        raise SSRFError("URL must be a non-empty string.")

    url = url.strip()
    parsed = urlparse(url)

    if parsed.scheme.lower() not in allowed_schemes:
        raise SSRFError(f"Disallowed scheme '{parsed.scheme}'. Allowed schemes: {allowed_schemes}")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFError(f"Missing hostname in URL: '{url}'")

    resolve_and_validate_host(hostname)
    return url
