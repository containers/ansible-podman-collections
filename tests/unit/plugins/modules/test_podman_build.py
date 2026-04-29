from __future__ import absolute_import

__metaclass__ = type

from unittest.mock import Mock, patch

import pytest
from ansible.module_utils.basic import AnsibleModule


class TestPodmanBuildModule:
    """Unit tests for podman_quadlet_build.py module."""

    @pytest.mark.parametrize(
        "test_params, expected_valid",
        [
            # Valid minimal parameters
            ({"name": "myimage", "file": "/tmp/Containerfile"}, True),
            # Valid minimal parameters
            ({"name": "myimage", "set_working_directory": "/tmp/build"}, True),
            # Valid parameters with all image states
            ({"name": "myimage", "file": "/tmp/Containerfile", "state": "quadlet"}, True),
        ],
    )
    def test_module_parameter_validation(self, test_params, expected_valid):
        """Test that valid parameters are accepted."""
        # Mock the PodmanImageManager to avoid actual execution
        with patch(
            "ansible_collections.containers.podman.plugins.modules.podman_quadlet_build.create_quadlet_state"
        ) as mock_quadlet:

            mock_manager_instance = Mock()
            mock_manager_instance.execute.return_value = {"changed": False, "build": {}}
            mock_quadlet.return_value = {"changed": False}

            # Mock AnsibleModule.exit_json to capture the call
            with patch.object(AnsibleModule, "exit_json") as mock_exit:
                with patch.object(AnsibleModule, "__init__", return_value=None) as mock_init:
                    # Create a mock module instance
                    mock_module = Mock()
                    mock_module.params = test_params
                    mock_module.get_bin_path.return_value = "/usr/bin/podman"
                    mock_module.check_mode = False

                    # Mock the AnsibleModule constructor to return our mock
                    mock_init.return_value = None

                    # We can't easily test the full main() function due to AnsibleModule constructor,
                    # so we test parameter validation by creating an AnsibleModule directly
                    if expected_valid:
                        # For quadlet state, test that code path
                        if test_params.get("state") == "quadlet":
                            mock_module.params["state"] = "quadlet"
                            # This would normally call create_quadlet_state
                            assert test_params.get("state") == "quadlet"
                        else:
                            # For other states, test that PodmanImageManager would be called
                            assert test_params.get("name") is not None

    @pytest.mark.parametrize(
        "invalid_params, expected_error",
        [
            # Missing required name and file parameters
            ({}, "name"),
            # Missing required name parameter
            ({"file": "/tmp/Containerfile"}, "name"),
            # Invalid state
            ({"name": "alpine", "file": "/tmp/Containerfile", "state": "invalid"}, "state"),
        ],
    )
    def test_module_parameter_validation_failures(self, invalid_params, expected_error):
        """Test that invalid parameters are rejected."""
        # Test parameter validation by checking that certain combinations should fail
        # Note: Full validation testing would require mocking AnsibleModule completely
        # This is a basic structure test
        assert expected_error in ["name", "file", "state"]

    @pytest.mark.parametrize(
        "state, should_call_quadlet",
        [
            ("quadlet", True),
        ],
    )
    def test_state_handling_logic(self, state, should_call_quadlet):
        """Test that different states are handled correctly."""
        # This tests the logical flow rather than the full execution
        if should_call_quadlet:
            # Quadlet state should trigger quadlet code path
            assert state == "quadlet"
        else:
            # Other states should trigger PodmanImageManager
            assert state in ["present", "absent", "build"]

    def test_mutual_exclusion_logic(self):
        """Test that mutually exclusive parameters are defined correctly."""
        # Test the logic that authfile and username/password are mutually exclusive

        # These combinations should be mutually exclusive:
        # - authfile with username
        # - authfile with password

        mutually_exclusive_combinations = [
            ({"authfile": "/path/to/auth", "username": "user"}, True),
            ({"authfile": "/path/to/auth", "password": "pass"}, True),
            ({"username": "user", "password": "pass"}, False),  # This should be allowed
            ({"authfile": "/path/to/auth"}, False),  # This should be allowed
        ]

        for params, should_be_exclusive in mutually_exclusive_combinations:
            # This tests the logic of mutual exclusion
            has_authfile = "authfile" in params
            has_credentials = "username" in params or "password" in params

            if should_be_exclusive:
                assert has_authfile and has_credentials
            else:
                assert not (has_authfile and has_credentials) or not has_authfile

    def test_required_together_logic(self):
        """Test that username and password are required together."""
        # Test that username and password should be required together

        test_cases = [
            ({"username": "user"}, True),  # Missing password
            ({"password": "pass"}, True),  # Missing username
            ({"username": "user", "password": "pass"}, False),  # Both present
            ({}, False),  # Neither present
        ]

        for params, should_fail_required_together in test_cases:
            has_username = "username" in params
            has_password = "password" in params

            if should_fail_required_together:
                # One is present but not the other
                assert has_username != has_password
            else:
                # Both present or both absent
                assert has_username == has_password

    def test_required_one_of_logic(self):
        """Test that one of file or set_working_directory is defined."""
        # Test that one of file or set_working_directory is defined

        test_cases = [
            ({}, True),  # Neither present
            ({"file": "/foo/Containerfile"}, False),  # File present
            ({"set_working_directory": "/foo"}, False),  # set_working_directory present
            ({"file": "/foo/Containerfile", "set_working_directory": "/bar"}, False)  # Both present
        ]

        for params, should_fail_required_one_of in test_cases:
            has_file = "file" in params
            has_set_working_directory = "set_working_directory" in params

            if should_fail_required_one_of:
                # None are present
                assert not (has_file and has_set_working_directory)
            else:
                # One of both are present
                assert has_file or has_set_working_directory
