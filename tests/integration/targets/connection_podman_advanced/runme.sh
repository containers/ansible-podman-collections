#!/usr/bin/env bash

set -o pipefail
set -eux

# Enhanced Podman Connection Plugin Tests
# Tests for new features and configuration options

function run_ansible {
    ${SUDO:-} ${ANSIBLECMD:-ansible-playbook} test_advanced_features.yml -i "test_connection.inventory" \
        -e target_hosts="podman_advanced" \
        "$@"
}

function run_configuration_test {
    local config_name="$1"
    local extra_vars="$2"
    echo "Testing configuration: $config_name"

    ${SUDO:-} ${ANSIBLECMD:-ansible-playbook} test_advanced_features.yml -i "test_connection.inventory" \
        -e target_hosts="podman_advanced" \
        -e "$extra_vars" \
        "$@"
}

echo "=== Running Enhanced Podman Connection Tests ==="

# Create a container
${SUDO} podman run -d --name "podman-container" python:3.10-alpine sleep 1d

# Test 1: Basic functionality with new features
echo "Test 1: Basic advanced features"
run_ansible "$@"

# Test 2: Mount detection disabled
echo "Test 2: Mount detection disabled"
run_configuration_test "mount_disabled" "ansible_podman_mount_detection=false" "$@"

# Test 3: Different timeout settings
echo "Test 3: Short timeout"
run_configuration_test "short_timeout" "ansible_podman_timeout=5" "$@"

# Test 4: Different retry settings
echo "Test 4: More retries"
run_configuration_test "more_retries" "ansible_podman_retries=5" "$@"

# Test 5: Different user context
echo "Test 5: Root user context"
run_configuration_test "root_user" "ansible_user=root" "$@"

# Test 6: Custom environment variables
echo "Test 6: Custom environment variables"
run_configuration_test "custom_env" "ansible_podman_extra_env={'CUSTOM_TEST': 'value', 'DEBUG': 'true'}" "$@"

# Test 7: Verify plugin identification
echo "Test 7: Plugin identification verification"
ANSIBLE_VERBOSITY=4 run_ansible "$@" | tee check_log
${SUDO:-} grep -q "Using podman connection from collection" check_log
${SUDO:-} rm -f check_log

# Test 8: Error handling with invalid executable
echo "Test 8: Error handling test"
set +o pipefail
ANSIBLE_PODMAN_EXECUTABLE=fakepodman run_ansible "$@" 2>&1 | grep "Could not find fakepodman in PATH"
test_result=$?
set -o pipefail

if [ $test_result -eq 0 ]; then
    echo "Error handling test passed"
else
    echo "Error handling test failed - error message not found"
    exit 1
fi

# Test 9: Performance test with multiple operations
echo "Test 9: Performance test"
time run_ansible "$@" > /tmp/performance_test.log 2>&1
echo "Performance test completed - check /tmp/performance_test.log for timing"

echo "Test 10: Missing container exec"
${SUDO:-} ${ANSIBLECMD:-ansible-playbook} test_missing_container_exec.yml -i "test_connection.inventory"

echo "Test 11: Removed between exec"
${SUDO:-} ${ANSIBLECMD:-ansible-playbook} test_removed_between_exec.yml -i "test_connection.inventory"

echo "Test 12: Missing container put"
${SUDO:-} ${ANSIBLECMD:-ansible-playbook} test_missing_container_put.yml -i "test_connection.inventory"

echo "Test 13: Missing container fetch"
${SUDO:-} ${ANSIBLECMD:-ansible-playbook} test_missing_container_fetch.yml -i "test_connection.inventory"

echo "=== All Enhanced Podman Connection Tests Completed Successfully ==="
