from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.containers.podman.plugins.module_utils.podman.podman_container_lib import (
    PodmanModuleParams,
    PodmanContainerDiff,
)


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (
            {
                "cap_add": ["SYS_ADMIN"],
                "name": "testcont",
                "image": "testimage",
                "command": None,
            },
            [
                b"create",
                b"--name",
                b"testcont",
                b"--cap-add",
                b"SYS_ADMIN",
                b"testimage",
            ],
        ),
        (
            {
                "stop_signal": 9,
                "name": "testcont",
                "image": "testimage",
                "command": None,
                "sig_proxy": True,
            },
            [
                b"create",
                b"--name",
                b"testcont",
                b"--stop-signal",
                b"9",
                b"--sig-proxy=True",
                b"testimage",
            ],
        ),
    ],
)
def test_container_add_params(test_input, expected):
    podm = PodmanModuleParams(
        "create",
        test_input,
        "4.0.0",
        None,
    )
    assert podm.construct_command_from_params() == expected


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (
            [
                None,  # module
                {"conmon_pidfile": "bbb"},  # module params
                {
                    "conmonpidfile": "ccc",
                    "config": {
                        "createcommand": [
                            "podman",
                            "create",
                            "--conmon-pidfile=ccc",
                            "testcont",
                        ]
                    },
                },  # container info
                {},  # image info
                "4.1.1",  # podman version
            ],
            True,
        ),
        (
            [
                None,  # module
                {"conmon_pidfile": None},  # module params
                {
                    "conmonpidfile": "ccc",
                    "config": {
                        "createcommand": [
                            "podman",
                            "create",
                            "--conmon-pidfile=ccc",
                            "testcont",
                        ]
                    },
                },  # container info
                {},  # image info
                "4.1.1",  # podman version
            ],
            True,
        ),
        (
            [
                None,  # module
                {"conmon_pidfile": None},  # module params
                {
                    "conmonpidfile": None,
                    "config": {
                        "createcommand": [
                            "podman",
                            "create",
                            "testcont",
                        ]
                    },
                },  # container info
                {},  # image info
                "4.1.1",  # podman version
            ],
            False,
        ),
        (
            [
                None,  # module
                {"conmon_pidfile": "aaa"},  # module params
                {
                    "conmonpidfile": None,
                    "config": {
                        "createcommand": [
                            "podman",
                            "create",
                            "testcont",
                        ]
                    },
                },  # container info
                {},  # image info
                "4.1.1",  # podman version
            ],
            True,
        ),
        (
            [
                None,  # module
                {"conmon_pidfile": "aaa"},  # module params
                {
                    "conmonpidfile": "aaa",
                    "config": {
                        "createcommand": [
                            "podman",
                            "create",
                            "--conmon-pidfile=aaa",
                            "testcont",
                        ]
                    },
                },  # container info
                {},  # image info
                "4.1.1",  # podman version
            ],
            False,
        ),
    ],
)
def test_container_diff(test_input, expected):
    diff = PodmanContainerDiff(*test_input)
    assert diff.diffparam_conmon_pidfile() == expected
