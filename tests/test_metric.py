
from datetime import datetime, timedelta
from unittest import TestCase
try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

from caliper.metric import EWMA, Counter, Meter, Gauge


class TestCounter(TestCase):

    def setUp(self):
        self.counter = Counter()

    def test_starts_at_zero(self):
        self.assertEqual(self.counter.get_count(), 0)
        self.assertEqual(self.counter.count, 0)

    def test_increments_by_one(self):
        self.counter.inc()
        self.assertEqual(self.counter.count, 1)

    def test_increments_by_n(self):
        self.counter.inc(42)
        self.assertEqual(self.counter.count, 42)

    def test_decrements_by_one(self):
        self.counter.dec()
        self.assertEqual(self.counter.count, -1)

    def test_decrements_by_n(self):
        self.counter.dec(42)
        self.assertEqual(self.counter.count, -42)


class TestEWMA(TestCase):

    def test_one_minute_sets_alpha(self):
        one_minute = EWMA.one_minute()
        self.assertAlmostEqual(one_minute._alpha, 0.07996, 5)

    def test_five_minutes_sets_alpha(self):
        five_minutes = EWMA.five_minutes()
        self.assertAlmostEqual(five_minutes._alpha, 0.01653, 5)

    def test_fifteen_minutes_sets_alpha(self):
        fifteen_minutes = EWMA.fifteen_minutes()
        self.assertAlmostEqual(fifteen_minutes._alpha, 0.00554, 5)

    def test_update_adds_one(self):
        ewma = EWMA.one_minute()
        ewma.update(1)
        self.assertEqual(ewma._uncounted, 1)

    def test_update_adds_N(self):
        ewma = EWMA.one_minute()
        ewma.update(42)
        self.assertEqual(ewma._uncounted, 42)

    def test_tick_sets_uninitialized_rate(self):
        ewma = EWMA.one_minute()
        ewma.update(3)
        ewma.tick()
        self.assertEqual(ewma.rate, 3/5.0)

    def test_tick_sets_initialized_rate(self):
        ewma = EWMA(0.5)
        ewma.update(3)
        ewma.tick()
        ewma.update(2)
        ewma.tick()

        self.assertEqual(ewma.rate, 0.5)


class TestMeter(TestCase):

    def setUp(self):
        self.meter = Meter()

    def test_mark_increments_count_by_one(self):
        self.meter.mark()
        self.assertEqual(self.meter.count, 1)

    def test_mark_increments_count_by_N(self):
        self.meter.mark(42)
        self.assertEqual(self.meter.count, 42)

    def test_mark_calls_tick(self):
        with patch.object(self.meter, '_tick') as _tick:
            self.meter.mark()
            _tick.assert_called_once_with()

    def test_mark_calls_rate_updates(self):
        self.meter.m1rate = Mock()
        self.meter.m5rate = Mock()
        self.meter.m15rate = Mock()

        self.meter.mark()

        self.meter.m1rate.update.assert_called_once_with(1)
        self.meter.m5rate.update.assert_called_once_with(1)
        self.meter.m15rate.update.assert_called_once_with(1)

    def test_tick_does_not_prematurely_tick_rates(self):
        self.meter.m1rate = Mock()
        self.meter.m5rate = Mock()
        self.meter.m15rate = Mock()

        self.meter.mark()

        self.meter.m1rate.tick.assert_not_called()
        self.meter.m5rate.tick.assert_not_called()
        self.meter.m15rate.tick.assert_not_called()

    def test_tick_sets_last_tick(self):
        then = datetime.now() - timedelta(seconds=7)
        self.meter._last_tick = then

        self.meter.mark()

        self.assertTrue(self.meter._last_tick >= then + timedelta(seconds=7))

    def test_tick_updates_rates_n_times(self):
        then = datetime.now() - timedelta(seconds=14)
        self.meter._last_tick = then
        self.meter.m1rate = Mock()
        self.meter.m5rate = Mock()
        self.meter.m15rate = Mock()

        self.meter.mark()

        self.assertEqual(self.meter.m1rate.tick.call_count, 2)
        self.assertEqual(self.meter.m5rate.tick.call_count, 2)
        self.assertEqual(self.meter.m15rate.tick.call_count, 2)


class TestGauge(TestCase):

    def test_gets_value(self):
        g = Gauge()
        g.value = 42
        self.assertEqual(g.get_value(), 42)

    def test_property_gets_overloaded_value(self):
        l = [1, 2, 3]
        g = Gauge()
        g.get_value = lambda: len(l)
        self.assertEqual(g.value, 3)
