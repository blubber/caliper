'''
'''

import math

from .util import cached_property


# XXX: Not sure if inheriting from tuple and overloading __new__ is a good idea.


class Snapshot(tuple):
    ''' A snapshot holds an immutable view over a reservoir, and offers some
    statistical measures about it's contents. Snapshots are iterable. '''

    def __new__(cls, iterable):
        return tuple.__new__(cls, sorted(float(x) for x in iterable))

    def get_value(self, quantile):
        ''' Returns the value at `quantile`.

        :param quantile: :class:`float` in ``[0, 1]``.
        :returns: The value at the given quantile.
        '''
        if not 0 <= quantile <= 1:
            raise ValueError('Quantile should be in [0, 1].')

        if len(self) == 0:
            return 0

        pos = quantile * float(len(self) + 1)
        index = int(pos)

        if index == 0:
            value = self[0]
        elif index >= len(self):
            value = self[-1]
        else:
            lower = self[index - 1]
            upper = self[index]
            value = lower + (pos - index) * (upper - lower)

        return value

    @cached_property
    def mean(self):
        if len(self) == 0:
            return 0
        return sum(self) / float(len(self))

    @cached_property
    def stddev(self):
        if len(self) <= 1:
            return 0
        sum_ = sum((x - self.mean)**2 for x in self)
        variance = sum_ / float(len(self) - 1)
        return math.sqrt(variance)


class WeightedSnapshot(tuple):

    def __new__(cls, iterable):
        iterable = list(iterable)

        if len(iterable):
            values, weights = zip(*sorted(iterable))
        else:
            values, weights = [], []

        obj = tuple.__new__(cls, (float(x) for x in values))

        sumweight = float(sum(weights))
        obj._normweights = [w / sumweight for w in weights]

        obj._quantiles = [sum(obj._normweights[:i]) for i in range(len(values))]

        return obj

    def get_value(self, quantile):
        if not 0 <= quantile <= 1:
            raise ValueError('Quantile should be in [0, 1].')

        for pos, acc in enumerate(self._quantiles):
            if acc > quantile:
                break
        else:
            pos = len(self)

        if pos <= 1:
            value = self[0]
        else:
            value = self[pos - 1]

        return value

    @cached_property
    def mean(self):
        if len(self) == 0:
            return 0
        return sum(v * w for v, w in zip(self, self._normweights))

    @cached_property
    def stddev(self):
        if len(self) <= 1:
            return 0
        variance = sum(w * (v - self.mean)**2 for v, w in zip(self, self._normweights))
        return math.sqrt(variance)
