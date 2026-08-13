import pytest

from app.services.moderation import ModerationError, moderate, sanitize


def test_moderate_ok():
    moderate("Voici un prompt de test parfaitement valide.")
    moderate("A" * 5000)


def test_moderate_empty():
    with pytest.raises(ModerationError):
        moderate("   ")


def test_moderate_too_long():
    with pytest.raises(ModerationError):
        moderate("A" * 5001)


def test_moderate_insult():
    with pytest.raises(ModerationError):
        moderate("Tu es un idiot")


def test_moderate_spam():
    with pytest.raises(ModerationError):
        moderate("https://a.com https://b.com https://c.com")


def test_sanitize():
    assert sanitize("  bonjour   le    monde  ") == "bonjour le monde"
