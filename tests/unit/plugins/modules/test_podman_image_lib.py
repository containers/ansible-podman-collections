from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.containers.podman.plugins.module_utils.podman.podman_image_lib import ImageRepository


class TestImageRepository:
    """Unit tests for ImageRepository class - specifically testing issue #947 fix."""

    @pytest.mark.parametrize(
        "name, tag, expected_full_name, expected_delimiter, description",
        [
            # Issue #947 scenario: tag with version and digest should use : delimiter
            (
                "docker.io/valkey/valkey",
                "8-bookworm@sha256:fec42f399876eb6faf9e008570597741c87ff7662a54185593e74b09ce83d177",
                "docker.io/valkey/valkey:8-bookworm@sha256:fec42f399876eb6faf9e008570597741c87ff7662a54185593e74b09ce83d177",
                ":",
                "Issue #947 - version@digest should use : delimiter",
            ),
            # Pure digest should use @ delimiter
            (
                "docker.io/library/alpine",
                "sha256:abc123def456abc123def456abc123def456abc123def456abc123def456abc1",
                "docker.io/library/alpine@sha256:abc123def456abc123def456abc123def456abc123def456abc123def456abc1",
                "@",
                "Pure digest should use @ delimiter",
            ),
            # Regular tag should use : delimiter
            (
                "docker.io/library/alpine",
                "3.19",
                "docker.io/library/alpine:3.19",
                ":",
                "Regular tag should use : delimiter",
            ),
            # Another version@digest combination
            (
                "quay.io/prometheus/prometheus",
                "v2.45.0@sha256:8d1dca1de3c9b6ba49e0e3a87e8e57c8fcb2e36e6f165f8969c0c9a48a80a9a2",
                "quay.io/prometheus/prometheus:v2.45.0@sha256:8d1dca1de3c9b6ba49e0e3a87e8e57c8fcb2e36e6f165f8969c0c9a48a80a9a2",
                ":",
                "Complex registry with version@digest should use : delimiter",
            ),
            # Edge case: tag starts with sha256 but is not pure digest
            (
                "docker.io/library/alpine",
                "sha256tag-v1.0",
                "docker.io/library/alpine:sha256tag-v1.0",
                ":",
                "Tag starting with sha256 but not pure digest should use : delimiter",
            ),
            # Default latest tag
            ("alpine", "latest", "alpine:latest", ":", "Default latest tag should use : delimiter"),
            # Registry with port
            (
                "localhost:5000/test/image",
                "v1.0@sha256:deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
                "localhost:5000/test/image:v1.0@sha256:deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
                ":",
                "Registry with port and version@digest should use : delimiter",
            ),
            # Pure short digest
            ("alpine", "sha256:abc123", "alpine@sha256:abc123", "@", "Short pure digest should use @ delimiter"),
        ],
    )
    def test_image_repository_delimiter_selection(self, name, tag, expected_full_name, expected_delimiter, description):
        """Test that ImageRepository selects the correct delimiter for different tag formats."""
        repo = ImageRepository(name, tag)

        assert (
            repo.full_name == expected_full_name
        ), f"{description}: Expected {expected_full_name}, got {repo.full_name}"
        assert (
            repo.delimiter == expected_delimiter
        ), f"{description}: Expected delimiter '{expected_delimiter}', got '{repo.delimiter}'"
        assert repo.name == name, f"Name should be preserved: Expected {name}, got {repo.name}"
        assert repo.tag == tag, f"Tag should be preserved: Expected {tag}, got {repo.tag}"

    def test_issue_947_specific_scenario(self):
        """Test the exact scenario reported in issue #947."""
        name = "docker.io/valkey/valkey"
        tag = "8-bookworm@sha256:fec42f399876eb6faf9e008570597741c87ff7662a54185593e74b09ce83d177"

        repo = ImageRepository(name, tag)

        # Before the fix, this would have been:
        # docker.io/valkey/valkey@8-bookworm@sha256:fec42f399876eb6faf9e008570597741c87ff7662a54185593e74b09ce83d177
        # After the fix, it should be:
        # docker.io/valkey/valkey:8-bookworm@sha256:fec42f399876eb6faf9e008570597741c87ff7662a54185593e74b09ce83d177

        expected = (
            "docker.io/valkey/valkey:8-bookworm@sha256:fec42f399876eb6faf9e008570597741c87ff7662a54185593e74b09ce83d177"
        )
        assert (
            repo.full_name == expected
        ), f"Issue #947 fix verification failed. Expected: {expected}, Got: {repo.full_name}"

    def test_repository_parsing(self):
        """Test that repository name parsing works correctly with various formats."""
        test_cases = [
            # (input_name, expected_name, expected_parsed_tag)
            ("alpine", "alpine", None),
            ("alpine:3.19", "alpine", "3.19"),
            ("alpine@sha256:abc123", "alpine", "sha256:abc123"),
            ("registry.io/alpine:latest", "registry.io/alpine", "latest"),
            ("localhost:5000/test:v1.0", "localhost:5000/test", "v1.0"),
        ]

        for input_name, expected_name, expected_parsed_tag in test_cases:
            repo = ImageRepository(input_name, "latest")  # default tag
            assert (
                repo.name == expected_name
            ), f"Name parsing failed for {input_name}: Expected {expected_name}, got {repo.name}"
            assert (
                repo.parsed_tag == expected_parsed_tag
            ), f"Tag parsing failed for {input_name}: Expected {expected_parsed_tag}, got {repo.parsed_tag}"

    def test_delimiter_logic_precision(self):
        """Test the precise logic for delimiter selection."""
        # Test cases that specifically target the delimiter selection logic
        test_cases = [
            # Tag that starts with sha256: should use @
            ("image", "sha256:abc123", "@"),
            # Tag that contains sha256 but doesn't start with sha256: should use :
            ("image", "v1.0-sha256-abc123", ":"),
            ("image", "release-sha256:abc123", ":"),
            ("image", "sha256suffix", ":"),
            # Version followed by digest should use :
            ("image", "1.0@sha256:abc123", ":"),
            ("image", "latest@sha256:abc123", ":"),
        ]

        for name, tag, expected_delimiter in test_cases:
            repo = ImageRepository(name, tag)
            assert (
                repo.delimiter == expected_delimiter
            ), f"Delimiter selection failed for tag '{tag}': Expected '{expected_delimiter}', got '{repo.delimiter}'"

    def test_original_name_preservation(self):
        """Test that original_name is always preserved."""
        test_cases = [
            "alpine",
            "alpine:3.19",
            "alpine@sha256:abc123",
            "registry.io/namespace/image:tag",
        ]

        for original in test_cases:
            repo = ImageRepository(original, "latest")
            assert (
                repo.original_name == original
            ), f"Original name not preserved: Expected {original}, got {repo.original_name}"
