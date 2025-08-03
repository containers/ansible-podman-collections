# Contributing to the Podman Ansible Collection

First off, thank you for considering contributing to this collection! We welcome any help, from reporting a bug to submitting a new feature. Every contribution is valuable.

This document provides guidelines to help you get started. Please read it carefully to ensure a smooth and effective contribution process.

## Code of Conduct

All contributors are expected to follow our [Code of Conduct](CODE-OF-CONDUCT.md). Please make sure you are familiar with its contents.

## How to Contribute

You can contribute in several ways:

* **Reporting Bugs:** If you find a bug, please [open an issue](https://github.com/containers/ansible-podman-collections/issues/new?assignees=&labels=bug&projects=&template=bug_report.yml) and provide as much detail as possible, including your Podman version, Ansible version, the playbook you are using, and the full error output.
* **Suggesting Enhancements:** If you have an idea for a new feature or an improvement to an existing one, please [open a feature request](https://github.com/containers/ansible-podman-collections/issues/new?assignees=&labels=enhancement&projects=&template=feature_request.yml).
* **Submitting Pull Requests:** If you want to fix a bug or add a feature yourself, please follow the guidelines below.

## Development Setup

1. **Fork and Clone:** Fork the repository on GitHub and clone your fork locally.

    ```bash
    git clone https://github.com/YOUR-USERNAME/ansible-podman-collections.git
    cd ansible-podman-collections
    ```

2. **Set up a Virtual Environment:** It's highly recommended to work in a Python virtual environment.

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install Dependencies:** The collection's testing dependencies are listed in `test-requirements.txt`.

    ```bash
    pip install -r test-requirements.txt
    ```

## Guidelines for Pull Requests

### General Workflow

1. Create a new branch for your changes: `git checkout -b my-feature-or-fix`.
2. Make your changes. Follow the coding and testing guidelines below.
3. Commit your changes with a clear and descriptive message. See existing commit messages for style (`git log --oneline`).
4. Push your branch to your fork: `git push origin my-feature-or-fix`.
5. Open a pull request against the `main` branch of the original repository.

### Fixing a Bug

1. If an issue for the bug doesn't already exist, please create one.
2. Ideally, add an integration test case to `tests/integration/targets/` that reproduces the bug and fails before your fix.
3. Implement the code change that fixes the bug.
4. Run the tests to ensure your fix works and doesn't break anything else.
5. In your PR description, use the "Fixes #123" syntax to link it to the issue.

### Adding a New Module

We have a script to help you scaffold a new module.

1. **Define Module Variables:** Copy `contrib/my_module_template_vars.yaml` and customize it with your new module's details (name, author, options, etc.).
2. **Generate the Module:** Run the `contrib/generate_module.sh` script. This will create a new module file in the `contrib` directory.
3. **Place the Module:** Move the generated file into `plugins/modules/`.
4. **Add Logic:** Implement the core logic for your module. If you need to share code with other modules, consider adding it to `plugins/module_utils/`.
5. **Document:** Ensure the `DOCUMENTATION`, `EXAMPLES`, and `RETURN` sections are thorough and accurate. This is critical for users.
6. **Add Tests:** Create a new integration test role and a new CI workflow for your module (see below).

## Testing Strategy

This collection uses three types of tests. All tests must pass before a PR can be merged.

### 1. Sanity Tests

These tests check for code style, syntax errors, and other common issues. Sanity tests must pass in pull requests in opder to merge.

* **How to Run:**

    ```bash
    bash contrib/ansible-lint.sh
    ```

* **Guidelines:**
  * This will install collection in `/tmp` directory and run `ansible-test` sanity in docker.
  * The maximum line length is 120 characters.

### 2. Unit Tests

Unit tests are for testing specific functions in isolation, often by mocking external dependencies. This is an area we are actively working to improve.

* **Location:** `tests/unit/plugins/modules/`
* **How to Run:**

    ```bash
    bash contrib/ansible-unit.sh
    ```

* **Guidelines:**
  * This will install collection in `/tmp` directory and run `ansible-test` unit tests.

### 3. Integration Tests

These are the most important tests in the collection. They run Ansible playbooks to test modules against a live Podman instance.

* **Location:** `tests/integration/targets/`
* **Structure:** Each subdirectory in `targets` is an Ansible role that tests a specific module or feature. The main logic is in `tasks/main.yml`.

* **Adding a New Integration Test:**
    1. Create a new directory (role) for your module: `tests/integration/targets/my_new_module/tasks`.
    2. Create a `main.yml` file inside that directory.
    3. Write Ansible tasks that execute your module and verify its behavior. Use the `assert` or `fail` modules to check for expected outcomes.

        ```yaml
        - name: Run my_new_module
          my_new_module:
            name: test_container
            state: present
          register: result

        - name: Assert that the container was created
          assert:
            that:
              - result.changed
              - result.container.State.Status == "running"
        ```

* **Running Locally:** You can run a specific test role using `ansible-playbook`. This requires a working Podman installation.
* Create a testing playbook with your tests like:

    ```yaml
    - hosts: all
      gather_facts: false
      tasks:

        - include_tasks: tests/integration/targets/my_new_module/tasks/main.yml

    ```

    Install the collection version you develop with:

    ```bash
    ansible-galaxy collection install -vvv --force .
    ```

    and then run the playbook it with:

    ```bash
    ansible-playbook -vv -i localhost, my_playbook.yml
    ```

## Continuous Integration (CI)

We use GitHub Actions to run all our tests automatically.

### Adding a CI Job for a New Module

To ensure your new module is tested on every PR, you must add a new workflow file. We use a reusable workflow to make this easy.

1. Go to the `.github/workflows/` directory.
2. Create a new file named after your module, e.g., `podman_my_new_module.yml`.
3. Copy the content from an existing module workflow, like `podman_export.yml`, and adapt it. You only need to change a few lines:

    ```yaml
    name: Podman my_new_module

    on:
      push:
        paths:
          - 'plugins/modules/podman_my_new_module.py'
          - 'tests/integration/targets/podman_my_new_module/**'
      pull_request:
        paths:
          - 'plugins/modules/podman_my_new_module.py'
          - 'tests/integration/targets/podman_my_new_module/**'

    jobs:
      test:
        uses: ./.github/workflows/reusable-module-test.yml
        with:
          module_name: podman_my_new_module  # The name of your test role
          display_name: "Podman my_new_module" # A friendly name for the job
    ```

4. Commit this new workflow file along with your module and test code.

## Final Checklist for Pull Requests

Before you submit your PR, please make sure you have:

* [ ] Read this `CONTRIBUTING.md` guide.
* [ ] Added or updated tests for your changes.
* [ ] Run `ansible-test sanity` and fixed any issues.
* [ ] Ensured all CI checks are passing on your PR.
* [ ] Updated the `DOCUMENTATION` block in the module if you changed any parameters.

Thank you for your contribution!
