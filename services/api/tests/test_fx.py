from datetime import date
from decimal import Decimal, localcontext
import unittest

import httpx

from vela.fx import Amount, ECBRates, value_amounts


class FXTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.day = date(2026, 10, 25)  # Sunday; last published quote is Friday.
        self.body = b'{"date":"2026-10-23","base":"HUF","quote":"EUR","rate":0.0025}'
        self.status = 200
        def respond(request):
            self.calls.append(request)
            return httpx.Response(self.status, content=self.body)
        self.client = httpx.Client(transport=httpx.MockTransport(respond))
        self.rates = ECBRates(self.client, today=lambda: self.day)

    def tearDown(self):
        self.client.close()

    def test_ecb_only_request_and_decimal_metadata(self):
        quote = self.rates.get('HUF', 'EUR', on=self.day)
        self.assertEqual(quote.rate, Decimal('0.0025'))
        self.assertIsInstance(quote.rate, Decimal)
        self.assertEqual(quote.rate_date, date(2026, 10, 23))
        self.assertEqual(quote.requested_on, self.day)
        self.assertEqual(quote.source, 'ECB via Frankfurter v2')
        self.assertEqual(str(self.calls[0].url),
                         'https://api.frankfurter.dev/v2/providers/ecb/rate/huf/eur?date=2026-10-25')
        self.assertNotIn('authorization', self.calls[0].headers)

    def test_current_cache_rolls_on_clock_day_and_historical_separate(self):
        first = self.rates.get('HUF', 'EUR')
        self.assertIs(self.rates.get('HUF', 'EUR'), first)
        self.assertNotIn('date', self.calls[0].url.params)
        self.rates.get('HUF', 'EUR', on=self.day)
        self.assertEqual(len(self.calls), 2)
        self.day = date(2026, 10, 26)
        self.rates.get('HUF', 'EUR')
        self.assertEqual(len(self.calls), 3)
        self.rates.get('HUF', 'EUR', on=date(2026, 10, 25))
        self.assertEqual(len(self.calls), 3)

    def test_bounded_cache_evicts_old_quote(self):
        rates = ECBRates(self.client, today=lambda: self.day, cache_size=1)
        rates.get('HUF', 'EUR')
        rates.get('HUF', 'EUR', on=self.day)
        rates.get('HUF', 'EUR')
        self.assertEqual(len(self.calls), 3)

    def test_decimal_total_not_per_line_rounded_and_inputs_preserved(self):
        originals = (Amount(1000, 'EUR'), Amount(200, 'HUF'), Amount(200, 'HUF'))
        with localcontext() as ctx:
            ctx.prec = 2  # Caller context must not silently lose amount precision.
            result = value_amounts(originals, self.rates)
        self.assertEqual(result.exact_total_minor, Decimal('1001.0000'))
        self.assertEqual(result.total_minor, 1001)
        self.assertEqual(result.lines[1].converted_minor, Decimal('0.5000'))
        self.assertEqual(tuple(line.original for line in result.lines), originals)
        self.assertEqual(originals[1].minor, 200)
        self.assertTrue(result.complete)
        self.assertTrue(result.estimated)
        self.assertEqual(len(self.calls), 1)

    def test_unknown_or_missing_rate_is_incomplete_not_partial_zero(self):
        self.status = 503
        result = value_amounts([Amount(1000, 'EUR'), Amount(200, 'HUF'), Amount(None, 'EUR')], self.rates)
        self.assertIsNone(result.exact_total_minor)
        self.assertIsNone(result.total_minor)
        self.assertFalse(result.complete)
        self.assertEqual(result.lines[0].converted_minor, Decimal(1000))
        self.assertEqual(result.lines[1].unavailable, 'missing_rate')
        self.assertEqual(result.lines[2].unavailable, 'unknown_amount')
        self.status = 200
        self.assertIsNotNone(self.rates.get('HUF', 'EUR'))  # Failures not cached.

    def test_malformed_wrong_pair_nonpositive_nonfinite_and_future_rejected(self):
        invalid = [b'not json', b'[]', b'{"rate":true}',
                   b'{"date":"2026-10-26","base":"HUF","quote":"EUR","rate":0.0025}',
                   b'{"date":"2026-10-23","base":"EUR","quote":"HUF","rate":400}',
                   b'{"date":"2026-10-23","base":"HUF","quote":"EUR","rate":NaN}']
        for rate in ['0', '-1', '"0.0025"', '1e1000']:
            invalid.append(('{"date":"2026-10-23","base":"HUF","quote":"EUR","rate":'+rate+'}').encode())
        for body in invalid:
            with self.subTest(body=body):
                self.body = body
                self.assertIsNone(self.rates.get('HUF', 'EUR'))

    def test_network_outage_is_missing_not_uncaught_or_zero(self):
        def timeout(request):
            raise httpx.ReadTimeout('synthetic timeout', request=request)
        with httpx.Client(transport=httpx.MockTransport(timeout)) as client:
            result = value_amounts([Amount(1, 'HUF')], ECBRates(client, today=lambda: self.day))
        self.assertFalse(result.complete)
        self.assertIsNone(result.exact_total_minor)

    def test_identity_zero_negative_and_empty_without_network(self):
        result = value_amounts([Amount(1200, 'EUR'), Amount(-200, 'EUR'), Amount(0, 'EUR')], self.rates)
        self.assertEqual(result.exact_total_minor, Decimal(1000))
        self.assertFalse(result.estimated)
        self.assertEqual(value_amounts([], self.rates).exact_total_minor, Decimal(0))
        self.assertEqual(self.calls, [])

    def test_validation_no_implicit_currency_float_bool_or_future(self):
        for minor in [True, 1.1, Decimal(1), 9_007_199_254_740_992]:
            with self.assertRaises(ValueError):
                Amount(minor, 'EUR')
        with self.assertRaises(ValueError):
            Amount(1, 'USD')
        with self.assertRaises(ValueError):
            self.rates.get('USD', 'EUR')
        with self.assertRaises(ValueError):
            self.rates.get('EUR', 'HUF', on=date(2026, 10, 26))
        self.assertEqual(self.calls, [])

    def test_long_decimal_and_safeinteger_precision_preserved(self):
        self.body = b'{"date":"2026-10-23","base":"HUF","quote":"EUR","rate":0.00251234567890123456789}'
        result = value_amounts([Amount(9_007_199_254_740_991, 'HUF')], self.rates)
        # Independent integer oracle: 9007199254740991 *251234567890123456789 /10**23.
        self.assertEqual(result.exact_total_minor, Decimal('22629198126650.94907653252505775537899'))

    def test_owner_half_up_ties_and_round_once_after_aggregation(self):
        self.assertEqual(value_amounts([Amount(40200, 'HUF')], self.rates).total_minor, 101)
        self.assertEqual(value_amounts([Amount(-40200, 'HUF')], self.rates).total_minor, -101)
        # Two half-cent lines total one cent, not two individually rounded cents.
        self.assertEqual(value_amounts([Amount(200, 'HUF'), Amount(200, 'HUF')], self.rates).total_minor, 1)
        with self.assertRaisesRegex(ValueError, 'safe integer'):
            value_amounts([Amount(9_007_199_254_740_991, 'EUR'), Amount(1, 'EUR')], self.rates)
