"""Unit tests for SSRF validation and IP address blocking."""

import pytest
from clipora.core.errors import SSRFError
from clipora.core.netutil import is_ip_address_allowed, validate_url_ssrf_safe

def test_blocked_ip_addresses():
    blocked_ips = [
        "127.0.0.1",
        "127.0.1.1",
        "10.0.0.1",
        "10.254.254.254",
        "172.16.0.1",
        "172.31.255.255",
        "192.168.1.1",
        "169.254.169.254", # AWS metadata
        "169.254.1.1",     # Link-local
        "::1",             # IPv6 loopback
        "fe80::1",         # IPv6 link-local
        "fc00::1",         # IPv6 ULA
    ]
    for ip in blocked_ips:
        assert not is_ip_address_allowed(ip), f"IP {ip} should be blocked"

def test_allowed_public_ips():
    allowed_ips = [
        "8.8.8.8",
        "1.1.1.1",
        "142.250.190.46",
    ]
    for ip in allowed_ips:
        assert is_ip_address_allowed(ip), f"IP {ip} should be allowed"

def test_validate_url_ssrf_rejects_disallowed_schemes():
    with pytest.raises(SSRFError, match="Disallowed scheme"):
        validate_url_ssrf_safe("ftp://example.com/video.mp4")

    with pytest.raises(SSRFError, match="Disallowed scheme"):
        validate_url_ssrf_safe("file:///etc/passwd")

def test_validate_url_ssrf_rejects_private_ips():
    with pytest.raises(SSRFError, match="blocked"):
        validate_url_ssrf_safe("http://127.0.0.1:8000/api")

    with pytest.raises(SSRFError, match="blocked"):
        validate_url_ssrf_safe("http://169.254.169.254/latest/meta-data/")

    with pytest.raises(SSRFError, match="blocked"):
        validate_url_ssrf_safe("http://192.168.1.100/video.mp4")
