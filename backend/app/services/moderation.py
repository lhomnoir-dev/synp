import re

INSULTS = ["insulte_1", "idiot", "con", "merde"]
SPAM_PATTERN = re.compile(r"(https?://\S+|www\.\S+)")

MAX_CONTENT_LENGTH = 5000


class ModerationError(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def moderate(text: str) -> None:
    if not text or not text.strip():
        raise ModerationError("Le contenu est vide")

    if len(text) > MAX_CONTENT_LENGTH:
        raise ModerationError("Le contenu dépasse la taille maximale autorisée")

    lowered = text.lower()
    for word in INSULTS:
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            raise ModerationError("Contenu inapproprié détecté (langage injurieux)")

    if len(re.findall(SPAM_PATTERN, text)) >= 3:
        raise ModerationError("Contenu suspecté de spam (trop de liens)")


def sanitize(text: str) -> str:
    return " ".join(text.split())
