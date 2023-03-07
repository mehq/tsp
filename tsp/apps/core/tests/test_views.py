from django.test.client import Client
from django.urls import reverse


def test_health_check_returns_ok(client: Client):
    assert client.get(reverse("health-check")).content == b"ok"
