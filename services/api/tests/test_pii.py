"""Unit tests for PII masking module."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

api_root = Path(__file__).resolve().parents[1]
if str(api_root) not in sys.path:
    sys.path.insert(0, str(api_root))

from vela.pii import (
    is_pii_masking_enabled,
    is_valid_iban,
    is_valid_luhn,
    mask_pii,
    mask_pii_lines,
)


class TestPIIValidationHelpers(unittest.TestCase):
    def test_iban_validation(self):
        # Valid IBANs
        self.assertTrue(is_valid_iban("DE89 3704 0044 0532 0130 00"))
        self.assertTrue(is_valid_iban("DE89370400440532013000"))
        self.assertTrue(is_valid_iban("FR76 3000 6000 0112 3456 7890 189"))
        self.assertTrue(is_valid_iban("GB29 NWBK 6016 1331 9268 19"))
        self.assertTrue(is_valid_iban("NL91 ABNA 0417 1643 00"))
        self.assertTrue(is_valid_iban("ES91 2100 0418 4502 0005 1332"))

        # Invalid checksum or formats
        self.assertFalse(is_valid_iban("DE00 0000 0000 0000 0000 00"))
        self.assertFalse(is_valid_iban("DE89 3704 0044 0532 0130 01"))
        self.assertFalse(is_valid_iban("DE12 345"))  # too short
        self.assertFalse(is_valid_iban("NOT_AN_IBAN_AT_ALL"))

    def test_luhn_validation(self):
        # Valid cards (Visa, Mastercard, Amex, Mir)
        self.assertTrue(is_valid_luhn("4532 0150 1234 5671"))
        self.assertTrue(is_valid_luhn("4532-0150-1234-5671"))
        self.assertTrue(is_valid_luhn("4532015012345671"))
        self.assertTrue(is_valid_luhn("5555 5555 5555 4444"))
        self.assertTrue(is_valid_luhn("3782 822463 10005"))
        self.assertTrue(is_valid_luhn("2200 1234 5678 9019"))

        # Invalid Luhn checksum or invalid card formats
        self.assertFalse(is_valid_luhn("4532 0150 1234 5670"))
        self.assertFalse(is_valid_luhn("0000 0000 0000 0000"))  # all zeros rejected
        self.assertFalse(is_valid_luhn("12345"))  # too short
        self.assertFalse(is_valid_luhn("2026-03-15"))  # date, only 8 digits


class TestPIIEnvironmentFlag(unittest.TestCase):
    def test_flag_defaults_to_true(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(is_pii_masking_enabled())

    def test_flag_can_be_disabled(self):
        for val in ("false", "False", "0", "no", "off"):
            with patch.dict(os.environ, {"PII_MASKING": val}):
                self.assertFalse(is_pii_masking_enabled())

    def test_mask_pii_respects_flag(self):
        sample = "Kontoinhaber: Max Mustermann; IBAN: DE89 3704 0044 0532 0130 00"
        with patch.dict(os.environ, {"PII_MASKING": "false"}):
            self.assertEqual(mask_pii(sample), sample)
            # force=True overrides disabled flag
            self.assertIn("[REDACTED_NAME]", mask_pii(sample, force=True))


class TestPIICorpusStatementMasking(unittest.TestCase):
    """Test realistic corpus of >= 20 bank statement lines in DE, EN, and RU."""

    def setUp(self):
        self.corpus = [
            # 1. German: Kontoinhaber in statement header
            {
                "raw": "Kontoinhaber: Max Mustermann",
                "leaks": ["Max Mustermann"],
                "expected_contains": ["Kontoinhaber:", "[REDACTED_NAME]"],
            },
            # 2. German: Adresse header
            {
                "raw": "Adresse: Hauptstraße 10, 10115 Berlin",
                "leaks": ["Hauptstraße 10, 10115 Berlin"],
                "expected_contains": ["Adresse:", "[REDACTED_ADDRESS]"],
            },
            # 3. German: IBAN with spaces
            {
                "raw": "Kontoauszug IBAN: DE89 3704 0044 0532 0130 00",
                "leaks": ["DE89 3704 0044 0532 0130 00"],
                "expected_contains": ["[REDACTED_IBAN]"],
            },
            # 4. German: CSV transaction row with date, merchant, amount, and Visa card
            {
                "raw": "05.10.2026;REWE Markt;-63,47 EUR;Kartenzahlung 4532 0150 1234 5671",
                "leaks": ["4532 0150 1234 5671"],
                "expected_contains": ["05.10.2026", "REWE Markt", "-63,47 EUR", "[REDACTED_CARD]"],
            },
            # 5. German: Regular transaction without PII (ACME GmbH salary)
            {
                "raw": "01.10.2026;ACME GmbH;Gehalt Oktober;2.500,00;3.100,00",
                "leaks": [],
                "expected_contains": ["01.10.2026", "ACME GmbH", "Gehalt Oktober", "2.500,00", "3.100,00"],
            },
            # 6. German: Rent transaction without PII
            {
                "raw": "02.10.2026;Hausverwaltung Meier;Miete Oktober;-850,00;2.250,00",
                "leaks": [],
                "expected_contains": ["02.10.2026", "Hausverwaltung Meier", "-850,00", "2.250,00"],
            },
            # 7. German: German customer service hotline (+49...)
            {
                "raw": "Support hotline: +49 30 12345678, erreichbar Mo-Fr",
                "leaks": ["+49 30 12345678"],
                "expected_contains": ["[REDACTED_PHONE]", "erreichbar Mo-Fr"],
            },
            # 8. German: Merchant support email
            {
                "raw": "Customer contact: service@rewe.de fuer Rueckfragen",
                "leaks": ["service@rewe.de"],
                "expected_contains": ["[REDACTED_EMAIL]", "fuer Rueckfragen"],
            },
            # 9. English: Account holder header
            {
                "raw": "Account holder: Johnathan Doe",
                "leaks": ["Johnathan Doe"],
                "expected_contains": ["Account holder:", "[REDACTED_NAME]"],
            },
            # 10. English: Address header
            {
                "raw": "Address: 221B Baker Street, London NW1 6XE",
                "leaks": ["221B Baker Street, London NW1 6XE"],
                "expected_contains": ["Address:", "[REDACTED_ADDRESS]"],
            },
            # 11. English: British IBAN
            {
                "raw": "Bank transfer to GB29 NWBK 6016 1331 9268 19 confirmed",
                "leaks": ["GB29 NWBK 6016 1331 9268 19"],
                "expected_contains": ["[REDACTED_IBAN]", "confirmed"],
            },
            # 12. English: Card transaction with Spotify UK and USD amount
            {
                "raw": "2026-03-01;Spotify UK;-12.99 USD;Card 5555 5555 5555 4444",
                "leaks": ["5555 5555 5555 4444"],
                "expected_contains": ["2026-03-01", "Spotify UK", "-12.99 USD", "[REDACTED_CARD]"],
            },
            # 13. English: Netflix transaction (preserves merchant and amount)
            {
                "raw": "2026-03-02;Netflix Subscription;-15.99 EUR",
                "leaks": [],
                "expected_contains": ["2026-03-02", "Netflix Subscription", "-15.99 EUR"],
            },
            # 14. English: Employer direct deposit (positive amount)
            {
                "raw": "2026-03-03;Employer Direct Deposit;+3200.00 EUR",
                "leaks": [],
                "expected_contains": ["2026-03-03", "Employer Direct Deposit", "+3200.00 EUR"],
            },
            # 15. English: Combined email and UK telephone
            {
                "raw": "Queries: help@spotify.com or +44 20 7946 0958",
                "leaks": ["help@spotify.com", "+44 20 7946 0958"],
                "expected_contains": ["[REDACTED_EMAIL]", "[REDACTED_PHONE]"],
            },
            # 16. English/German: International 0049 phone format
            {
                "raw": "International phone: 0049 170 1234567 for inquiries",
                "leaks": ["0049 170 1234567"],
                "expected_contains": ["[REDACTED_PHONE]", "for inquiries"],
            },
            # 17. Russian: Владелец счёта header
            {
                "raw": "Владелец счёта: Смирнов Алексей Петрович",
                "leaks": ["Смирнов Алексей Петрович"],
                "expected_contains": ["Владелец счёта:", "[REDACTED_NAME]"],
            },
            # 18. Russian: Адрес header
            {
                "raw": "Адрес: г. Москва, ул. Ленина, д. 25, кв. 14",
                "leaks": ["г. Москва, ул. Ленина, д. 25, кв. 14"],
                "expected_contains": ["Адрес:", "[REDACTED_ADDRESS]"],
            },
            # 19. Russian: Mir card payment and Ruble amount
            {
                "raw": "15.03.2026;Yandex Food;-1200.50 RUB;Карта 2200 1234 5678 9019",
                "leaks": ["2200 1234 5678 9019"],
                "expected_contains": ["15.03.2026", "Yandex Food", "-1200.50 RUB", "[REDACTED_CARD]"],
            },
            # 20. Russian: Transfer by Russian phone number (+7...)
            {
                "raw": "16.03.2026;Перевод по номеру +7 (999) 123-45-67;-500.00 RUB",
                "leaks": ["+7 (999) 123-45-67"],
                "expected_contains": ["16.03.2026", "Перевод по номеру", "[REDACTED_PHONE]", "-500.00 RUB"],
            },
            # 21. Russian: Contact email and continuous Russian phone
            {
                "raw": "Контакты: info@yandex.ru или +79991234567",
                "leaks": ["info@yandex.ru", "+79991234567"],
                "expected_contains": ["[REDACTED_EMAIL]", "[REDACTED_PHONE]"],
            },
            # 22. Central Asia: Uzbekistan phone number (+998...)
            {
                "raw": "Ташкент офис: +998 90 123 45 67",
                "leaks": ["+998 90 123 45 67"],
                "expected_contains": ["Ташкент офис:", "[REDACTED_PHONE]"],
            },
            # 23. French: French IBAN in semicolon CSV preamble
            {
                "raw": "IBAN;FR76 3000 6000 0112 3456 7890 189;;;",
                "leaks": ["FR76 3000 6000 0112 3456 7890 189"],
                "expected_contains": ["IBAN;[REDACTED_IBAN];;;"],
            },
            # 24. Dutch: Netherlands IBAN
            {
                "raw": "IBAN: NL91 ABNA 0417 1643 00",
                "leaks": ["NL91 ABNA 0417 1643 00"],
                "expected_contains": ["IBAN: [REDACTED_IBAN]"],
            },
            # 25. Amex: Hyphenated Amex card payment
            {
                "raw": "Amex card payment: 3782-822463-10005;-45,00 EUR",
                "leaks": ["3782-822463-10005"],
                "expected_contains": ["Amex card payment: [REDACTED_CARD]", "-45,00 EUR"],
            },
        ]

    def test_corpus_count_at_least_20(self):
        self.assertGreaterEqual(len(self.corpus), 20)

    def test_corpus_no_pii_leaks_and_preserves_financial_data(self):
        for idx, item in enumerate(self.corpus):
            raw = item["raw"]
            masked = mask_pii(raw)

            # Check no leaks
            for leak in item["leaks"]:
                self.assertNotIn(
                    leak,
                    masked,
                    f"Corpus item #{idx+1} leaked PII '{leak}'. Raw: '{raw}', Masked: '{masked}'",
                )

            # Check expected preservation and redactions
            for expected in item["expected_contains"]:
                self.assertIn(
                    expected,
                    masked,
                    f"Corpus item #{idx+1} missing expected substring '{expected}'. Raw: '{raw}', Masked: '{masked}'",
                )

    def test_mask_pii_lines(self):
        raw_lines = [item["raw"] for item in self.corpus[:5]]
        masked_lines = mask_pii_lines(raw_lines)
        self.assertEqual(len(masked_lines), 5)
        for masked, item in zip(masked_lines, self.corpus[:5]):
            for expected in item["expected_contains"]:
                self.assertIn(expected, masked)

    def test_multiline_csv_preserves_structure(self):
        doc = (
            "Kontoauszug Girokonto;;;;\n"
            "Kontoinhaber: Max Mustermann\n"
            "Adresse: Musterstr. 12, 10115 Berlin\n"
            "IBAN;DE89 3704 0044 0532 0130 00;;;\n"
            "Buchungstag;Verwendungszweck;Betrag;Saldo\n"
            "01.10.2026;ACME GmbH Gehalt;2500,00;3100,00\n"
            "02.10.2026;Hausverwaltung Meier Miete;-850,00;2250,00\n"
            "05.10.2026;REWE Markt Kartenzahlung 4532 0150 1234 5671;-63,47;2186,53\n"
        )
        masked = mask_pii(doc)
        self.assertNotIn("Max Mustermann", masked)
        self.assertNotIn("Musterstr. 12", masked)
        self.assertNotIn("DE89 3704 0044 0532 0130 00", masked)
        self.assertNotIn("4532 0150 1234 5671", masked)

        # Financial integrity preserved
        self.assertIn("01.10.2026;ACME GmbH Gehalt;2500,00;3100,00", masked)
        self.assertIn("02.10.2026;Hausverwaltung Meier Miete;-850,00;2250,00", masked)
        self.assertIn("05.10.2026;REWE Markt Kartenzahlung [REDACTED_CARD];-63,47;2186,53", masked)
        self.assertIn("Kontoinhaber: [REDACTED_NAME]", masked)
        self.assertIn("Adresse: [REDACTED_ADDRESS]", masked)
        self.assertIn("IBAN;[REDACTED_IBAN];;;", masked)


class TestPIIRegressionsReviewAttempt2(unittest.TestCase):
    """Regressions identified during orchestrator review (attempt 1 to 2)."""

    def test_nineteen_digit_cards_and_groupings(self):
        # 19-digit cards (4-4-4-4-3)
        valid_19_spaced = "4000 0000 0000 0000 006"
        valid_19_hyphen = "4000-0000-0000-0000-006"
        valid_19_cont = "4000000000000000006"
        invalid_19 = "4000 0000 0000 0000 007"

        self.assertTrue(is_valid_luhn(valid_19_spaced))
        self.assertTrue(is_valid_luhn(valid_19_hyphen))
        self.assertTrue(is_valid_luhn(valid_19_cont))
        self.assertFalse(is_valid_luhn(invalid_19))

        self.assertEqual(mask_pii(valid_19_spaced, force=True), "[REDACTED_CARD]")
        self.assertEqual(mask_pii(valid_19_hyphen, force=True), "[REDACTED_CARD]")
        self.assertEqual(mask_pii(valid_19_cont, force=True), "[REDACTED_CARD]")
        self.assertEqual(mask_pii(invalid_19, force=True), invalid_19)

        # Other standard card groupings
        diners_14 = "3000 123456 1233"
        self.assertTrue(is_valid_luhn(diners_14))
        self.assertEqual(mask_pii(diners_14, force=True), "[REDACTED_CARD]")

        visa_13 = "4000 1234 5678 8"
        self.assertTrue(is_valid_luhn(visa_13))
        self.assertEqual(mask_pii(visa_13, force=True), "[REDACTED_CARD]")

    def test_phone_adjacent_amounts_and_dotted_formats(self):
        # Case 1: Phone adjacent to amount (previously swallowed 1200.50 EUR)
        s1 = "+491701234567 1200.50 EUR"
        self.assertEqual(mask_pii(s1, force=True), "[REDACTED_PHONE] 1200.50 EUR")

        # Case 2: Dotted phone number (previously failed decimal ending check)
        s2 = "Phone: +49.170.123.45.67"
        self.assertEqual(mask_pii(s2, force=True), "Phone: [REDACTED_PHONE]")

        # Case 3: Dotted phone with sentence punctuation
        s3 = "Phone: +49.170.123.45.67."
        self.assertEqual(mask_pii(s3, force=True), "Phone: [REDACTED_PHONE].")

        # Case 4: Dotted phone with following amount
        s4 = "Phone: +49.170.123.45.67 and amount 500.00 EUR"
        self.assertEqual(mask_pii(s4, force=True), "Phone: [REDACTED_PHONE] and amount 500.00 EUR")

        # Case 5: Spaced phone with adjacent decimal amount
        s5 = "Phone: +49 170 12 34 56 1200.50 EUR"
        self.assertEqual(mask_pii(s5, force=True), "Phone: [REDACTED_PHONE] 1200.50 EUR")

        # Case 6: Slashed phone
        s6 = "Hotline: +49/170/1234567"
        self.assertEqual(mask_pii(s6, force=True), "Hotline: [REDACTED_PHONE]")

        # Case 7: Continuous phone in transaction
        s7 = "Transaction +491701234567, amount: -150.00 EUR"
        self.assertEqual(mask_pii(s7, force=True), "Transaction [REDACTED_PHONE], amount: -150.00 EUR")

    def test_financial_amounts_and_dates_not_corrupted(self):
        # Pure dates
        d1 = "Date: 2026-03-15 and 01.10.2026"
        self.assertEqual(mask_pii(d1, force=True), d1)

        # Monetary amounts with plus or minus
        a1 = "Profit: +100.00 EUR"
        self.assertEqual(mask_pii(a1, force=True), a1)

        a2 = "Big amount: +1000000.00 EUR"
        self.assertEqual(mask_pii(a2, force=True), a2)

        a3 = "Large balance: +1000000000 EUR"
        self.assertEqual(mask_pii(a3, force=True), a3)

        a4 = "German amount: +1.000.000,00 EUR"
        self.assertEqual(mask_pii(a4, force=True), a4)

        a5 = "Balance: -45,00 EUR"
        self.assertEqual(mask_pii(a5, force=True), a5)


class TestPIIRegressionsEscalationAttempt3(unittest.TestCase):
    """Regressions found after the second Flash attempt."""

    def test_cards_adjacent_to_amount_preserve_amount(self):
        cases = {
            "Card: 4532 0150 1234 5671 1200.50 EUR":
                "Card: [REDACTED_CARD] 1200.50 EUR",
            "Card: 4532015012345671 1200.50 EUR":
                "Card: [REDACTED_CARD] 1200.50 EUR",
            "Card: 4000 0000 0000 0000 006 75.00 EUR":
                "Card: [REDACTED_CARD] 75.00 EUR",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(mask_pii(raw, force=True), expected)

    def test_00_phone_upper_digit_boundary(self):
        raw = "Phone: 00441234567890123"
        self.assertEqual(mask_pii(raw, force=True), "Phone: [REDACTED_PHONE]")

    def test_invalid_card_next_to_amount_is_not_masked(self):
        raw = "Card: 4532 0150 1234 5670 1200.50 EUR"
        self.assertEqual(mask_pii(raw, force=True), raw)

    def test_grouped_card_lengths_13_through_19(self):
        cards = (
            "4000 0000 0000 6",
            "4000 0000 0000 02",
            "4000 0000 0000 006",
            "4000 0000 0000 0002",
            "4000 0000 0000 00006",
            "4000 0000 0000 000002",
            "4000 0000 0000 0000 006",
        )
        for card in cards:
            with self.subTest(card=card):
                self.assertTrue(is_valid_luhn(card))
                self.assertEqual(mask_pii(card, force=True), "[REDACTED_CARD]")


if __name__ == "__main__":
    unittest.main()
