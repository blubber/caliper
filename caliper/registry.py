
from collections import UserDict
import re

RE_LABEL = re.compile(r'^[a-z_][a-z0-9_]*$', re.I)


class InvalidName(Exception):
    pass


class InvalidLabel(Exception):
    pass


class DuplicateName(Exception):
    pass


class Registry(UserDict):

    _default_registry = None

    @classmethod
    def default_registry(cls):
        if cls._default_registry is None:
            cls._default_registry = cls()
        return cls._default_registry

    def register(self, name, metric):
        labels = self._split_name(name)
        data = self.data

        while len(labels) > 0:
            label = labels.pop(0)

            if label in data:
                if isinstance(data[label], dict):
                    data = data[label]
                    continue
                else:
                    raise DuplicateName(name)
            elif len(labels) > 0:
                data[label] = {}
                data = data[label]
            else:
                data[label] = metric

    def query(self, name):
        labels = self._split_name(name)
        data = self.data
        while len(labels) > 0:
            label = labels.pop(0)

            if label in data:
                if len(labels) == 0:
                    return data[label]
                else:
                    data = data[label]
            else:
                return None

    def _split_name(self, name):
        labels = name.split('.')

        if len(labels) == 0:
            raise InvalidName(name)

        for label in labels:
            if not RE_LABEL.match(label):
                raise InvalidLabel('Label `{}` is invalid for name `^s`'.
                                   format(label, name))
        return labels

    __setitem__ = register
    __getitem__ = query
