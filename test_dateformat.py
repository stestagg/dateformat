import dateutil.parser

try:
    import pytz
    HAVE_PYTZ = True
except ImportError:
    HAVE_PYTZ = False

import unittest
import datetime
import dateformat


class TestDateFormat(unittest.TestCase):

    SAMPLE_LIST = [
        ("hh:mm:ss", "10:45:30"),
        ("MM/DD/YY", "11/12/14"),
        ("MM-DD-YY", "10-12-14"),
        ("MM-DD-YY", "10-12-60"),
        ("MM-DD-YY", "10-12-70"),
        ("MM-DD-YYYY", "10-12-1970"),
        ("MM-DD-YYYY", "10-12-2070"),
        ("YYYY-MM-DD", "2016-05-03"),
        ("YYYY-MMM-DD", "2016-Jun-03"),
        ("YYYY-MMMMM-DD", "2016-August-03"),
        ("hhpm", "12am"),
        ("hhPM", "12PM"),
        ("hhAM", "05PM"),
        ("hh:mm:ss+HHMM", "12:12:10+0100"),
        ("hh:mm:ss+HHMM", "12:12:11+0500"),
        ("hh:mm:ss+HHMM", "12:12:12-0500"),
        ("hh:mm:ss", "01:02:03"),
        ("YYYY-MM-DDThh:mm", "2007-04-05T23:59"),
        ("YYYY-MM-DDThh:mm:ss.SSSSSS", "2007-04-05T23:59:01.234567"),
        ("DD-MMM-YYYY hhmm", "21-Jul-2015 2005"),
        ("DDst of MMMMM, YYYY", "01st of June, 1985"),
        ("DDst of MMMMM, YYYY", "03rd of May, 2222"),
        ("DDst of MMMMM, YYYY", "11th of June, 1985"),
    ]

    def test_parsing_simple_date_gives_expected_value(self):
        parser = dateformat.DateFormat("DD/MM/YY hh:mm")
        result = parser.parse("10/12/12 16:23")
        self.assertEqual(result, datetime.datetime(2012, 12, 10, 16, 23))

    def test_parsing_invalid_date_returns_default(self):
        parser = dateformat.DateFormat("DD/MM/YY hh:mm")
        with self.assertRaises(ValueError):
            parser.parse('xxx')
        self.assertIsNone(parser.parse('xxx', None))
        self.assertEqual(parser.parse('xxx', '123'), '123')

    def test_matches_format(self):
        parser = dateformat.DateFormat("DD/MM/YY hh:mm")
        for value, expected in [
            ('x', False),
            ('1/2/34 09:45', True),
            ('1/2/34 09:45:99', False),
            ('1/2/1985 09:45', False),
            (None, False),
        ]:
            self.assertEqual(parser.matches_format(value), expected)

    def test_parsing_various_dates_matches_dateutil_results(self):
        for format, date in self.SAMPLE_LIST:
            expected = dateutil.parser.parse(date)
            actual = dateformat.DateFormat(format).parse(date)
            self.assertEqual(actual, expected)

    def test_formatting_a_parsed_date_returns_original_value(self):
        for spec, date in self.SAMPLE_LIST:
            format = dateformat.DateFormat(spec)
            parsed = format.parse(date)
            self.assertEqual(date, format.format(parsed))

    def test_invalid_dates_raise_errors(self):
        for spec, valid, invalid in [
            ("pm", "PM", "xx"),
            ("hh:mmAM", "12:02am", "15:02am"),
            ("hh:mm", "23:02", "28:02"),
            ("hh:mm", "23:52", "23:62"),
            ("YYYY", "1234", "12345"),
            ("DD:MMThh:mm", "12:12T12:12", "12:12Z12:12"),
            ("DD MM", "12 12", "1212"),
        ]:
            format = dateformat.DateFormat(spec)
            self.assertIsInstance(format.parse(valid), datetime.datetime)
            with self.assertRaises(ValueError):
                format.parse(invalid)

    def test_am_pm_calc_is_correct(self):
        am_hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        pm_hours = [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
        tests = [("am", h) for h in am_hours] + [("pm", h) for h in pm_hours]
        for expected, hour in tests:
            for minute, second in [
                (1, 1),
                (59, 59),
            ]:
                date = datetime.datetime(2015, 1, 1, hour, minute, second)
                self.assertEqual(dateformat.DateFormat("am").format(date), expected)

    def test_formatting_various_dates_notz(self):
        the_date = datetime.datetime(2015, 1, 2, 3, 14, 25, 678901, None)
        for format, expected in [
            ("hh:mm:ss", "03:14:25"),
            ("hh AM", "03 AM"),
            ("hhAm", "03Am"),
            ("hh am", "03 am"),
            ("SS", "68"),
            ("SSS", "679"),
            ("SSSS", "6789"),
            ("SSSSSS", "678901"),
            ]:
            actual = dateformat.DateFormat(format).format(the_date)
            self.assertEqual(expected, actual)

    def test_isoformat_datetime(self):
        expected = datetime.datetime(2017, 12, 6, 11, 55, 44)
        date_format = dateformat.DateFormat(dateformat.ISOFORMAT_DATETIME)
        assert date_format.parse("2017-12-6T11:55:44") == expected
        assert date_format.format(date_format.parse("2017-12-6T11:55:44")) == "2017-12-06T11:55:44"

    def test_unix_timestamp_parsing(self):
        for format_str, value, expected in [
            ('UNIX_TIMESTAMP', '1956531661', datetime.datetime(2032, 1, 1, 1, 1, 1)),

            ('UNIX_TIMESTAMP.S', '1956531661.1', datetime.datetime(2032, 1, 1, 1, 1, 1, 100000)),
            ('UNIX_TIMESTAMP.S', '1956531661.01', datetime.datetime(2032, 1, 1, 1, 1, 1, 10000)),
            ('UNIX_TIMESTAMP.S', '1956531661.001', datetime.datetime(2032, 1, 1, 1, 1, 1, 1000)),
            ('UNIX_TIMESTAMP.S', '1956531661.0001', datetime.datetime(2032, 1, 1, 1, 1, 1, 100)),
            ('UNIX_TIMESTAMP.S', '1956531661.00001', datetime.datetime(2032, 1, 1, 1, 1, 1, 10)),
            ('UNIX_TIMESTAMP.S', '1956531661.000001', datetime.datetime(2032, 1, 1, 1, 1, 1, 1)),
            ('UNIX_TIMESTAMP.S', '1956531661.0000001', datetime.datetime(2032, 1, 1, 1, 1, 1, 0)),

            ('UNIX_TIMESTAMP', '0', datetime.datetime(1970, 1, 1, 0, 0, 0)),
            ('UNIX_MILLISECONDS', '0', datetime.datetime(1970, 1, 1, 0, 0, 0)),
            ('UNIX_MICROSECONDS', '0', datetime.datetime(1970, 1, 1, 0, 0, 0)),
            ('UNIX_NANOSECONDS', '0', datetime.datetime(1970, 1, 1, 0, 0, 0)),

            ('UNIX_TIMESTAMP', '1', datetime.datetime(1970, 1, 1, 0, 0, 1)),
            ('UNIX_MILLISECONDS', '1', datetime.datetime(1970, 1, 1, 0, 0, 0, 1000)),
            ('UNIX_MICROSECONDS', '1', datetime.datetime(1970, 1, 1, 0, 0, 0, 1)),
            ('UNIX_NANOSECONDS', '1', datetime.datetime(1970, 1, 1, 0, 0, 0, 0)),

            ('UNIX_TIMESTAMP', '1553606835', datetime.datetime(2019, 3, 26, 13, 27, 15)),
            ('UNIX_MILLISECONDS', '1553606835123', datetime.datetime(2019, 3, 26, 13, 27, 15, 123000)),
            ('UNIX_MICROSECONDS', '1553606835123456', datetime.datetime(2019, 3, 26, 13, 27, 15, 123456)),
            ('UNIX_NANOSECONDS', '1553606835123456789', datetime.datetime(2019, 3, 26, 13, 27, 15, 123457)),
        ]:
            date_format = dateformat.DateFormat(format_str)
            self.assertEqual(date_format.parse(value), expected)

    def test_unix_timestamp_format(self):
        for format_str, expected, value in [
            ('UNIX_TIMESTAMP', '1956531661', datetime.datetime(2032, 1, 1, 1, 1, 1)),
            ('UNIX_TIMESTAMP.SSS', '1956531661.123', datetime.datetime(2032, 1, 1, 1, 1, 1, 123000)),
            ('UNIX_TIMESTAMP.S', '1956531661.1', datetime.datetime(2032, 1, 1, 1, 1, 1, 100000)),
            ('UNIX_TIMESTAMP.S', '1956531661.01', datetime.datetime(2032, 1, 1, 1, 1, 1, 10000)),
            ('UNIX_TIMESTAMP.S', '1956531661.001', datetime.datetime(2032, 1, 1, 1, 1, 1, 1000)),
            ('UNIX_TIMESTAMP.S', '1956531661.0001', datetime.datetime(2032, 1, 1, 1, 1, 1, 100)),
            ('UNIX_TIMESTAMP.S', '1956531661.00001', datetime.datetime(2032, 1, 1, 1, 1, 1, 10)),
            ('UNIX_TIMESTAMP.S', '1956531661.000001', datetime.datetime(2032, 1, 1, 1, 1, 1, 1)),
            
            ('UNIX_TIMESTAMP', '0', datetime.datetime(1970, 1, 1, 0, 0, 0)),
            ('UNIX_MILLISECONDS', '0', datetime.datetime(1970, 1, 1, 0, 0, 0)),
            ('UNIX_MICROSECONDS', '0', datetime.datetime(1970, 1, 1, 0, 0, 0)),
            ('UNIX_NANOSECONDS', '0', datetime.datetime(1970, 1, 1, 0, 0, 0)),

            ('UNIX_TIMESTAMP', '1', datetime.datetime(1970, 1, 1, 0, 0, 1)),
            ('UNIX_MILLISECONDS', '1', datetime.datetime(1970, 1, 1, 0, 0, 0, 1000)),
            ('UNIX_MICROSECONDS', '1', datetime.datetime(1970, 1, 1, 0, 0, 0, 1)),
            ('UNIX_NANOSECONDS', '1000', datetime.datetime(1970, 1, 1, 0, 0, 0, 1)),

            ('UNIX_TIMESTAMP', '1553606835', datetime.datetime(2019, 3, 26, 13, 27, 15)),
            ('UNIX_MILLISECONDS', '1553606835123', datetime.datetime(2019, 3, 26, 13, 27, 15, 123000)),
            ('UNIX_MICROSECONDS', '1553606835123456', datetime.datetime(2019, 3, 26, 13, 27, 15, 123456)),
            ('UNIX_NANOSECONDS', '1553606835000001792', datetime.datetime(2019, 3, 26, 13, 27, 15, 2)),
        ]:
            date_format = dateformat.DateFormat(format_str)
            self.assertEqual(date_format.format(value), expected)

    if HAVE_PYTZ:
        def test_parsing_dates_with_all_named_timezones(self):
            time_base = "2017-12-6T11:55:44"
            datetime_base = datetime.datetime(2017, 12, 6, 11, 55, 44)
            date_format = dateformat.DateFormat(f"{dateformat.ISOFORMAT_DATETIME} UTC")
            for timezone in pytz.all_timezones:
                source = f"{time_base} {timezone}"
                parsed = date_format.parse(source)
                tzinfo = pytz.timezone(timezone)
                assert parsed.tzinfo.zone == tzinfo.zone
                assert parsed == tzinfo.localize(datetime_base)

        def test_formatting_dates_with_named_timezones(self):
            date = datetime.datetime(2017, 12, 6, 11, 55, 44)
            local_date = pytz.timezone("Europe/Warsaw").localize(date)
            date_format = dateformat.DateFormat(f"{dateformat.ISOFORMAT_DATETIME} (UTC)")


        def test_formatting_tzaware_unix_timestamps(self):
            date = datetime.datetime(2017, 12, 6, 11, 55, 44)
            local_date = pytz.timezone("Europe/Warsaw").localize(date)
            date_format = dateformat.DateFormat(f"UNIX_TIMESTAMP")
            formatted = date_format.format(local_date)
            self.assertEqual(formatted, '1512557744')


if __name__ == '__main__':
    import unittest
    unittest.main()