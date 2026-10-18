"""Explicitly keyed encryption and HMAC for sensitive employee identifiers.

Deployers MUST set an independent VN_PII_FERNET_KEY; neither plaintext storage
nor derivation from Django SECRET_KEY is allowed. Plan key rotation separately.
"""

import base64
import binascii
import hashlib
import hmac
import re

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError


def _key():
    raw = getattr(settings, "VN_PII_FERNET_KEY", "")
    if not raw:
        raise ImproperlyConfigured(
            "VN_PII_FERNET_KEY is required before storing personal identifiers."
        )
    try:
        key = raw.encode("ascii") if isinstance(raw, str) else raw
        secret = base64.urlsafe_b64decode(key)
        if len(secret) != 32:
            raise ValueError("Invalid Fernet key length")
        Fernet(key)
    except (ValueError, TypeError, UnicodeError, binascii.Error) as exc:
        raise ImproperlyConfigured("Invalid VN_PII_FERNET_KEY") from exc
    return key, secret


def normalize_identifier(value):
    if not isinstance(value, str):
        raise ValidationError("Mã định danh phải là chuỗi.")
    normalized = re.sub(r"[\s-]", "", value).upper()
    if not 4 <= len(normalized) <= 32 or not normalized.isalnum():
        raise ValidationError("Mã định danh phải gồm 4–32 ký tự chữ hoặc số.")
    return normalized


def protect_identifier(value):
    normalized = normalize_identifier(value)
    key, secret = _key()
    encrypted = Fernet(key).encrypt(normalized.encode("utf-8")).decode("ascii")
    digest = hmac.new(secret, normalized.encode("utf-8"), hashlib.sha256).hexdigest()
    return encrypted, digest


def reveal_identifier(ciphertext):
    key, _ = _key()
    try:
        return Fernet(key).decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, TypeError, ValueError, UnicodeError) as exc:
        raise ValidationError("Không thể giải mã thông tin định danh.") from exc


def mask_identifier(identifier):
    value = normalize_identifier(identifier)
    return "*" * max(len(value) - 4, 0) + value[-4:]
