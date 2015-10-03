
from datetime import datetime
from math import exp

from .reservoir import ExponentiallyDecayingReservoir


class SamplingMetric(object):
    ''' Base class for metrics that use a reservoir. '''

    @staticmethod
    def default_reservoir():
        return ExponentiallyDecayingReservoir()

    def __init__(self, reservoir=None):
        self._reservoir = reservoir or SamplingMetric.default_reservoir()

    def snapshot(self):
        return self._reservoir.snapshot()


class Counter(object):
    ''' A counter metric. '''

    def __init__(self):
        self._count = 0

    @property
    def count(self):
        return self.get_count()

    def get_count(self):
        ''' Get the current value of the counter. '''
        return self._count

    def inc(self, n=1):
        ''' Increment the counter by `n`. '''
        self._count += n

    def dec(self, n=1):
        ''' Decrement the counter by `n`. '''
        self._count -= n


class Gauge(object):
    ''' An instanteneous metric.

    The easiest way to use this metric is to override (or monkey patch) the
    :meth:`get_value` method, otherwise update the internal value use the
    :property:`value` setter.
    '''

    def __init__(self):
        self._value = None

    @property
    def value(self):
        return self.get_value()

    @value.setter
    def value(self, value):
        self._value = value

    def get_value(self):
        return self._value


class Histogram(SamplingMetric, Counter):
    ''' A metric that calculates the distribution of a value. '''

    def __init__(self, reservoir=None):
        SamplingMetric.__init__(self, reservoir)
        Counter.__init__(self)

    def update(self, value):
        Counter.inc(self)
        self._reservoir.update(value)


class Timer(SamplingMetric):
    ''' A timer. '''

    class Context(object):

        def __init__(self, timer, update_on_success, update_on_failure):
            self._timer = timer
            self._update_on_success = update_on_success
            self._update_on_failure = update_on_failure
            self._aborted = False

        def abort(self):
            self._aborted = True

        def __enter__(self):
            self._started = datetime.now()
            return self

        def __exit__(self, exc_type, *args):
            if not self._aborted:
                delta = (datetime.now() - self._started).total_seconds()
                if exc_type and self._update_on_failure or \
                        exc_type is None and self._update_on_success:
                    self._timer.update(delta)

    def __init__(self, reservoir=None):
        super(Timer, self).__init__(reservoir)
        self._histogram = Histogram(reservoir)
        self._meter = Meter()

    def time(self, update_on_success=True, update_on_failure=True):
        ''' Returns a context manager that records time.

        :param update_on_success: If ``True`` (default) the duration will be recorded
                                  if no exception was raised inside the context.
        :param update_on_failure: If ``True`` (default) the duration will be recorded
                                  even if an exception was raised inside the context.

        The context manager has an :meth:`abort` method that prevents the duration
        from being recorded regardless of the configuration of the manager.
        '''
        return Timer.Context(self, update_on_success, update_on_failure)

    def update(self, duration):
        ''' Add `duration` in seconds. '''
        if duration > 0:
            self._histogram.update(duration)
            self._meter.mark()

    def snapshot(self):
        return self._histogram.snapshot()


class Meter(object):
    ''' A meter metric that measures mean throughput measured and one,
    five and fifteen minute exponetially-weighted moving average throughput.

    :param interval: Update the moving averages each `interval` seconds.
    '''

    INTERVAL = 5

    def __init__(self, interval=INTERVAL):
        self._count = 0
        self._interval = float(interval)
        self._last_tick = datetime.now()
        self.m1rate = EWMA.one_minute()
        self.m5rate = EWMA.five_minutes()
        self.m15rate = EWMA.fifteen_minutes()

    @property
    def count(self):
        return self.get_count()

    def get_count(self):
        return self._count

    def mark(self, n=1):
        self._tick()
        self._count += n
        self.m1rate.update(n)
        self.m5rate.update(n)
        self.m15rate.update(n)

    def _tick(self):
        new_tick = datetime.now()
        age = (new_tick - self._last_tick).total_seconds()

        if age > self._interval:
            self._last_tick = new_tick

            # XXX: This is inaccurate if age approaches a multiple of interval.
            #      the float part of the range should be subtracted from _last_tick.
            for _ in range(int(age / self._interval)):
                self.m1rate.tick()
                self.m5rate.tick()
                self.m15rate.tick()


class EWMA(object):
    ''' Implements Exponentially Weighted Moving Average used by Metered metrics.

    :param alpha: Smoothing constant.
    :param interval: A timedelta.
    '''

    INTERVAL = 5
    M1_ALPHA = 1 - exp(-INTERVAL / 60.0)
    M5_ALPHA = 1 - exp(-INTERVAL / 60.0 / 5.0)
    M15_ALPHA = 1 - exp(-INTERVAL / 60.0 / 15.0)

    @classmethod
    def one_minute(cls):
        return cls(EWMA.M1_ALPHA, EWMA.INTERVAL)

    @classmethod
    def five_minutes(cls):
        return cls(EWMA.M5_ALPHA, EWMA.INTERVAL)

    @classmethod
    def fifteen_minutes(cls):
        return cls(EWMA.M15_ALPHA, EWMA.INTERVAL)

    def __init__(self, alpha, interval=INTERVAL):
        self._interval = float(interval)
        self._alpha = alpha
        self._uncounted = 0
        self._initialized = False
        self._rate = 0

    @property
    def rate(self):
        ''' Returns the rate in units per second. '''
        return self._rate

    def update(self, n=1):
        self._uncounted += n

    def tick(self):
        count = float(self._uncounted)
        self._uncounted = 0

        instant_rate = count / self._interval

        if self._initialized:
            self._rate += (self._alpha * (instant_rate - self._rate))
        else:
            self._rate = instant_rate
            self._initialized = True
