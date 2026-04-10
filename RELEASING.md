# Releasing a New Version

This document describes how to release a new version of the `containers.podman` collection.

## Step 1: Update the Changelog

Add a new section for the release tag in `changelogs/changelog.yaml`. Include all user-facing changes since the previous release — bugfixes, new features, new modules, breaking changes, etc. **Skip maintenance-only changes** like CI improvements, test infrastructure updates, or internal refactoring that don't affect users.

Each release entry follows this format:

```yaml
  X.Y.Z:
    changes:
      release_summary: Short summary of the release
      bugfixes:
        - podman_container - Description of the fix
      minor_changes:
        - podman_image - Description of the change
      major_changes:
        - Description of major change
    # Include 'modules' section only when new modules are added:
    modules:
      - description: What the module does
        name: module_name
        namespace: ''
    # Include 'plugins' section only when new plugins are added
    release_date: 'YYYY-MM-DD'
```

Valid change categories: `release_summary`, `major_changes`, `minor_changes`, `breaking_changes`, `deprecated_features`, `removed_features`, `security_fixes`, `bugfixes`, `known_issues`.

## Step 2: Update the Version in galaxy.yml

Set the new version:

```bash
python contrib/build.py X.Y.Z
```

This reads `galaxy.yml.in` and writes `galaxy.yml` with the version injected.

## Step 3: Generate the CHANGELOG

Run:

```bash
antsibull-changelog release
```

This reads `changelogs/changelog.yaml` and regenerates `CHANGELOG.rst`.

## Step 4: Update Documentation (Major Releases Only)

For major releases (e.g., 1.18.0 -> 1.19.0), regenerate the documentation:

1. If new modules were added, `git add` their generated doc files first.
2. Run:

    ```bash
    contrib/build_docs.sh [output_dir]
    ```

    The default output directory is `$HOME/podman-docs`. The script builds the collection, installs it to a temp path, and runs `antsibull-docs` + Sphinx to generate HTML docs.

Skip this step for patch/minor releases (e.g., 1.19.0 -> 1.19.1).

## Step 5: Create a PR

Create a branch with the changelog, galaxy.yml, and CHANGELOG.rst changes (plus docs if applicable), then open a PR:

```bash
git checkout -b release-X.Y.Z
git add changelogs/changelog.yaml galaxy.yml CHANGELOG.rst
git commit -m "Release X.Y.Z"
git push origin release-X.Y.Z
```

## Step 6: Tag and Publish

After the PR is merged to `main`, tag the merge commit with the release version:

```bash
git tag X.Y.Z
git push origin X.Y.Z
```

The tag push triggers the `collection-publish.yml` GitHub Actions workflow, which automatically builds and publishes the collection to [Ansible Galaxy](https://galaxy.ansible.com/containers/podman). The tag must match the pattern `[0-9]+.[0-9]+.[0-9]+`.
