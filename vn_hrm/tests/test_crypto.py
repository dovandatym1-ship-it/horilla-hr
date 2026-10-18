from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.test import SimpleTestCase, override_settings

from vn_hrm.crypto import mask_identifier, protect_identifier, reveal_identifier


class IdentityEncryptionTests(SimpleTestCase):
    def test_missing_key_fails_closed(self):
        with override_settings(VN_PII_FERNET_KEY=""):
            with self.assertRaises(ImproperlyConfigured):
                protect_identifier("012345678901")

    def test_round_trip_mask_and_digest(self):
        key = Fernet.generate_key().decode("ascii")
        with override_settings(VN_PII_FERNET_KEY=key):
            ciphertext, digest = protect_identifier("0123-4567 8901")
            self.assertNotIn("012345678901", ciphertext)
            self.assertEqual(len(digest), 64)
            self.assertEqual(reveal_identifier(ciphertext), "012345678901")
            self.assertEqual(mask_identifier("012345678901"), "********8901")
            self.assertEqual(protect_identifier("012345678901")[1], digest)

    def test_invalid_identifiers_rejected(self):
        for value in ("", "a", "a/b/c", object()):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    protect_identifier(value)

    def test_invalid_key_rejected(self):
        with override_settings(VN_PII_FERNET_KEY="not-a-Fernet-key"):
            with self.assertRaises(ImproperlyConfigured):
                protect_identifier("012345678901")
