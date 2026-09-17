import unittest
from datetime import timedelta
from io import BytesIO

from auth import validate_email, validate_password
from files import parse_share_expiry, validate_uploaded_file


class AuthValidationTests(unittest.TestCase):
    def test_password_requires_complexity(self):
        self.assertFalse(validate_password('weakpass'))
        self.assertFalse(validate_password('Weakpass'))
        self.assertFalse(validate_password('Weakpass1'))
        self.assertTrue(validate_password('StrongPass123!'))

    def test_email_validation(self):
        self.assertTrue(validate_email('user@example.com'))
        self.assertTrue(validate_email('test.user+tag@domain.co.uk'))
        self.assertFalse(validate_email('invalid.email@'))
        self.assertFalse(validate_email('no-at-sign.com'))

    def test_share_expiry_parsing(self):
        self.assertEqual(parse_share_expiry('1h'), timedelta(hours=1))
        self.assertEqual(parse_share_expiry('1d'), timedelta(days=1))
        self.assertEqual(parse_share_expiry('7d'), timedelta(days=7))
        self.assertIsNone(parse_share_expiry('never'))
        self.assertIsNone(parse_share_expiry(''))

    def test_upload_validation_blocks_executables_and_allows_safe_files(self):
        ok, msg = validate_uploaded_file('invoice.pdf', 'application/pdf', b'%PDF-1.4')
        self.assertTrue(ok)
        self.assertIsNone(msg)

        ok, msg = validate_uploaded_file('payload.exe', 'application/x-msdownload', b'MZ')
        self.assertFalse(ok)
        self.assertIn('not allowed', msg.lower())

        ok, msg = validate_uploaded_file('malware.html', 'text/html', b'<html>hi</html>')
        self.assertFalse(ok)
        self.assertIn('not allowed', msg.lower())

        ok, msg = validate_uploaded_file('small.txt', 'text/plain', b'hello')
        self.assertTrue(ok)


if __name__ == '__main__':
    unittest.main()
