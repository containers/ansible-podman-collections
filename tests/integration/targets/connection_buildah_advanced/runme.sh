#!/usr/bin/env bash

set -o pipefail
set -eux

# Enhanced Buildah Connection Plugin Tests
# Tests for new features and configuration options

# New requirement from ansible-core 2.14
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8

# Buildah storage configuration for compatibility
export STORAGE_OPTS="overlay.mount_program=/usr/bin/fuse-overlayfs"

function run_ansible {
    ${SUDO:-} ${ANSIBLECMD:-ansible-playbook} test_buildah_features.yml -i "test_connection.inventory" \
        -e target_hosts="buildah_advanced" \
        "$@"
}

function run_configuration_test {
    local config_name="$1"
    local extra_vars="$2"
    echo "Testing configuration: $config_name"

    ${SUDO:-} ${ANSIBLECMD:-ansible-playbook} test_buildah_features.yml -i "test_connection.inventory" \
        -e target_hosts="buildah_advanced" \
        -e "$extra_vars" \
        "$@"
}

echo "=== Running Enhanced Buildah Connection Tests ==="

# Create a container
${SUDO:-} buildah from --name=buildah-container python:3.10-alpine

# Test 1: Basic functionality with new features
echo "Test 1: Basic advanced features"
run_ansible "$@"

# Test 2: Mount detection disabled
echo "Test 2: Mount detection disabled"
run_configuration_test "mount_disabled" "ansible_buildah_mount_detection=false" "$@"

# Test 3: Different timeout settings
echo "Test 3: Short timeout"
run_configuration_test "short_timeout" "ansible_buildah_timeout=5" "$@"

# Test 4: Different retry settings
echo "Test 4: More retries"
run_configuration_test "more_retries" "ansible_buildah_retries=5" "$@"

# Test 5: Custom working directory
echo "Test 5: Custom working directory"
run_configuration_test "custom_workdir" "ansible_buildah_working_directory=/home" "$@"

# Test 6: Auto-commit enabled
echo "Test 6: Auto-commit enabled"
run_configuration_test "auto_commit" "ansible_buildah_auto_commit=true" "$@"

# Test 7: Custom environment variables
echo "Test 7: Custom environment variables"
run_configuration_test "custom_env" "ansible_buildah_extra_env={'CUSTOM_BUILD': 'value', 'DEBUG': 'true'}" "$@"

# Test 8: Verify plugin identification
echo "Test 8: Plugin identification verification"
ANSIBLE_VERBOSITY=4 run_ansible "$@" | tee check_log
${SUDO:-} grep -q "Using buildah connection from collection" check_log
${SUDO:-} rm -f check_log

# Test 9: Error handling with invalid executable
echo "Test 9: Error handling test"
set +o pipefail
ANSIBLE_BUILDAH_EXECUTABLE=fakebuildah run_ansible "$@" 2>&1 | grep "Could not find fakebuildah in PATH"
test_result=$?
set -o pipefail

if [ $test_result -eq 0 ]; then
    echo "Error handling test passed"
else
    echo "Error handling test failed - error message not found"
    exit 1
fi

# Test 10: Performance test with multiple operations
echo "Test 10: Performance test"
time run_ansible "$@" > /tmp/buildah_performance_test.log 2>&1
echo "Performance test completed - check /tmp/buildah_performance_test.log for timing"

echo "=== All Enhanced Buildah Connection Tests Completed Successfully ==="
