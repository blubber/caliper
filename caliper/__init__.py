
from . import metric, registry, reservoir, snapshot

from .metric import (
    Counter,
    EWMA,
    Gauge,
    Histogram,
    Meter,
    Timer,
)
from .registry import Registry
from .reservoir import (
    ExponentiallyDecayingReservoir,
    Reservoir,
    SlidingWindowReservoir,
    UniformReservoir,
)
from .snapshot import Snapshot, WeightedSnapshot

__all__ = [
    'metric', 'registry', 'reservoir', 'snapshot',
    'Counter', 'Gauge', 'Histogram', 'Timer', 'Meter', 'EWMA',
    'Reservoir', 'SlidingWindowReservoir', 'UniformReservoir',
    'ExponentiallyDecayingReservoir', 'Registry',
    'Snapshot', 'WeightedSnapshot',
    'create_metric', 'counter', 'gauge', 'histogram', 'meter', 'timer',
]


def create_metric(cls, name, *args, **kwargs):
    metric = cls(*args, **kwargs)
    Registry.default_registry().register(name, metric)
    return metric


def counter(name, *args, **kwargs):
    return Counter(*args, **kwargs)


def gauge(name, *args, **kwargs):
    return Gauge(*args, **kwargs)


def histogram(name, *args, **kwargs):
    return Histogram(*args, **kwargs)


def meter(name, *args, **kwargs):
    return Meter(*args, **kwargs)


def timer(name, *args, **kwargs):
    return Timer(*args, **kwargs)
