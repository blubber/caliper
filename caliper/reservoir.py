'''
    Reservoirs
    ~~~~~~~~~~
    Reservoirs hold (a subset) of data from a data stream, some reservoirs employ
    a sampling method to improve storage requirements and/or recency while offering
    good statistical properties.
'''

from random import randint

from datetime import datetime, timedelta
from math import exp
from random import random

from .snapshot import Snapshot, WeightedSnapshot


class BaseReservoir(object):
    ''' A reservoir holds (a subset) of values from a stream of data. '''

    def __init__(self):
        self._res = []
        self._count = 0

    def update(self, value):
        ''' Add `value` to the reservoir. '''
        raise NotImplementedError()

    def snapshot(self):
        ''' Create a snapshot of the current state of the reservoir.

        :returns: :class:`~caliper.snapshot.Snapshot`.
        '''
        return Snapshot(self._res)

    def __len__(self):
        ''' Returns the total number of values added to the reservoir, regardless
        of the actual number of values a reservoir might hold.
        '''
        return self._count


class Reservoir(BaseReservoir):
    ''' A reservoir that stores all values added to it. '''

    def update(self, value):
        self._count += 1
        self._res.append(value)


class SlidingWindowReservoir(BaseReservoir):
    ''' A reservoir that keeps the `size` most recent values added to it. '''

    DEFAULT_SIZE = 100

    def __init__(self, size=DEFAULT_SIZE):
        super(SlidingWindowReservoir, self).__init__()
        assert size > 0
        self._res = []
        self._size = size

    def update(self, value):
        if self._count < self._size:
            self._res.append(value)
        else:
            self._res[self._count % self._size] = value
        self._count += 1


class UniformReservoir(BaseReservoir):
    ''' A Sampling reservoir that represents a uniform sample of the input stream. Sampling
    is done using Vitter's Algorithm R.
    '''

    DEFAULT_SIZE = 1028

    def __init__(self, size=DEFAULT_SIZE):
        super(UniformReservoir, self).__init__()
        self._size = size

    def update(self, value):
        if self._count < self._size:
            self._res.append(value)
        else:
            index = randint(0, self._count - 1)
            if index < self._size:
                self._res[index] = value
        self._count += 1


class ExponentiallyDecayingReservoir(BaseReservoir):
    ''' A sampling reservoir that employs exponential decay. The reservoir attempts
    to strike a balance betwee storage requirements, recency and statistical accuracy.
    '''

    DEFAULT_SIZE = 1028
    DEFAULT_ALPHA = 0.015
    RESCALE_THRESHOLD = timedelta(hours=1)

    def __init__(self, size=DEFAULT_SIZE, alpha=DEFAULT_ALPHA):
        super(ExponentiallyDecayingReservoir, self).__init__()
        self._size = size
        self._alpha = alpha
        self._set_next_rescale()
        self._landmark = datetime.now()
        self._res = {}

    def update(self, value, timestamp=None):
        self._rescale_if_needed()
        timestamp = timestamp or datetime.now()

        assert timestamp > self._landmark, 'Timestamp before landmark!'

        weight = self._sample_weight((timestamp - self._landmark).total_seconds())
        sample = (value, weight)

        scale = random()
        while scale == 0.0:
            scale = random()
        priority = weight / scale

        if self._count < self._size:
            self._res[priority] = sample
        else:
            first = sorted(self._res.keys())[0]
            if first < priority and priority not in self._res:
                self._res[priority] = sample
                del self._res[first]

        self._count += 1

    def snapshot(self):
        return WeightedSnapshot(self._res.values())

    def _rescale_if_needed(self):
        if datetime.now() >= self._next_rescale:
            self._rescale()

    def _sample_weight(self, t):
        return exp(self._alpha * t)

    def _rescale(self):
        self._set_next_rescale()

        old_landmark = self._landmark
        self._landmark = datetime.now()
        scale = exp(-self._alpha * (self._landmark - old_landmark).total_seconds())

        new_res = {}

        for key, (value, weight) in self._res.items():   # XXX: iteritems?
            new_res[key * scale] = (value, weight * scale)

        self._res = new_res

    def _set_next_rescale(self):
        self._next_rescale = (datetime.now() +
                              ExponentiallyDecayingReservoir.RESCALE_THRESHOLD)
