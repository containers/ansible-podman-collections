from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from plugins.module_utils.podman.podman_container_lib import (
    PodmanContainerDiff,
)

# To run it with pytest, VSCode, debugger etc etc
# Do it from collection root directory:
#
# mkdir -p ansible_collections/containers/podman
# touch ansible_collections/__init__.py
# touch ansible_collections/containers/__init__.py
# touch ansible_collections/containers/podman/__init__.py
# touch plugins/__init__.py
# ln -s $PWD/plugins ansible_collections/containers/podman/plugins


# In order to test the diff function, we need to patch the _diff_update_and_compare function
def substitute_update_and_compare(instance_diff, param_name, before, after):
    return before, after


@pytest.fixture
def diff_patched(monkeypatch):
    monkeypatch.setattr(
        PodmanContainerDiff, "_diff_update_and_compare", substitute_update_and_compare
    )


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (
            [
                None,  # module
                {"volume": ["/mnt:/tmp"]},  # module params
                {
                    "mounts": [
                        {
                            "type": "bind",
                            "source": "/mnt",
                            "destination": "/tmp",
                            "driver": "",
                            "mode": "",
                            "options": ["rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        }
                    ],
                    "config": {
                        "createcommand": [
                            "podman",
                            "-v",
                            "/mnt:/tmp",
                        ],
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
                {"volume": ["/tmp"]},  # module params
                {
                    "mounts": [
                        {
                            "type": "volume",
                            "name": "f92e0010df188214805a7f1007683d42c72f3b1bc5c4a14f2e63d42d15c80308",
                            "source": "/home/user/.local/share/containers/storage/volumes/somehash/_data",
                            "destination": "/tmp",
                            "driver": "local",
                            "mode": "",
                            "options": ["nosuid", "nodev", "rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        }
                    ],
                    "config": {
                        "createcommand": [
                            "podman",
                            "-v",
                            "/tmp",
                        ],
                    },
                },  # container info
                {},  # image info
                "4.1.1",  # podman version
            ],
            True,
        ),
    ],
)
def test_basic_volume_diff(diff_patched, test_input, expected):
    diff = PodmanContainerDiff(*test_input)
    result = diff.diffparam_volumes_all()  # before, after
    assert (set(result[0]) == set(result[1])) == expected


@pytest.mark.parametrize(
    "test_input, expected, change",
    [
        (
            [
                None,  # module
                {"volume": ["/mnt:/data1"]},  # module params
                {
                    "mounts": [
                        {
                            "type": "bind",
                            "source": "/mnt",
                            "destination": "/tmp",
                            "driver": "",
                            "mode": "",
                            "options": ["rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        }
                    ],
                    "config": {
                        "createcommand": [
                            "podman",
                            "-v",
                            "/mnt:/tmp",
                        ],
                    },
                },  # container info
                {},  # image info
                "4.1.1",  # podman version
            ],
            False,
            ["dst=/tmp", "dst=/data1"],
        ),
        (
            [
                None,  # module
                {"volume": ["/mnt"]},  # module params
                {
                    "mounts": [
                        {
                            "type": "bind",
                            "source": "/mnt",
                            "destination": "/tmp",
                            "driver": "",
                            "mode": "",
                            "options": ["rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        }
                    ],
                    "config": {
                        "createcommand": [
                            "podman",
                            "-v",
                            "/mnt:/tmp",
                        ],
                    },
                },  # container info
                {},  # image info
                "4.1.1",  # podman version
            ],
            False,
            ["dst=/tmp", "dst=/mnt"],
        ),
    ],
)
def test_basic_volume_diff_change(diff_patched, test_input, expected, change):
    diff = PodmanContainerDiff(*test_input)
    result = diff.diffparam_volumes_all()  # before, after
    assert (result[0] == result[1]) == expected
    assert change[0] in result[0][0]
    assert change[1] in result[1][0]


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (
            [
                None,  # module
                {"volume": ["/mnt/", "/data1:/data2/", "./data"]},  # module params
                {
                    "mounts": [
                        {
                            "type": "volume",
                            "name": "647fda605f70e34d37845a3bda6d01108eb07742beb16865a7a46b5e89f0deb6",
                            "source": "/home/sshnaidm/.local/share/containers/storage/volumes/some_hash/_data",
                            "destination": "/mnt/",
                            "driver": "local",
                            "mode": "",
                            "options": ["nosuid", "nodev", "rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        },
                        {
                            "type": "volume",
                            "name": "b74a7b937ecb0fbccb50a158ed872b04318fb997b0e70a3ccdd16a90196acd06",
                            "source": "/home/sshnaidm/.local/share/containers/storage/volumes/some_hash2/_data",
                            "destination": "/home/user/data",
                            "driver": "local",
                            "mode": "",
                            "options": ["nosuid", "nodev", "rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        },
                        {
                            "type": "bind",
                            "source": "/data1",
                            "destination": "/data2/",
                            "driver": "",
                            "mode": "",
                            "options": ["nosuid", "nodev", "rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        },
                    ],
                    "config": {
                        "createcommand": [
                            "podman",
                            "-v",
                            "/mnt/",
                            "-v",
                            "/data1:/data2/",
                            "-v",
                            "./data",
                        ],
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
                {
                    "volume": ["/mnt/", "/dev/fuse", "named_one:/named", "vvv:/datax"]
                },  # module params
                {
                    "mounts": [
                        {
                            "type": "volume",
                            "name": "09e94208842f5a1e686c0c2e72df9f9d13f7a479d5e1a114a0e6287ff43685f3",
                            "source": "/home/sshnaidm/.local/share/containers/storage/volumes/hash/_data",
                            "destination": "/dev/fuse",
                            "driver": "local",
                            "mode": "",
                            "options": ["nosuid", "nodev", "rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        },
                        {
                            "type": "volume",
                            "name": "named_one",
                            "source": "/home/sshnaidm/.local/share/containers/storage/volumes/named_one/_data",
                            "destination": "/named",
                            "driver": "local",
                            "mode": "",
                            "options": ["nosuid", "nodev", "rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        },
                        {
                            "type": "volume",
                            "name": "vvv",
                            "source": "/home/sshnaidm/.local/share/containers/storage/volumes/vvv/_data",
                            "destination": "/datax",
                            "driver": "local",
                            "mode": "",
                            "options": ["nosuid", "nodev", "rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        },
                        {
                            "type": "volume",
                            "name": "d4d5990d184da6572b2bd3ae879bd1275a52d77fdb1e92d435e874b7490f8148",
                            "source": "/home/sshnaidm/.local/share/containers/storage/volumes/hash1/_data",
                            "destination": "/mnt/",
                            "driver": "local",
                            "mode": "",
                            "options": ["nosuid", "nodev", "rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        },
                    ],
                    "config": {
                        "createcommand": [
                            "podman",
                            "-v",
                            "/mnt/",
                            "-v",
                            "/dev/fuse",
                            "-v",
                            "named_one:/named",
                            "-v",
                            "vvv:/datax",
                        ],
                    },
                },  # container info
                {},  # image info
                "4.1.1",  # podman version
            ],
            True,
        ),
    ],
)
def test_basic_multiple_volume_diff(diff_patched, test_input, expected):
    diff = PodmanContainerDiff(*test_input)
    result = diff.diffparam_volumes_all()  # before, after
    assert (set(result[0]) == set(result[1])) == expected


@pytest.mark.parametrize(
    "test_input, expected, change",
    [
        (
            [
                None,  # module
                {"volume": ["/data1:/data5/", "./data"]},  # module params
                {
                    "mounts": [
                        {
                            "type": "volume",
                            "name": "647fda605f70e34d37845a3bda6d01108eb07742beb16865a7a46b5e89f0deb6",
                            "source": "/home/sshnaidm/.local/share/containers/storage/volumes/some_hash/_data",
                            "destination": "/mnt/",
                            "driver": "local",
                            "mode": "",
                            "options": ["nosuid", "nodev", "rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        },
                        {
                            "type": "volume",
                            "name": "b74a7b937ecb0fbccb50a158ed872b04318fb997b0e70a3ccdd16a90196acd06",
                            "source": "/home/sshnaidm/.local/share/containers/storage/volumes/some_hash2/_data",
                            "destination": "/home/user/data",
                            "driver": "local",
                            "mode": "",
                            "options": ["nosuid", "nodev", "rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        },
                        {
                            "type": "bind",
                            "source": "/data1",
                            "destination": "/data2/",
                            "driver": "",
                            "mode": "",
                            "options": ["nosuid", "nodev", "rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        },
                    ],
                    "config": {
                        "createcommand": [
                            "podman",
                            "-v",
                            "/mnt/",
                            "-v",
                            "/data1:/data2/",
                            "-v",
                            "./data",
                        ],
                    },
                },  # container info
                {},  # image info
                "4.1.1",  # podman version
            ],
            False,
            ["dst=/mnt", "dst=/data5"],
        ),
        (
            [
                None,  # module
                {
                    "volume": ["/mnt/", "newvol:/newvol1", "named_one:/named", "vvv:/datax"]
                },  # module params
                {
                    "mounts": [
                        {
                            "type": "volume",
                            "name": "09e94208842f5a1e686c0c2e72df9f9d13f7a479d5e1a114a0e6287ff43685f3",
                            "source": "/home/sshnaidm/.local/share/containers/storage/volumes/hash/_data",
                            "destination": "/dev/fuse",
                            "driver": "local",
                            "mode": "",
                            "options": ["nosuid", "nodev", "rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        },
                        {
                            "type": "volume",
                            "name": "named_one",
                            "source": "/home/sshnaidm/.local/share/containers/storage/volumes/named_one/_data",
                            "destination": "/named",
                            "driver": "local",
                            "mode": "",
                            "options": ["nosuid", "nodev", "rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        },
                        {
                            "type": "volume",
                            "name": "vvv",
                            "source": "/home/sshnaidm/.local/share/containers/storage/volumes/vvv/_data",
                            "destination": "/datax",
                            "driver": "local",
                            "mode": "",
                            "options": ["nosuid", "nodev", "rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        },
                        {
                            "type": "volume",
                            "name": "d4d5990d184da6572b2bd3ae879bd1275a52d77fdb1e92d435e874b7490f8148",
                            "source": "/home/sshnaidm/.local/share/containers/storage/volumes/hash1/_data",
                            "destination": "/mnt/",
                            "driver": "local",
                            "mode": "",
                            "options": ["nosuid", "nodev", "rbind"],
                            "rw": True,
                            "propagation": "rprivate",
                        },
                    ],
                    "config": {
                        "createcommand": [
                            "podman",
                            "-v",
                            "/mnt/",
                            "-v",
                            "/dev/fuse",
                            "-v",
                            "named_one:/named",
                            "-v",
                            "vvv:/datax",
                        ],
                    },
                },  # container info
                {},  # image info
                "4.1.1",  # podman version
            ],
            False,
            ["dst=/dev/fuse", "src=newvol"],
        ),
    ],
)
def test_basic_multiple_volume_diff_change(diff_patched, test_input, expected, change):
    diff = PodmanContainerDiff(*test_input)
    result = diff.diffparam_volumes_all()  # before, after
    assert (result[0] == result[1]) == expected
    assert change[0] in " ".join(list(result[0]))
    assert change[1] in " ".join(list(result[1]))
