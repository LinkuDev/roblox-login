from app.domain.models import Credential, Proxy


def test_credential_parse():
    c = Credential.parse("user1:pass1:SECRET")
    assert c.username == "user1"
    assert c.password == "pass1"
    assert c.totp_secret == "SECRET"


def test_credential_repr_masks_password():
    c = Credential("user", "supersecret")
    assert "supersecret" not in repr(c)


def test_proxy_parse_variants():
    assert Proxy.parse("1.2.3.4:8080").url == "http://1.2.3.4:8080"
    p = Proxy.parse("1.2.3.4:8080:user:pw")
    assert p.username == "user" and p.password == "pw"
    p2 = Proxy.parse("socks5://u:p@host:1080")
    assert p2.scheme == "socks5" and p2.host == "host"
