# Working on containers.podman

Project docs: [README.md](README.md) (usage and requirements), [CONTRIBUTING.md](CONTRIBUTING.md) (setup, testing and contributions), [RELEASING.md](RELEASING.md) (releases), [SECURITY.md](SECURITY.md) (disclosure), [CODE-OF-CONDUCT.md](CODE-OF-CONDUCT.md), [connection plugin guide](docs/connection_plugins.md), [examples](playbooks/examples/README.md), and [CI recipes](contrib/README.md). This file records decisions and pitfalls those workflows do not make obvious.

## Fixing bugs and extending existing modules

- Prefer focused fixes: the collection is in maintenance mode. Preserve behavior on older Podman versions; guard new CLI flags using the existing version-check helpers.
- Container and pod arguments use convention-based dispatch: `construct_command_from_params()` and `is_different()` discover `addparam_*` and `diffparam_*` methods by name through reflection. For a new option, update the argument spec (`ARGUMENTS_SPEC_CONTAINER` / `ARGUMENTS_SPEC_POD`), add `addparam_<option>` to `PodmanModuleParams` / `PodmanPodModuleParams`, add the corresponding `diffparam_<option>` to `PodmanContainerDiff` / `PodmanPodDiff` where comparable, plus module documentation. Because dispatch is by name, nothing errors when a method is absent: an argument spec alone can accept an option that is silently omitted from the CLI command.
- Check `plugins/module_utils/podman/quadlet.py` when changing an option supported by `state=quadlet`; CLI handling and Quadlet generation are separate paths. Reuse `_diff_generic` for values represented in inspect's `CreateCommand`, checking whether Podman normalizes the value before comparing it.
- Preserve the module's `executable` parameter through every command path, including inspect, version checks and cleanup; avoid introducing hardcoded `podman` calls that bypass the selected binary.
- When adding CLI options with alternate spellings, check `ARGUMENTS_OPTS_DICT` in `plugins/module_utils/podman/common.py`. It maps short and long flags when reading `CreateCommand`; missing aliases can cause false differences and unnecessary resource recreation.
- For state-management fixes, exercise initial creation, an unchanged second run, and an actual configuration change. Check `changed`, diff output and check mode where supported. Inspect `podman_actions` to diagnose command construction; matching a command alone does not prove idempotency.
- Regression integration tasks must be included from the target's `tasks/main.yml` to run. Clean up resources in `always:` blocks so failed tests do not contaminate later runs.

## Testing the code you changed

- For local integration tests, build/install the current collection, then create a temporary playbook outside the working tree that includes the desired test role's tasks. Ensure Ansible selects the newly installed collection.
- Keep imports relative: modules use `..module_utils.podman`, utilities use `.common` or sibling imports. Test an isolated installation rather than patching an installed collection in place.
- Prefer `ansible-test units` from an installed collection directory over plain pytest; the harness supplies collection import handling. For integration tests, use `TEST2RUN=<target> ./ci/run_containers_tests.sh` after selecting the collection under test.
- Connection tests use `./ci/run_connection_test.sh podman` or `buildah`, not `TEST2RUN`. A nonempty `ROOT` enables sudo. For either advanced connection target, run `SUDO= ANSIBLECMD=$(command -v ansible-playbook) ./runme.sh` inside its directory. CI masks advanced-test failures with `|| echo`; inspect their output.
- The connection harness does not validate the `podman_unshare` become plugin. Add a focused playbook exercising privilege escalation when changing it; existing connection CI does not cover become-plugin changes.
- `contrib/ansible-unit.sh` and `contrib/ansible-lint.sh` share and wipe `/tmp/ansible-lint-*`; do not run them concurrently. Their Python versions can differ from CI: check the scripts and relevant workflow before diagnosing an environment failure.
- If default Ansible temporary paths are unwritable, set task-specific `ANSIBLE_LOCAL_TEMP`, `ANSIBLE_REMOTE_TEMP`, and `ANSIBLE_SSH_CONTROL_PATH_DIR` under `/tmp`.

Example `/tmp/test-local.yml`; replace `podman_volume` with the target you want to test:

```yaml
---
- name: Run volume integration tasks
  hosts: localhost
  connection: local
  gather_facts: true
  vars:
    ansible_python_interpreter: "{{ ansible_playbook_python }}"
  tasks:
    - name: Include the test role's tasks
      ansible.builtin.include_tasks: "{{ repo_dir }}/tests/integration/targets/podman_volume/tasks/main.yml"
```

Run it from the repository, after installing the collection under test:

```bash
ansible-playbook -i localhost, /tmp/test-local.yml -e repo_dir="$PWD" --diff -vv
```

Keeping the playbook outside the working tree matters: `build_ignore` does not exclude root-level `*.yml`, so a scratch playbook left in the repository root is packaged into the release artifact.

## Adding modules or changing shared code

- A new module needs an integration target, a wrapper in `ci/playbooks/containers/`, and a workflow using `.github/workflows/reusable-module-test.yml`. Adapt an existing module workflow rather than maintaining another template here.
- Include shared utilities in the affected workflows' path filters; otherwise utility-only changes may skip dependent module tests. Run the affected targets when changing shared command, diff or Quadlet logic.
- Inventory plugins use `.github/workflows/test-inventory-examples.yml`, including inventory unit tests; connection plugins use `.github/workflows/connections_tests.yml`. That workflow has no become-plugin path filter or explicit become-plugin test; add coverage for become-plugin changes rather than assuming connection tests cover them.
- Sanity ignore files are version-specific. Fix the underlying issue when possible; if an exception is necessary, scope it narrowly and check every applicable Ansible version.
- README compatibility requirements and `meta/runtime.yml` currently disagree. Treat a compatibility change as its own decision; do not reconcile them incidentally during another fix.

## Preparing and publishing releases

- Increase the major release version only when a new module or plugin has been added since the previous release; otherwise increase only the minor release version. In this repository's terminology, major means `1.Y.x` to `1.(Y+1).0`, and minor means `1.Y.Z` to `1.Y.(Z+1)`. New options, Podman compatibility updates and fixes to existing modules/plugins therefore receive only a minor bump. Verify additions against the previous release tag before choosing.
- Record user-facing changes in the combined `changelogs/changelog.yaml`; omit CI, test infrastructure and other maintenance-only changes. Include new modules/plugins in their respective sections. Generate `CHANGELOG.rst` with antsibull-changelog, then verify the version, release summary and release date remain correct.
- Rebuild HTML documentation for new module/plugin releases as specified in `RELEASING.md`. From the repository root, use `contrib/build_docs.sh "$PWD/docs"`: the script changes directory, so its output path must be absolute. Verify the documentation build reports success. It uses fixed `/tmp/docs_new_*` paths, so avoid simultaneous builds.
- Build release packages from a clean checkout or tracked-source staging directory. `ansible-galaxy collection build` can include unrelated untracked files unless excluded by `build_ignore`; inspect the artifact contents and version before delivery.
- Release preparation ends with a reviewable branch/PR. After merge, pushing the numeric version tag triggers Galaxy publication. `contrib/publish.sh` is also a publishing operation: `DRYRUN=1` still sends a publish request with a test key and suppresses failures. Use collection build for a local packaging check.

## Delivering changes

- Sign commits with `git commit -s` (DCO); omit AI co-author attribution.
