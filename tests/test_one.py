import unittest2
import sys
import datetime
from enum import Enum
sys.path.insert(0, "../pytodict")  # prefer local version

from pytodict.custom_serializer_base import CustomSerializerBase
from pytodict.core import ModelBase, to_dict, to_json, add_custom_serializers, set_global_setting, ToDict, _to_dict



class TestOne(unittest2.TestCase):
    def test_class_parameter(self):
        class T:
            l = ['test', 'epa']

            def __init__(self):
                self.t = ['a']

        d = to_dict(T())
        self.assertTrue('l' in d)
        self.assertTrue('t' in d)

    def test_dict(self):
        d1 = {'t': 1, 's': 2}
        d = to_dict(d1)

        self.assertDictEqual(d1, d)

    def test_exception_if_list(self):
        e = None
        try:
            l = ['t', 'e', 's', 't']
            to_dict(l)
        except AttributeError as e1:
            e = e1

        self.assertIsInstance(e, AttributeError)

    def test_list(self):
        class Foo(ModelBase):
            def __init__(self):
                self.l = ['t', 'e', 's', 't']

        d = Foo().to_dictionary()
        self.assertTrue('l' in d)
        self.assertTrue(isinstance(d['l'], list))

    def test_excluded_attr(self):
        class Foo(ModelBase):
            _excluded_json_attr = ['a1', 'b2']

            def __init__(self):
                self._aaa = 2
                self.a2 = 2
                self.a1 = 1
                self.b2 = "hello"
                self.c = "hidden"
                self.d1 = {"4": 1}

        foo = Foo()
        d = to_dict(foo)

        self.assertTrue('a2' in d)
        self.assertFalse('a1' in d)
        self.assertDictEqual(d['d1'], foo.d1)

    def test_excluded_attr_nestled(self):
        class SubFoo(ModelBase):
            _excluded_json_attr = ['t4']

            def __init__(self):
                self.t4 = 2
                self.t44 = 3

            def __str__(self):
                return "(%i, %i)" % (self.t4, self.t44)

        class Foo(ModelBase):
            def __init__(self):
                self.t2 = 22
                self.t4 = 4
                self.t3 = SubFoo()

        d = to_dict(Foo())
        self.assertTrue('t4' in d)
        self.assertFalse('t4' in d['t3'])

    def test_excluded_attr_nestled_list(self):
        class SubFoo(ModelBase):
            _excluded_json_attr = ['t4']

            def __init__(self):
                self.t4 = 2
                self.t44 = 3

            def __str__(self):
                return "(%i, %i)" % (self.t4, self.t44)

        class Foo(ModelBase):
            def __init__(self):
                self.t2 = 22
                self.t4 = 4
                self.t3 = [SubFoo(), SubFoo()]

        d = to_dict(Foo())
        self.assertTrue('t4' in d)
        self.assertFalse('t4' in d['t3'][0])

    def test_included_class(self):
        class SubFoo(ModelBase):
            def __init__(self):
                self.t4 = 2
                self.t44 = 3

            def __str__(self):
                return "(%i, %i)" % (self.t4, self.t44)

        class Foo(ModelBase):
            def __init__(self):
                self.t2 = 22
                self.t3 = SubFoo()

        foo = Foo()
        d = to_dict(foo)

        self.assertTrue('t2' in d)
        self.assertTrue('t4' in d['t3'])
        self.assertEqual(d['t3']['t4'], 2)

    def test_custom_serializer(self):
        class FoSerializer(CustomSerializerBase):
            def __init__(self):
                super(FoSerializer, self).__init__(self.get_module_and_class_name(Foo))

            def serialize(self, obj):
                return {
                    "monkey": obj.t4,
                    "giraffe": obj.t44
                }

        class Foo(ModelBase):
            _excluded_json_attr = ['a1', 'b2']

            def __init__(self):
                self.t4 = 4
                self.t44 = 44

        d = to_dict(Foo(), custom_serializers=FoSerializer())
        self.assertTrue('monkey' in d)

    def test_custom_serializer_global(self):
        class FooWithSerializer(ModelBase):
            _excluded_json_attr = ['a1', 'b2']

            def __init__(self):
                self.t4 = 4
                self.t44 = 44

        class FoSerializer(CustomSerializerBase):
            def __init__(self):
                super(FoSerializer, self).__init__(self.get_module_and_class_name(FooWithSerializer))

            def serialize(self, obj):
                return {
                    "monkey": obj.t4,
                    "giraffe": obj.t44
                }

        add_custom_serializers(FoSerializer())
        d = to_dict(FooWithSerializer())
        self.assertTrue('monkey' in d)

    def test_property(self):
        class Foo:
            def __init__(self):
                self._t1 = 12
                self.t2 = 13

            @property
            def t1(self):
                return self._t1

        d = to_dict(Foo())
        self.assertTrue('t1' in d)
        self.assertTrue('t2' in d)

    def test_str(self):
        class AlarmState(Enum):
            DISABLED = (1, "disabled")

            def __init__(self, value, description):
                self.__dict__['value'] = value
                self.description = description

            def describe(self):
                return self.description

            def __str__(self):
                return "%s" % self.describe()

        class Foo:
            def __init__(self):
                self.state = AlarmState.DISABLED

        d = to_dict(Foo())
        self.assertTrue('state' in d)

        set_global_setting('allow_constants', True)
        error = False
        try:
            to_dict(Foo())
        except AttributeError:
            error = True
        self.assertTrue(error)
        set_global_setting('allow_constants', False)

        d = to_dict(Foo(), use_str_method=True)
        self.assertTrue('state' in d)
        self.assertEqual('disabled', d['state'])

    def test_tuple(self):
        class Foo:
            t = (12, 'test', 'epa')

        d = to_dict(Foo())
        self.assertTrue('t' in d)
        self.assertEqual(len(d['t']), 3)
        self.assertEqual(d['t'][0], 12)

    def test_json(self):
        class Foo:
            t = (12, 'test', 'epa')

        d = to_json(Foo())
        self.assertTrue(isinstance(d, str))
        self.assertTrue('{"t": ' in d)
        self.assertTrue("12" in d)
        self.assertTrue('"test"' in d)
        self.assertTrue('"epa"' in d)

    def test_json_non_obj(self):
        t = (12, 'test', 'epa')

        d = to_json(t)
        self.assertTrue(isinstance(d, str))
        self.assertTrue("12" in d)
        self.assertTrue('"test"' in d)
        self.assertTrue('"epa"' in d)

        try:
            to_dict(t)
            self.assertTrue(False)
        except AttributeError:
            pass

    def test_to_dict_function(self):
        class Foo(ToDict):
            def to_dict(self, depth, custom_serializers, default=None, excluded_json_attr=list(), use_str_method=None,
                        allow_no_obj=False):
                return {"t11": self.t1, "t22": _to_dict(self.t2, depth, custom_serializers, default=default,
                                                        excluded_json_attr=excluded_json_attr,
                                                        use_str_method=use_str_method)}

            def __init__(self):
                self.t1 = (12, 'test', 'epa')
                self.t2 = Foo2()

        class Foo2:
            def __init__(self):
                self.a1 = 1
                self.a2 = 2

        class Foo3:
            def __init__(self):
                self.c1 = 1
                self.c2 = Foo()

        d = to_dict(Foo())
        self.assertTrue("t11" in d)
        self.assertTrue("t22" in d)
        self.assertFalse("t1" in d)
        self.assertFalse("t2" in d)
        self.assertTrue(len(d["t22"]), 2)
        d = to_dict(Foo3())
        self.assertTrue("t11" in d["c2"])
        self.assertTrue("t22" in d["c2"])
        self.assertFalse("t1" in d["c2"])
        self.assertFalse("t2" in d["c2"])
        self.assertTrue(len(d["c2"]["t22"]), 2)

    def test_status_msg(self):
        status = {'date': datetime.datetime.utcnow()}

        d = to_dict(status)
        self.assertEqual(str(status['date']), str(d['date']))


if __name__ == '__main__':
    unittest2.main()
