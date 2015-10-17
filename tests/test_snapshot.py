
from unittest import TestCase

from caliper.snapshot import Snapshot, WeightedSnapshot


class TestSnapshot(TestCase):

    def setUp(self):
        self.values = [5, 1, 2, 3, 4]
        self.snap = Snapshot(self.values)

    def test_small_percentile_is_first_element(self):
        self.assertEqual(self.snap.get_value(0.01), 1)

    def test_big_percentile_is_last_element(self):
        self.assertEqual(self.snap.get_value(1.0), 5)

    def test_disallows_negative_percentile(self):
        with self.assertRaises(ValueError):
            self.snap.get_value(-0.42)

    def test_disallows_percentile_larger_then_one(self):
        with self.assertRaises(ValueError):
            self.snap.get_value(1.1)

    def test_42th_percentile(self):
        self.assertEqual(self.snap.get_value(0.42), 2.52)

    def test_75th_percentile(self):
        self.assertEqual(self.snap.get_value(0.75), 4.5)

    def test_95th_percentile(self):
        self.assertEqual(self.snap.get_value(0.95), 5.0)

    def test_98th_percentile(self):
        self.assertEqual(self.snap.get_value(0.98), 5.0)

    def test_99th_percentile(self):
        self.assertEqual(self.snap.get_value(0.99), 5.0)

    def test_999th_percentile(self):
        self.assertEqual(self.snap.get_value(0.999), 5.0)

    def test_calculates_the_mean_value(self):
        self.assertEqual(self.snap.mean, 3.0)

    def test_calculates_mean_of_zero_for_empty_snapshot(self):
        snap = WeightedSnapshot([])
        self.assertEqual(snap.mean, 0)

    def test_calculates_the_stddev(self):
        self.assertAlmostEqual(self.snap.stddev, 1.5811, places=4)

    def test_calculates_a_stddev_of_zero_for_empty_snapshot(self):
        snap = WeightedSnapshot([])
        self.assertEqual(snap.stddev, 0)

    def test_calculates_a_stddev_of_zero_for_snapshot_of_one_item(self):
        snap = WeightedSnapshot([(1, 1)])
        self.assertEqual(snap.stddev, 0)


class TestWeightedSnapshot(TestCase):

    def setUp(self):
        self.values = [5, 1, 2, 3, 4]
        self.weights = [1, 2, 3, 2, 2]
        self.snap = WeightedSnapshot(zip(self.values, self.weights))

    def test_small_percentile_is_first_element(self):
        self.assertEqual(self.snap.get_value(0.01), 1)

    def test_big_percentile_is_last_element(self):
        self.assertEqual(self.snap.get_value(1.0), 5)

    def test_disallows_negative_percentile(self):
        with self.assertRaises(ValueError):
            self.snap.get_value(-0.42)

    def test_disallows_percentile_larger_then_one(self):
        with self.assertRaises(ValueError):
            self.snap.get_value(1.1)

    def test_75th_percentile(self):
        self.assertEqual(self.snap.get_value(0.75), 4)

    def test_95th_percentile(self):
        self.assertEqual(self.snap.get_value(0.95), 5)

    def test_98th_percentile(self):
        self.assertEqual(self.snap.get_value(0.98), 5)

    def test_99th_percentile(self):
        self.assertEqual(self.snap.get_value(0.99), 5)

    def test_999th_percentile(self):
        self.assertEqual(self.snap.get_value(0.999), 5)

    def test_calculates_the_mean_value(self):
        self.assertEqual(self.snap.mean, 2.7)

    def test_calculates_mean_of_zero_for_empty_snapshot(self):
        snap = WeightedSnapshot([])
        self.assertEqual(snap.mean, 0)

    def test_calculates_the_stddev(self):
        self.assertAlmostEqual(self.snap.stddev, 1.2689, places=4)

    def test_calculates_a_stddev_of_zero_for_empty_snapshot(self):
        snap = WeightedSnapshot([])
        self.assertEqual(snap.stddev, 0)

    def test_calculates_a_stddev_of_zero_for_snapshot_of_one_item(self):
        snap = WeightedSnapshot([(1, 1)])
        self.assertEqual(snap.stddev, 0)
