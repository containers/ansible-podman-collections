### Podman connection examples (with podman_containers inventory)

This folder shows practical playbooks that execute directly inside running Podman containers using the connection plugin `containers.podman.podman` and inventory plugin `containers.podman.podman_containers`.

How to use
1) Create a simple inventory source that discovers running containers:
   - See `inventory/podman_all.yml`
   - Adjust `label_selectors` or `name_patterns` if you want to target a subset

2) Run an example, e.g. basic exec:
```bash
ansible-playbook -i playbooks/examples/inventory/podman_all.yml playbooks/examples/podman_exec_basic.yml
```

Examples included
- `podman_exec_basic.yml` — Run common commands (uptime, os-release), demonstrate environment variables and idempotent checks
- `podman_copy_fetch.yml` — Copy files into a container and fetch them back (works with rootless or root)
- `podman_multiuser_tasks.yml` — Execute tasks as different users inside containers (root and non-root), with optional become
- `podman_pkg_manage.yml` — Install a package using apk/apt/yum depending on detected distro (no Python required)

Notes
- The inventory plugin assigns the connection automatically; no SSH is used
- To run as non-root, set `ansible_user` (e.g. `nobody` or a numeric UID) on hosts or in a task/role scope
- You can inject environment variables into exec using `ansible_podman_extra_env`

### Buildah connection playbook examples

This folder contains self-contained Ansible playbooks demonstrating how to build images with Buildah while executing steps inside a working container through the Buildah connection plugin (`ansible_connection: containers.podman.buildah`). Each example shows a realistic workflow and explains the options used.

Prerequisites
- Podman and Buildah installed (rootless supported)
- Ansible installed (`ansible-core` recommended)
- Network access to pull base images

How these playbooks work
- A working container is created on localhost using `buildah from <image>`.
- The playbook dynamically adds a temporary inventory host whose `ansible_connection` is `containers.podman.buildah` and `remote_addr` is the Buildah working container ID.
- File operations and commands within the container use the Buildah connection plugin (no SSH), so modules like `copy`, `command`, and `shell` act inside the container.
- Image metadata/commit/push operations are executed on localhost with `buildah config/commit/push` referencing the same container ID.

Common variables
- `buildah_base_image`: base image to start the working container (varies per example)
- `image_name`: final image name (and optional tag)
- `ansible_buildah_working_directory`: working directory inside the container for all build steps (passed to the connection plugin)

Examples
1) build_node_ai_api.yml — Node.js AI prediction API image without a Dockerfile
   - Starts from `node:14`, copies `package.json` and app sources to `/app`, runs `npm install`, sets image metadata, commits to `my-ai-node-app:latest`.
   - Options highlighted:
     - `ansible_connection: containers.podman.buildah`
     - `ansible_buildah_working_directory: /app`

2) build_go_ai_multistage.yml — Multi-stage Go build to a minimal runtime image
   - Stage 1: compile inside `golang:1.21` working container, fetch the compiled binary to host.
   - Stage 2: start `alpine:latest`, copy binary into the container, configure CMD and exposed port, commit `minimal-ai-inference:latest`.
   - Shows how to move artifacts between stages using the connection plugin’s `fetch_file` and normal `copy`.

3) build_ai_env_with_ansible.yml — Create a consistent AI dev environment image with an Ansible role
   - Starts from `python:3.11-slim`, then applies role `roles/ai-dev-env` which installs common data-science packages inside the container using raw/pip commands.
   - Demonstrates layering higher-level Ansible logic on top of a Buildah working container.

4) gitlab_ci_build_model_image.yml — CI-friendly image build using Buildah connection (template)
   - Builds and optionally pushes an image for a simple model serving app (`app.py`, `requirements.txt`).
   - Designed to be called from GitLab CI; see the included `.gitlab-ci.yml` for a minimal job that runs `ansible-playbook`.

Running an example
```bash
cd playbook/examples
ansible-playbook build_node_ai_api.yml -e image_name=my-ai-node-app:latest
```

Notes
- The Buildah connection runs commands with `buildah run <container> …` under the hood; metadata operations such as `buildah config`, `commit`, and `push` still run on localhost and reference the working container ID.
- If you prefer persistent names, set `container_name` (Buildah will use named working containers). Otherwise, the container ID returned by `buildah from` is used.


