from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.containers.podman.plugins.module_utils.podman.common import (
    lower_keys,
)


@pytest.mark.parametrize('test_input, expected', [
    (["AAA", "BBB"], ["AAA", "BBB"]),
    ("AAQQ", "AAQQ"),
    ({"AAA": "AaaAa", "11": 22, "AbCdEf": None, "bbb": "aaaAA"},
     {"aaa": "AaaAa", "11": 22, "abcdef": None, "bbb": "aaaAA"})
])
def test_lower_keys(test_input, expected):
    print(lower_keys.__code__.co_filename)
    assert lower_keys(test_input) == expected
