from abc import ABCMeta, abstractmethod


class CustomSerializerBase(metaclass=ABCMeta):
    def __init__(self, class_name):
        self._class_name = class_name

    @abstractmethod
    def serialize(self, obj):
        return ""

    @property
    def class_name(self):
        return self._class_name

    @class_name.setter
    def class_name(self, val):
        self._class_name = val

    @staticmethod
    def get_module_and_class_name(clazz):
        if hasattr(clazz, "__module__"):
            return clazz.__module__ + "." + clazz.__name__
        else:
            return clazz.__name__
