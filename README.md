# Caliper

Caliper lets you easily measure aspects of your app. If is inspired by
the Metrics library for Java.

## Example

```python
>>> import random, time, caliper
>>> timer = caliper.timer()
>>> for i in range(10):
...     with timer.time():
...         time.sleep(random.random())
>>> snapshot = timer.snapshot()
>>> min(snapshot), snapshot.mean, max(snapshot), snapshot.stddev
(0.04058, 0.5666512047313835, 0.971152, 0.29092769932094975)
```
