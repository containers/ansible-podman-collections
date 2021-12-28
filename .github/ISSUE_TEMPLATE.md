<!--
---------------------------------------------------
BUG REPORT INFORMATION
---------------------------------------------------
Use the commands below to provide key information from your environment:
You do NOT have to include this information if this is a FEATURE REQUEST

Please update your version of Podman Ansible modules to the latest possible and
retry your command before creating an issue.
-->

**Is this a BUG REPORT or FEATURE REQUEST? (leave only one on its own line)**

/kind bug

/kind feature

**Description**

<!--
Briefly describe the problem you are having in a few paragraphs.
-->

**Steps to reproduce the issue:**

1.

2.

3.

**Describe the results you received:**


**Describe the results you expected:**


**Additional information you deem important (e.g. issue happens only occasionally):**


**Version of the `containers.podman` collection:**
**Either git commit if installed from git: `git show --summary`**
**Or version from `ansible-galaxy` if installed from galaxy: `ansible-galaxy collection list | grep containers.podman`**

```
(paste your output here)
```

**Output of `ansible --version`:**

```
(paste your output here)
```

**Output of `podman version`:**

```
(paste your output here)
```

**Output of `podman info --debug`:**

``` yaml
(paste your output here)
```

**Package info (e.g. output of `rpm -q podman` or `apt list podman`):**

```
(paste your output here)
```

**Playbok you run with ansible (e.g. content of `playbook.yaml`):**

``` yaml
(paste your output here)
```

**Command line and output of ansible run with high verbosity**

**Please NOTE: if you submit a bug about idempotency, run the playbook with `--diff` option, like:**

`ansible-playbook -i inventory --diff -vv playbook.yml`

```
(paste your output here)
```

**Additional environment details (AWS, VirtualBox, physical, etc.):**
