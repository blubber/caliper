from functools import partial
import re
import uuid

from caliper import metric, reservoir, snapshot

from caliper.metric import (
    Counter,
    EWMA,
    Gauge,
    Histogram,
    Meter,
    Timer,
)
from caliper.reservoir import (
    ExponentiallyDecayingReservoir,
    Reservoir,
    SlidingWindowReservoir,
    UniformReservoir,
)
from caliper.snapshot import Snapshot, WeightedSnapshot

__all__ = [
    'metric', 'registry', 'reservoir', 'snapshot',
    'Counter', 'Gauge', 'Histogram', 'Timer', 'Meter', 'EWMA',
    'Reservoir', 'SlidingWindowReservoir', 'UniformReservoir',
    'ExponentiallyDecayingReservoir', 'Registry',
    'Snapshot', 'WeightedSnapshot',
    'create_metric', 'counter', 'gauge', 'histogram', 'meter', 'timer',
]


_registry = {}


def get_or_create_metric(cls, name=None, *args, **kwargs):
    name = name or ('a%s' % uuid.uuid4().hex)
    key = _split_registry_key('%s.%s' % (name, cls.__name__))

    metric = _registry.get(key)
    if metric:
        if not type(metric) is cls:
            raise TypeError('A metric with key %s already exists with type %s' %
                    ('.'.join(key), metric.__class__))
    else:
        metric = cls(*args, **kwargs)
        _registry[key] = metric

    return metric


counter = partial(get_or_create_metric, Counter)
gauge = partial(get_or_create_metric, Gauge)
histogram = partial(get_or_create_metric, Histogram)
meter = partial(get_or_create_metric, Meter)
timer = partial(get_or_create_metric, Timer)


def _split_registry_key(keystr):
    match = re.match('^([a-zA-Z][a-zA-Z0-9_]*)(?:\.([a-zA-Z][a-zA-Z0-9_]*))*$', keystr)
    if not match:
        raise ValueError("'%s' is in invalid registry key" % keystr)

    return tuple(keystr.split('.'))
