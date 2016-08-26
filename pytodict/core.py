import json
import inspect
from abc import ABCMeta, abstractmethod
from pytodict.custom_serializer_base import CustomSerializerBase

settings = dict()
settings['custom_serializers'] = dict()
settings['allow_constants'] = False


def set_global_setting(setting, value):
    global settings
    settings[setting] = value


def get_global_setting(setting):
    global settings
    return settings[setting]


def remove_global_setting(setting):
    global settings
    del settings[setting]


def add_custom_serializers(custom_serializers):
    global settings
    if isinstance(custom_serializers, dict):
        settings['custom_serializers'].update(custom_serializers)
    elif isinstance(custom_serializers, list):
        for custom_serializer in custom_serializers:
            settings['custom_serializers'][custom_serializer.class_name] = custom_serializer
    elif isinstance(custom_serializers, CustomSerializerBase):
        settings['custom_serializers'][custom_serializers.class_name] = custom_serializers


def del_custom_serializers(custom_serializers):
    global settings
    if isinstance(custom_serializers, dict):
        for custom_serializer in custom_serializers.keys():
            del settings['custom_serializers'][custom_serializer]

    elif isinstance(custom_serializers, list):
        for custom_serializer in custom_serializers:
            del settings['custom_serializers'][custom_serializer.class_name]

    elif isinstance(custom_serializers, CustomSerializerBase):
        del settings['custom_serializers'][custom_serializers.class_name]


def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


def _attribute_getter(obj):
    global settings
    attributes = set()

    if isinstance(obj, dict):
        for k in obj.keys():
            if(not callable(obj[k]) and (not isinstance(k, str) or (isinstance(k, str) and not
            k.startswith("_"))) and not isinstance(obj[k], staticmethod)):
                attributes.add(k)

    for attr, value in inspect.getmembers(obj.__class__,
                                          lambda a: not (inspect.isroutine(a)) or (isinstance(a, property))):
        if not attr.startswith('_') and (settings['allow_constants'] or (not settings['allow_constants'] and
           not attr.isupper())):
            attributes.add(attr)

    if hasattr(obj, "__dict__"):
        for attr, value in obj.__dict__.items():
            if not callable(value) and not attr.startswith("_") and not isinstance(value, staticmethod):
                attributes.add(attr)

    return attributes

'''
    for attr, value in obj.__class__.__dict__.items():
        if not callable(value) and not attr.startswith("_") and not isinstance(value, staticmethod):
            attributes.add(attr)

    for attr, value in inspect.getmembers(obj.__class__, lambda a: (isinstance(a, property))):
        attributes.add(attr)

    for attr, value in obj.__dict__.items():
        if not callable(value) and not attr.startswith("_") and not isinstance(value, staticmethod):
            attributes.add(attr)
'''


def _to_dict(obj, depth, custom_serializers, default=None, excluded_json_attr=list(), use_str_method=None,
             allow_no_obj=False):
    global settings
    if use_str_method is None and 'use_str_method' in settings:
        use_str_method = settings['use_str_method']
    elif use_str_method is None:
        use_str_method = False

    depth += 1
    if depth > 400:
        raise AttributeError("maximum recursion depth exceeded while calling a Python object")

    if isinstance(obj, ToDict):
        return obj.to_dict(depth, custom_serializers, default=default, excluded_json_attr=excluded_json_attr,
                                      use_str_method=use_str_method, allow_no_obj=allow_no_obj)

    # if hasattr(obj, "__module__") and (obj.__module__ + "." + obj.__class__.__name__) in custom_serializers:
    if hasattr(obj, "__module__") and (str(obj.__class__)) in custom_serializers:
        return custom_serializers[str(obj.__class__)].serialize(obj)

    json_attr = set()
    for clazz in type(obj).mro():
        json_attr |= set(getattr(clazz, "_excluded_json_attr", []))
    json_attr |= set(excluded_json_attr)

    attributes = _attribute_getter(obj)
    values = dict()

    # if hasattr(obj, "__module__") and (obj.__module__ + "." + obj.__class__.__name__) in custom_serializers:
    #    return custom_serializers[obj.__module__ + "." + obj.__class__.__name__].serialize(obj)

    if isinstance(obj, list):
        if depth == 1 and not allow_no_obj:
            raise AttributeError("Can't covert a list to dict")

        l = []

        for item in obj:
            l.append(_to_dict(item, depth, custom_serializers, default=default,
                              excluded_json_attr=excluded_json_attr))
        return l

    elif isinstance(obj, tuple):
        if depth == 1 and not allow_no_obj:
            raise AttributeError("Can't covert a tuple to list")

        l = []

        for item in obj:
            l.append(_to_dict(item, depth, custom_serializers, default=default,
                              excluded_json_attr=excluded_json_attr))
        return tuple(l)

    elif isinstance(obj, str) or isinstance(obj, int) or isinstance(obj, bool):
        if depth == 1 and not allow_no_obj:
            raise AttributeError("Can't covert a list to dict")

        return obj

    elif obj.__class__.__name__ == "datetime":
        return obj.__str__()

    if len(attributes) == 0 and default is not None:
        return _to_dict(default(obj), depth, custom_serializers, default=default,
                        excluded_json_attr=excluded_json_attr)

    for k in attributes:
        if not isinstance(obj, dict):
            v = getattr(obj, k)
        else:
            v = obj[k]

        if k not in json_attr:
            if isinstance(v, dict):
                if len(v) == 0:
                    values[k] = {}
                    continue
                values[k] = {}
                for k2 in v.keys():
                    values[k][k2] = _to_dict(v[k2], depth, custom_serializers, default=default,
                                             excluded_json_attr=excluded_json_attr)
            elif isinstance(v, list):
                values[k] = _to_dict(v, depth, custom_serializers, default=default,
                                     excluded_json_attr=excluded_json_attr)

            elif isinstance(v, str) or isinstance(v, int) or isinstance(v, bool):
                values[k] = v

            elif hasattr(v, "to_json") and callable(getattr(v, "to_json")):
                values[k] = _to_dict(v, depth, custom_serializers, default=default,
                                     excluded_json_attr=excluded_json_attr)

            elif default is not None:
                values[k] = _to_dict(default(v), depth, custom_serializers, default=default,
                                     excluded_json_attr=excluded_json_attr)

            elif hasattr(v, 'to_dict'):
                values[k] = v.to_dict(depth, custom_serializers, default=default, excluded_json_attr=excluded_json_attr,
                                      use_str_method=use_str_method, allow_no_obj=allow_no_obj)

            elif hasattr(v, "__str__") and callable(getattr(v, "__str__")) and use_str_method:
                values[k] = v.__str__()

            elif isinstance(v, object):
                values[k] = _to_dict(v, depth, custom_serializers, default=default,
                                     excluded_json_attr=excluded_json_attr)
            # else:
                # values[k] = self._to_dict(depth, custom_serializers, obj=v.__dict__)

    return values


def to_json(obj, default=None, custom_serializers=None, sort_keys=False, indent=None, separators=None,
            excluded_json_attr=list(), use_str_method=None):

    return json.dumps(to_dict(obj, custom_serializers=custom_serializers, default=default,
                              excluded_json_attr=excluded_json_attr, use_str_method=use_str_method, allow_no_obj=True),
                      sort_keys=sort_keys, indent=indent, separators=separators)


def to_dict(obj, default=None, custom_serializers=None, excluded_json_attr=list(), use_str_method=None,
            allow_no_obj=False):
    global settings
    cs = {}
    if custom_serializers is not None and not isinstance(custom_serializers, dict):
        if not isinstance(custom_serializers, list):
            cs[custom_serializers.class_name] = custom_serializers
        else:
            for custom_serializer in custom_serializers:
                cs[custom_serializer.class_name] = custom_serializer

    if 'custom_serializers' in settings:
        cs = merge_two_dicts(cs, settings['custom_serializers'])

    if 'allow_constants' not in settings:
        settings['allow_constants'] = False

    return _to_dict(obj, 0, cs, default=default, excluded_json_attr=excluded_json_attr, use_str_method=use_str_method,
                    allow_no_obj=allow_no_obj)


class ModelBase(object):
    def to_json(self, default=None, custom_serializers=None, sort_keys=False, indent=None, excluded_json_attr=list(),
                use_str_method=None):
        # separators=None,
        return to_json(self, default=default, custom_serializers=custom_serializers, sort_keys=sort_keys, indent=indent,
                       excluded_json_attr=excluded_json_attr, use_str_method=use_str_method)

    def to_dict(self, default=None, custom_serializers=None, excluded_json_attr=list(), use_str_method=None):
        return to_dict(self, custom_serializers=custom_serializers, default=default,
                       excluded_json_attr=excluded_json_attr, use_str_method=use_str_method)


class ToDict(metaclass=ABCMeta):
    @abstractmethod
    def to_dict(self, depth, custom_serializers, default=None, excluded_json_attr=list(), use_str_method=None,
             allow_no_obj=False):
        pass
