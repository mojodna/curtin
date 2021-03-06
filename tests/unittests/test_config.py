# This file is part of curtin. See LICENSE file for copyright and license info.

import copy
import json
import textwrap

from curtin import config
from .helpers import CiTestCase


class TestMerge(CiTestCase):
    def test_merge_cfg_string(self):
        d1 = {'str1': 'str_one'}
        d2 = {'dict1': {'d1.e1': 'd1-e1'}}

        expected = {'str1': 'str_one', 'dict1': {'d1.e1': 'd1-e1'}}
        config.merge_config(d1, d2)
        self.assertEqual(d1, expected)


class TestCmdArg2Cfg(CiTestCase):
    def test_cmdarg_flat(self):
        self.assertEqual(config.cmdarg2cfg("foo=bar"), {'foo': 'bar'})

    def test_dict_dict(self):
        self.assertEqual(config.cmdarg2cfg("foo/v1/v2=bar"),
                         {'foo': {'v1': {'v2': 'bar'}}})

    def test_no_equal_raises_value_error(self):
        self.assertRaises(ValueError, config.cmdarg2cfg, "foo/v1/v2"),

    def test_json(self):
        self.assertEqual(
            config.cmdarg2cfg('json:foo/bar=["a", "b", "c"]', delim="/"),
            {'foo': {'bar': ['a', 'b', 'c']}})

    def test_cmdarg_multiple_equal(self):
        self.assertEqual(
            config.cmdarg2cfg("key=mykey=value"),
            {"key": "mykey=value"})

    def test_with_merge_cmdarg(self):
        cfg1 = {'foo': {'key1': 'val1', 'mylist': [1, 2]}, 'f': 'fval'}
        cfg2 = {'foo': {'key2': 'val2', 'mylist2': ['a', 'b']}, 'g': 'gval'}

        via_merge = copy.deepcopy(cfg1)
        config.merge_config(via_merge, cfg2)

        via_merge_cmdarg = copy.deepcopy(cfg1)
        config.merge_cmdarg(via_merge_cmdarg, 'json:=' + json.dumps(cfg2))

        self.assertEqual(via_merge, via_merge_cmdarg)


class TestConfigArchive(CiTestCase):
    def test_archive_dict(self):
        myarchive = _replace_consts(textwrap.dedent("""
            _ARCH_HEAD_
            - type: _CONF_TYPE_
              content: |
                key1: val1
                key2: val2
            - content: |
               _CONF_HEAD_
               key1: override_val1
        """))
        ret = config.load_config_archive(myarchive)
        self.assertEqual(ret, {'key1': 'override_val1', 'key2': 'val2'})

    def test_archive_string(self):
        myarchive = _replace_consts(textwrap.dedent("""
            _ARCH_HEAD_
            - |
              _CONF_HEAD_
              key1: val1
              key2: val2
            - |
              _CONF_HEAD_
              key1: override_val1
        """))
        ret = config.load_config_archive(myarchive)
        self.assertEqual(ret, {'key1': 'override_val1', 'key2': 'val2'})

    def test_archive_mixed_dict_string(self):
        myarchive = _replace_consts(textwrap.dedent("""
            _ARCH_HEAD_
            - type: _CONF_TYPE_
              content: |
                key1: val1
                key2: val2
            - |
              _CONF_HEAD_
              key1: override_val1
        """))
        ret = config.load_config_archive(myarchive)
        self.assertEqual(ret, {'key1': 'override_val1', 'key2': 'val2'})

    def test_recursive_string(self):
        myarchive = _replace_consts(textwrap.dedent("""
            _ARCH_HEAD_
            - |
              _ARCH_HEAD_
              - |
                _CONF_HEAD_
                key1: val1
                key2: val2
            - |
              _ARCH_HEAD_
               - |
                 _CONF_HEAD_
                 key1: override_val1
        """))
        ret = config.load_config_archive(myarchive)
        self.assertEqual(ret, {'key1': 'override_val1', 'key2': 'val2'})

    def test_recursive_dict(self):
        myarchive = _replace_consts(textwrap.dedent("""
            _ARCH_HEAD_
            - type: _CONF_TYPE_
              content: |
                key1: val1
                key2: val2
            - content: |
                _ARCH_HEAD_
                 - |
                   _CONF_HEAD_
                   key1: override_val1
        """))
        ret = config.load_config_archive(myarchive)
        self.assertEqual(ret, {'key1': 'override_val1', 'key2': 'val2'})


def _replace_consts(cfgstr):
    repls = {'_ARCH_HEAD_': config.ARCHIVE_HEADER,
             '_ARCH_TYPE_': config.ARCHIVE_TYPE,
             '_CONF_HEAD_': config.CONFIG_HEADER,
             '_CONF_TYPE_': config.CONFIG_TYPE}
    for k, v in repls.items():
        cfgstr = cfgstr.replace(k, v)
    return cfgstr

# vi: ts=4 expandtab syntax=python
