
from datetime import datetime, timedelta
from math import exp

from unittest import TestCase
from unittest.mock import Mock, patch

from caliper.reservoir import Reservoir, SlidingWindowReservoir, UniformReservoir, ExponentiallyDecayingReservoir


class TestReservoir(TestCase):

    def setUp(self):
        self.res = Reservoir()

    def test_add_100_elements(self):
        for i in range(100):
            self.res.update(i)

        self.assertEqual(len(self.res), 100)

    @patch('caliper.reservoir.Snapshot')
    def test_snapshot_receives_correct_data(self, Snapshot):
        for i in range(100):
            self.res.update(i)

        snap = self.res.snapshot()
        Snapshot.assert_called_once_with(list(range(100)))


class TestSlidingWindowReservoir(TestCase):

    def setUp(self):
        self.res = SlidingWindowReservoir(15)

    def test_add_15_elements(self):
        for i in range(15):
            self.res.update(i)
        self.assertEqual(len(self.res), 15)

    def test_add_30_elements(self):
        for i in range(30):
            self.res.update(i)
        self.assertEqual(len(self.res), 30)
        self.assertEqual(len(self.res._res), 15)
        self.assertEqual(self.res._res, list(range(15, 30)))

    @patch('caliper.reservoir.Snapshot')
    def test_snapshot_receives_all_data(self, Snapshot):
        for i in range(15):
            self.res.update(i)

        snap = self.res.snapshot()
        Snapshot.assert_called_once_with(list(range(15)))

    @patch('caliper.reservoir.Snapshot')
    def test_snapshot_receives_most_recent_data(self, Snapshot):
        for i in range(30):
            self.res.update(i)

        snap = self.res.snapshot()
        Snapshot.assert_called_once_with(list(range(15, 30)))


class TestUniformReservoir(TestCase):

    def setUp(self):
        self.res = UniformReservoir(15)

    def test_add_15_elements(self):
        for i in range(15):
            self.res.update(i)
        self.assertEqual(len(self.res), 15)

    def test_add_30_elements(self):
        for i in range(30):
            self.res.update(i)
        self.assertEqual(len(self.res), 30)
        self.assertEqual(len(self.res._res), 15)

    @patch('caliper.reservoir.randint')
    def test_randint_called_with_count_minus_one(self, randint):
        for i in range(15):
            self.res.update(i)

        randint.return_value = 1

        self.res.update(42)

        randint.assert_called_once_with(0, 14)

    @patch('caliper.reservoir.randint')
    def test_full_reservoir_insert_in_correct_position(self, randint):
        for _ in range(15):
            self.res.update(0)

        randint.return_value = 5
        self.res.update(42)
        randint.assert_called_once_with(0, 14)
        self.assertEqual(self.res._res[5], 42)
        randint.reset_mock()

        randint.return_value = 0
        self.res.update(21)
        randint.assert_called_once_with(0, 15)
        self.assertEqual(self.res._res[0], 21)
        randint.reset_mock()

        randint.return_value = 14
        self.res.update(1337)
        randint.assert_called_once_with(0, 16)
        self.assertEqual(self.res._res[-1], 1337)
        randint.reset_mock()

    def test_full_reservoir_ignores_index_too_large(self):
        for _ in range(30):
            self.res.update(0)

        with patch('caliper.reservoir.randint') as randint:
            randint.return_value = 20
            self.res.update(42)
            randint.assert_called_once_with(0, 29)
            self.assertFalse(42 in self.res._res)


class TestExponentiallyDecayingReservoir(TestCase):

    def setUp(self):
        self.res = ExponentiallyDecayingReservoir(15)

    def test_sample_weight(self):
        for dt, w in [(0, 1),
                      (1800, 532048240601.79865),
                      (3600, 2.830753303274694e+23)]:
            self.assertEqual(w, self.res._sample_weight(dt))

    @patch('caliper.reservoir.datetime')
    def test_set_next_rescale(self, datetime_mock):
        now = datetime.now()
        datetime_mock.now.return_value = now

        self.res._set_next_rescale()
        self.assertEqual(now + timedelta(hours=1), self.res._next_rescale)


    def test_add_15_elements(self):
        for i in range(15):
            self.res.update(i)
        self.assertEqual(len(self.res), 15)

    def test_add_30_elements(self):
        for i in range(30):
            self.res.update(i)
        self.assertEqual(len(self.res), 30)
        self.assertEqual(len(self.res._res), 15)

    def test_add_to_full_reservoir(self):
        self.res._res = {i: (i, i) for i in range(15)}

        self.res._landmark = datetime.now() - timedelta(minutes=30)
        self.res._count = 15

        self.assertIn(0, self.res._res)

        with patch.object(self.res, '_rescale_if_needed') as _rin, \
                patch.object(self.res, '_rescale') as _rescale, \
                patch.object(self.res, '_sample_weight') as _sample_weight, \
                patch('caliper.reservoir.random') as random:
            random.return_value = 0.5
            _sample_weight.return_value = 20

            self.res.update(42)

            _rin.assert_called_once_with()
            _rescale.assert_not_called()
            random.assert_called_once_with()

        for k, (v, w) in self.res._res.items():
            if v == 42:
                self.assertEqual(w, 20)
                self.assertEqual(k, 40)
                break
        else:
            self.assertTrue(False)

        self.assertEqual(len(self.res._res), 15)
        self.assertNotIn(0, self.res._res)

    def test_rescale(self):
        now = datetime.now()
        landmark = now - timedelta(seconds=3600)
        self.res._landmark = landmark

        self.res._res = {i: (i, 2 * i) for i in range(15)}
        self.res._count = 15

        with patch.object(self.res, '_set_next_rescale') as _set_next_resacle, \
                patch('caliper.reservoir.exp') as exp, \
                patch('caliper.reservoir.datetime') as datetime_mock:
            datetime_mock.now.return_value = now
            exp.return_value = 0.5

            self.res._rescale()

            datetime_mock.now.assert_called_once_with()
            exp.assert_called_once_with(-0.015 * 3600)
            _set_next_resacle.assert_called_once_with()

        expected = {0.5 * i: (i, i) for i in range(15)}
        self.assertEqual(self.res._res, expected)

