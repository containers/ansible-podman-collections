from __future__ import absolute_import

__metaclass__ = type

import pytest

from ansible_collections.containers.podman.plugins.module_utils.podman.quadlet import (
    BuildQuadlet,
)


def _default_params(**overrides):
    params = dict(
        annotation=None,
        arch=None,
        authfile=None,
        build_args=None,
        ca_cert_dir=None,
        cache=None,
        cmd_args=None,
        dns=None,
        dns_opt=None,
        dns_search=None,
        env=None,
        file=None,
        force_rm=None,
        group_add=None,
        ignore_file=None,
        name=None,
        labels=None,
        network=None,
        password=None,
        pull=None,
        retry=None,
        retry_delay=None,
        secret=None,
        set_working_directory=None,
        target=None,
        username=None,
        validate_certs=None,
        variant=None,
        volume=None,
        quadlet_options=None,
    )
    params.update(overrides)
    return params


def _build_content(**overrides):
    return BuildQuadlet(_default_params(**overrides)).create_quadlet_content()


class TestBuildQuadletMinimal:

    def test_minimal_with_file(self):
        content = _build_content(name="localhost/myimage:v1", file="/tmp/Containerfile")
        assert "[Build]\n" in content
        assert "File=/tmp/Containerfile\n" in content
        assert "ImageTag=localhost/myimage:v1\n" in content

    def test_minimal_with_working_directory(self):
        content = _build_content(name="myimage", set_working_directory="/src")
        assert "SetWorkingDirectory=/src\n" in content
        assert "ImageTag=myimage\n" in content


class TestBuildQuadletLabels:

    def test_labels_use_singular_key(self):
        content = _build_content(
            name="myimage",
            file="/tmp/Containerfile",
            labels={"maintainer": "testuser", "version": "1.0"},
        )
        assert "Label=maintainer=testuser\n" in content
        assert "Label=version=1.0\n" in content
        assert "Labels=" not in content

    def test_single_label(self):
        content = _build_content(name="myimage", file="/tmp/Containerfile", labels={"app": "web"})
        assert "Label=app=web\n" in content


class TestBuildQuadletAnnotations:

    def test_annotations_expanded(self):
        content = _build_content(
            name="myimage",
            file="/tmp/Containerfile",
            annotation={"com.example.key": "value1", "com.example.key2": "value2"},
        )
        assert "Annotation=com.example.key=value1\n" in content
        assert "Annotation=com.example.key2=value2\n" in content


class TestBuildQuadletBuildArgs:

    def test_build_args_expanded(self):
        content = _build_content(
            name="myimage",
            file="/tmp/Containerfile",
            build_args={"HTTP_PROXY": "http://proxy:8080", "VERSION": "3.0"},
        )
        assert "BuildArg=HTTP_PROXY=http://proxy:8080\n" in content
        assert "BuildArg=VERSION=3.0\n" in content


class TestBuildQuadletEnvironment:

    def test_env_expanded(self):
        content = _build_content(
            name="myimage",
            file="/tmp/Containerfile",
            env={"FOO": "bar", "DEBUG": "1"},
        )
        assert "Environment=FOO=bar\n" in content
        assert "Environment=DEBUG=1\n" in content


class TestBuildQuadletNetwork:

    def test_multiple_networks(self):
        content = _build_content(
            name="myimage",
            file="/tmp/Containerfile",
            network=["host", "mynet"],
        )
        assert "Network=host\n" in content
        assert "Network=mynet\n" in content


class TestBuildQuadletDNS:

    def test_dns_options(self):
        content = _build_content(
            name="myimage",
            file="/tmp/Containerfile",
            dns=["8.8.8.8", "1.1.1.1"],
            dns_opt=["ndots:5"],
            dns_search=["example.com"],
        )
        assert "DNS=8.8.8.8\n" in content
        assert "DNS=1.1.1.1\n" in content
        assert "DNSOption=ndots:5\n" in content
        assert "DNSSearch=example.com\n" in content


class TestBuildQuadletSecrets:

    def test_single_secret(self):
        content = _build_content(
            name="myimage",
            file="/tmp/Containerfile",
            secret=["id=mysecret,src=/run/secrets/mysecret"],
        )
        assert "Secret=id=mysecret,src=/run/secrets/mysecret\n" in content

    def test_multiple_secrets(self):
        content = _build_content(
            name="myimage",
            file="/tmp/Containerfile",
            secret=["id=aws,src=/root/.aws/creds", "id=ssh,src=/root/.ssh/id_rsa"],
        )
        assert "Secret=id=aws,src=/root/.aws/creds\n" in content
        assert "Secret=id=ssh,src=/root/.ssh/id_rsa\n" in content


class TestBuildQuadletCredentials:

    def test_username_password_becomes_podman_args(self):
        content = _build_content(
            name="myimage",
            file="/tmp/Containerfile",
            username="user",
            password="pass",
        )
        assert "PodmanArgs=--creds user:pass\n" in content

    def test_no_creds_without_both(self):
        content = _build_content(name="myimage", file="/tmp/Containerfile", username=None, password=None)
        assert "--creds" not in content


class TestBuildQuadletCacheAndCertDir:

    def test_cache_false_adds_no_cache(self):
        content = _build_content(name="myimage", file="/tmp/Containerfile", cache=False)
        assert "PodmanArgs=--no-cache\n" in content

    def test_cache_true_no_flag(self):
        content = _build_content(name="myimage", file="/tmp/Containerfile", cache=True)
        assert "--no-cache" not in content

    def test_ca_cert_dir(self):
        content = _build_content(name="myimage", file="/tmp/Containerfile", ca_cert_dir="/etc/certs")
        assert "PodmanArgs=--cert-dir /etc/certs\n" in content


class TestBuildQuadletCmdArgs:

    def test_cmd_args_appended_to_podman_args(self):
        content = _build_content(
            name="myimage",
            file="/tmp/Containerfile",
            cmd_args=["--log-level=debug", "--storage-driver=overlay"],
        )
        assert "PodmanArgs=--log-level=debug\n" in content
        assert "PodmanArgs=--storage-driver=overlay\n" in content


class TestBuildQuadletScalarParams:

    @pytest.mark.parametrize(
        "param, value, expected_key, expected_value",
        [
            ("arch", "amd64", "Arch", "amd64"),
            ("authfile", "/run/auth.json", "AuthFile", "/run/auth.json"),
            ("force_rm", True, "ForceRM", "true"),
            ("force_rm", False, "ForceRM", "false"),
            ("pull", "always", "Pull", "always"),
            ("retry", 5, "Retry", "5"),
            ("retry_delay", "10s", "RetryDelay", "10s"),
            ("target", "builder", "Target", "builder"),
            ("validate_certs", True, "TLSVerify", "true"),
            ("validate_certs", False, "TLSVerify", "false"),
            ("variant", "v8", "Variant", "v8"),
            ("ignore_file", "/tmp/.containerignore", "IgnoreFile", "/tmp/.containerignore"),
        ],
    )
    def test_scalar_param(self, param, value, expected_key, expected_value):
        content = _build_content(name="myimage", file="/tmp/Containerfile", **{param: value})
        assert f"{expected_key}={expected_value}\n" in content


class TestBuildQuadletVolumes:

    def test_multiple_volumes(self):
        content = _build_content(
            name="myimage",
            file="/tmp/Containerfile",
            volume=["/src:/src:ro", "/cache:/cache"],
        )
        assert "Volume=/src:/src:ro\n" in content
        assert "Volume=/cache:/cache\n" in content


class TestBuildQuadletOptions:

    def test_quadlet_options_extra_section(self):
        content = _build_content(
            name="myimage",
            file="/tmp/Containerfile",
            quadlet_options=["[Install]\nWantedBy=default.target"],
        )
        assert "[Install]\nWantedBy=default.target" in content

    def test_quadlet_options_plain_key_value(self):
        content = _build_content(
            name="myimage",
            file="/tmp/Containerfile",
            quadlet_options=["SomeKey=SomeValue"],
        )
        assert "SomeKey=SomeValue\n" in content


class TestBuildQuadletNoneParamsOmitted:

    def test_none_params_not_in_output(self):
        content = _build_content(name="myimage", file="/tmp/Containerfile")
        for key in [
            "Annotation=",
            "Arch=",
            "BuildArg=",
            "DNS=",
            "DNSOption=",
            "DNSSearch=",
            "Environment=",
            "ForceRM=",
            "GroupAdd=",
            "IgnoreFile=",
            "Label=",
            "Network=",
            "Pull=",
            "Retry=",
            "RetryDelay=",
            "Secret=",
            "Target=",
            "TLSVerify=",
            "Variant=",
            "Volume=",
            "PodmanArgs=",
        ]:
            assert key not in content
