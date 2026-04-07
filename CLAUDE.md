# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the `containers.podman` Ansible Collection — modules, plugins, and connection plugins for managing Podman containers. Published on [Ansible Galaxy](https://galaxy.ansible.com/containers/podman) from <https://github.com/containers/ansible-podman-collections>.

## Development Commands

### Testing

- **Run specific module integration tests**: `TEST2RUN=<module_name> ./ci/run_containers_tests.sh`
  - Example: `TEST2RUN=podman_container ./ci/run_containers_tests.sh`
  - Available tests correspond to playbooks in `ci/playbooks/containers/`
  - Runs with `-vv` first, retries with `-vvvvv` on failure for debugging

- **Run connection tests**: `./ci/run_connection_test.sh [podman|buildah]`
  - Use `ROOT=1` for root-privileged testing

- **Run sanity checks**: `bash contrib/ansible-lint.sh`
  - Builds collection to `/tmp`, installs it, runs `ansible-test sanity` in Docker
  - Max line length: 120 characters

- **Run unit tests**: `bash contrib/ansible-unit.sh`
  - Builds collection to `/tmp`, runs `ansible-test unit`
  - Can also run directly: `python -m pytest tests/unit/plugins/modules/`

- **Debug module execution**:
  - Check `podman_actions` in results to see actual podman commands executed
  - Use `check_mode: true` for dry-run testing without making changes

### Building and Packaging

- **Build collection**: `ansible-galaxy collection build`
- **Build RPM**: `make rpm`
- **Set version**: `python contrib/build.py <version>` — reads `galaxy.yml.in` template, adds version, writes `galaxy.yml`
- **Publish to Galaxy**: `bash contrib/publish.sh <version>` (use `DRYRUN=1` for testing)

## Code Architecture

### Module Pattern

All modules in `plugins/modules/` follow the pattern `podman_<resource>.py` (mutating) and `podman_<resource>_info.py` (read-only).

Every module file must contain three docstring constants at the top: `DOCUMENTATION` (YAML-formatted module docs with options, author, description), `RETURN` (return value documentation), and `EXAMPLES` (usage examples using full `containers.podman.<module>` namespace). These are required by `ansible-test sanity`.

Standard module structure:

1. `DOCUMENTATION`, `RETURN`, `EXAMPLES` docstring constants
2. Imports after docstrings (use `# noqa: E402` on post-docstring imports)
3. `main()` function creating `AnsibleModule` with `argument_spec`, `supports_check_mode=True`
4. Get executable path: `module.get_bin_path(module.params["executable"], required=True)`
5. Every module has an `executable` parameter (default: `"podman"`) for custom podman paths
6. Return results with `changed`, and typically `stdout`, `stderr`, or resource-specific data

### Module Utilities (`plugins/module_utils/podman/`)

- **`common.py`** — Core shared functions: `run_podman_command()`, `get_podman_version()`, `diff_generic()`, `createcommand()`, `generate_systemd()`, `lower_keys()`, `ARGUMENTS_OPTS_DICT` (long/short CLI arg mapping)
- **`podman_container_lib.py`** — The most complex module utility; see "Convention-Based Method Dispatch" below
- **`podman_pod_lib.py`** — Similar pattern to container lib for pod management
- **`podman_image_lib.py`** — `ImageRepository` (image name/tag/digest parsing and URL formation), `PodmanImageManager`, `PodmanImagePuller`, `PodmanImagePusher`
- **`quadlet.py`** — Systemd Quadlet integration for container/network/volume unit files

### Convention-Based Method Dispatch (Key Pattern)

The container and pod libraries use a **naming-convention-based dispatch** pattern that is critical to understand when adding or modifying parameters:

**`PodmanModuleParams`** — Converts module parameters to CLI arguments. For each parameter `foo`, define a method `addparam_foo(self, c)` that appends CLI flags to the command list `c` and returns it. The `construct_command_from_params()` method auto-discovers all `addparam_*` methods via reflection.

**`PodmanContainerDiff`** — Checks if a running container differs from desired state. For each parameter `foo`, define a method `diffparam_foo(self)` that compares the current container's state against the desired value. Returns `True` if different. The `is_different()` method auto-discovers all `diffparam_*` methods via reflection.

**Adding a new parameter to an existing module requires three changes:**

1. Add to `ARGUMENTS_SPEC_CONTAINER` (or equivalent) dict — defines the Ansible parameter type
2. Add `addparam_<name>` method to `PodmanModuleParams` — maps parameter to podman CLI flag
3. Add `diffparam_<name>` method to `PodmanContainerDiff` — implements idempotency check

For simple parameters, `diffparam_*` can delegate to `self._diff_generic("module_arg", "--cli-arg")` which uses `createcommand()` to extract the current value from podman inspect's `CreateCommand` output.

### Import Conventions

- Module files use **relative imports** for module_utils: `from ..module_utils.podman.common import run_podman_command`
- Module utility files (`plugins/module_utils/`) use **absolute imports** with full collection namespace: `from ansible_collections.containers.podman.plugins.module_utils.podman.common import lower_keys`
- All imports after the `DOCUMENTATION`/`RETURN`/`EXAMPLES` blocks need `# noqa: E402`

### Connection Plugins (`plugins/connection/`)

- `podman.py` — Execute commands inside Podman containers
- `buildah.py` — Execute commands inside Buildah containers

### Testing Architecture

- **Integration tests**: `tests/integration/targets/<module_name>/tasks/main.yml` — the primary test mechanism. Specific issue regression tests use `tasks/test_issue_<number>.yml` included from `main.yml`
- **Unit tests**: `tests/unit/plugins/modules/` — limited coverage, most testing is via integration tests
- **CI playbooks**: `ci/playbooks/containers/<module_name>.yml` — wrapper playbooks that include integration test tasks

### Build System

- `galaxy.yml.in` — source template (no version field)
- `contrib/build.py <version>` — generates `galaxy.yml` from template with version injected
- `Makefile` — RPM packaging target

## Adding CI for a New Module

When creating a new module, you need to set up four things for CI:

### 1. Integration test role

Create `tests/integration/targets/<module_name>/tasks/main.yml` with test tasks using `assert` to verify behavior. Organize regression tests as separate files (`test_issue_<number>.yml`) included from `main.yml`.

### 2. CI playbook

Create `ci/playbooks/containers/<module_name>.yml`:

```yaml
---
- hosts: all
  gather_facts: true
  tasks:
    - include_role:
        name: <module_name>
      vars:
        ansible_python_interpreter: "{{ _ansible_python_interpreter }}"
```

### 3. GitHub Actions workflow

Create `.github/workflows/<module_name>.yml` using the reusable template:

```yaml
name: Podman <module_name>

on:
  push:
    paths:
      - ".github/workflows/<module_name>.yml"
      - ".github/workflows/reusable-module-test.yml"
      - ci/playbooks/*.yml
      - "ci/run_containers_tests.sh"
      - "ci/playbooks/containers/<module_name>.yml"
      - "plugins/modules/<module_name>.py"
      - "tests/integration/targets/<module_name>/**"
    branches:
      - main
  pull_request:
    paths:
      - ".github/workflows/<module_name>.yml"
      - ".github/workflows/reusable-module-test.yml"
      - ci/playbooks/*.yml
      - "ci/run_containers_tests.sh"
      - "ci/playbooks/containers/<module_name>.yml"
      - "plugins/modules/<module_name>.py"
      - "tests/integration/targets/<module_name>/**"
  schedule:
    - cron: 7 0 * * *

jobs:
  test:
    uses: ./.github/workflows/reusable-module-test.yml
    with:
      module_name: "<module_name>"
      display_name: "Podman <module_name>"
```

The reusable template (`.github/workflows/reusable-module-test.yml`) also accepts optional inputs: `python_version`, `os_matrix` (JSON array), `ansible_versions` (JSON array), and `extra_collections` (space-separated list).

### 4. Module utilities (if needed)

If the module has complex state management, add a library in `plugins/module_utils/podman/` following the convention-based dispatch pattern described above.

## Integration Test Best Practices

- **Idempotency**: Resources may already exist. Assert like: `result.podman_actions | length == 0 or 'expected' in result.podman_actions[0]`
- **Dynamic digests**: Never hardcode SHA256 hashes. Pull a real image, extract digest with `podman_image_info`, use `{{ image_info.images[0].Digest }}`
- **Cleanup**: Use `always:` blocks to clean up test images/containers for reliability
- **Image URL delimiters**: Pure digests (`sha256:...`) use `@`, tags with digests use `:`
