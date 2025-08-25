# Podman and Buildah Connection Plugins

This document provides comprehensive information about the Podman and Buildah connection plugins included in the `containers.podman` Ansible collection.

## Table of Contents

1. [Overview](#overview)
2. [Installation and Setup](#installation-and-setup)
3. [Podman Connection Plugin](#podman-connection-plugin)
4. [Buildah Connection Plugin](#buildah-connection-plugin)
5. [Configuration Options](#configuration-options)
6. [Simple Usage Examples](#simple-usage-examples)
7. [Advanced Usage Examples](#advanced-usage-examples)
8. [Performance and Best Practices](#performance-and-best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Migration from Legacy Plugins](#migration-from-legacy-plugins)

## Overview

The connection plugins enable Ansible to execute tasks directly inside Podman containers and Buildah working containers. These plugins provide a seamless way to manage containerized environments using standard Ansible playbooks and tasks.

### Key Features

- **Direct container execution**: Run Ansible tasks inside containers without SSH
- **Fail-fast error handling**: No implicit retries; commands return rc/stdout/stderr to Ansible
- **Performance optimization**: Connection caching and mount detection for efficient file operations
- **Environment management**: Inject environment variables and configure container runtime
- **Unicode and special character support**: Handle complex file paths and command arguments
- **Privilege escalation**: Support for sudo and other privilege escalation methods
- **Timeout configuration**: Optional command timeout (default 0 = no timeout)

### Use Cases

- **Application deployment**: Deploy applications directly into containers
- **Container configuration**: Configure running containers with Ansible tasks
- **Multi-container orchestration**: Manage complex containerized applications
- **Development environments**: Set up and configure development containers
- **Testing and CI/CD**: Run tests and build processes inside containers
- **Container image customization**: Modify and configure container images using Buildah

## Installation and Setup

### Prerequisites

- Ansible 2.9 or later
- Podman 3.0+ (for Podman connection plugin)
- Buildah 1.20+ (for Buildah connection plugin)
- Python 3.6+ on the Ansible control node

### Installation

```bash
# Install from Ansible Galaxy
ansible-galaxy collection install containers.podman

# Or install from source
git clone https://github.com/containers/ansible-podman-collections.git
cd ansible-podman-collections
ansible-galaxy collection build
ansible-galaxy collection install containers-podman-*.tar.gz
```

## Podman Connection Plugin

The Podman connection plugin (`containers.podman.podman`) allows Ansible to execute tasks inside running Podman containers.

### Podman Connection Plugin Features

- **Container lifecycle management**: Automatically detect and connect to running containers
- **Mount point detection**: Optimize file transfers by detecting shared mounts
- **Environment variable injection**: Pass environment variables from inventory to container
- **Connection caching**: Cache container information for improved performance
- **Multiple execution modes**: Support for different container runtime configurations

### Podman Connection Plugin Basic Configuration

```yaml
# inventory.yml
[containers]
my-container

[containers:vars]
ansible_connection=containers.podman.podman
ansible_host=my-container-name
```

## Buildah Connection Plugin

The Buildah connection plugin (`containers.podman.buildah`) enables Ansible to execute tasks inside Buildah working containers, perfect for container image building and customization.

### Buildah Connection Plugin Features

- **Working container management**: Execute tasks in Buildah working containers
- **Auto-commit functionality**: Optionally commit changes after task execution
- **Working directory support**: Set and manage working directories
- **Layer optimization**: Efficient layer creation during image building
- **Build context management**: Handle build contexts and file transfers

### Buildah Connection Plugin Basic Configuration

```yaml
# inventory.yml
[buildah_containers]
build-container

[buildah_containers:vars]
ansible_connection=containers.podman.buildah
ansible_host=build-container-name
```

## Configuration Options

### Podman Connection Plugin Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `ansible_podman_executable` | string | `podman` | Path to podman executable |
| `ansible_podman_timeout` | int | `0` | Command execution timeout in seconds (0 = no timeout) |
| `ansible_podman_extra_env` | dict | `{}` | Additional environment variables to inject |
| `ansible_podman_mount_detection` | bool | `true` | Enable mount point detection for file operations |
| `ansible_podman_ignore_mount_errors` | bool | `true` | Continue without mount if detection fails |

### Buildah Connection Plugin Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `ansible_buildah_executable` | string | `buildah` | Path to buildah executable |
| `ansible_buildah_timeout` | int | `0` | Command execution timeout in seconds (0 = no timeout) |
| `ansible_buildah_extra_env` | dict | `{}` | Additional environment variables to inject |
| `ansible_buildah_mount_detection` | bool | `true` | Enable mount point detection for file operations |
| `ansible_buildah_ignore_mount_errors` | bool | `true` | Continue without mount if detection fails |
| `ansible_buildah_auto_commit` | bool | `false` | Automatically commit changes after tasks |
| `ansible_buildah_working_directory` | string |  | Working directory for command execution |

## Simple Usage Examples

Note: Modules like `package`, `file`, and `copy` require Python inside the target container. For minimal images without Python, prefer `raw`/`command` tasks or delegate host-side operations (for example, `podman cp`). Examples below assume Python is available unless stated otherwise.
### Example 1: Basic Container Management

```yaml
---
- name: Configure web server in container
  hosts: webserver_container
  vars:
    ansible_connection: containers.podman.podman
    ansible_host: nginx-container

  tasks:
    - name: Install additional packages
      package:
        name: curl
        state: present

    - name: Create configuration directory
      file:
        path: /etc/nginx/conf.d
        state: directory
        mode: '0755'

    - name: Copy nginx configuration
      copy:
        src: nginx.conf
        dest: /etc/nginx/conf.d/default.conf
        mode: '0644'
      notify: restart nginx

  handlers:
    - name: restart nginx
      service:
        name: nginx
        state: restarted
```

### Example 2: Multi-Container Application

```yaml
---
- name: Deploy multi-tier application
  hosts: localhost
  gather_facts: false

  tasks:
    - name: Start database container
      containers.podman.podman_container:
        name: app-database
        image: postgres:13
        state: started
        env:
          POSTGRES_DB: myapp
          POSTGRES_USER: appuser
          POSTGRES_PASSWORD: secret
        ports:
          - "5432:5432"

    - name: Start application container
      containers.podman.podman_container:
        name: app-server
        image: python:3.9
        state: started
        command: sleep infinity
        ports:
          - "8080:8080"

- name: Configure database
  hosts: app-database
  vars:
    ansible_connection: containers.podman.podman
    ansible_host: app-database

  tasks:
    - name: Create application database
      postgresql_db:
        name: myapp
        state: present

- name: Configure application
  hosts: app-server
  vars:
    ansible_connection: containers.podman.podman
    ansible_host: app-server

  tasks:
    - name: Install application dependencies
      pip:
        requirements: /app/requirements.txt

    - name: Start application service
      shell: |
        cd /app
        python app.py
      async: 3600
      poll: 0
```

### Example 3: Simple Image Building with Buildah

```yaml
---
- name: Build custom image with Buildah
  hosts: localhost
  gather_facts: false

  tasks:
    - name: Create working container
      shell: buildah from --name custom-build alpine:latest

- name: Configure the image
  hosts: custom-build
  vars:
    ansible_connection: containers.podman.buildah
    ansible_host: custom-build
    ansible_buildah_auto_commit: true

  tasks:
    - name: Update package index
      apk:
        update_cache: true

    - name: Install required packages
      apk:
        name:
          - python3
          - py3-pip
          - curl
        state: present

    - name: Create application user
      user:
        name: appuser
        shell: /bin/sh
        home: /app
        create_home: true

    - name: Set working directory
      file:
        path: /app
        state: directory
        owner: appuser
        group: appuser

- name: Commit custom image with Buildah
  hosts: localhost
  gather_facts: false

  tasks:
    - name: Commit the image
      shell: buildah commit custom-build custom-alpine:latest

    - name: Clean up working container
      shell: buildah rm custom-build
```

## Advanced Usage Examples

### Example 1: High-Performance Web Application Deployment

```yaml
---
- name: Deploy high-performance web application
  hosts: localhost
  gather_facts: false
  vars:
    app_replicas: 3
    load_balancer_image: "nginx:alpine"
    app_image: "python:3.9-slim"

  tasks:
    - name: Create application network
      containers.podman.podman_network:
        name: app-network
        state: present

    - name: Start application containers
      containers.podman.podman_container:
        name: "app-{{ item }}"
        image: "{{ app_image }}"
        state: started
        command: sleep infinity
        networks:
          - name: app-network
        env:
          FLASK_ENV: production
          WORKERS: "4"
          PORT: "5000"
        healthcheck:
          test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
          interval: 30s
          timeout: 10s
          retries: 3
      loop: "{{ range(1, app_replicas + 1) | list }}"

    - name: Start load balancer
      containers.podman.podman_container:
        name: load-balancer
        image: "{{ load_balancer_image }}"
        state: started
        ports:
          - "80:80"
          - "443:443"
        networks:
          - name: app-network
        volumes:
          - nginx-config:/etc/nginx/conf.d:ro
          - ssl-certs:/etc/ssl/certs:ro

- name: Configure application containers
  hosts: app_containers
  vars:
    ansible_connection: containers.podman.podman
    ansible_podman_extra_env:
      PYTHONPATH: "/app"
      LOG_LEVEL: "INFO"
    ansible_podman_timeout: 60

  tasks:
    - name: Install system dependencies
      apt:
        name:
          - build-essential
          - python3-dev
          - libpq-dev
        state: present
        update_cache: true

    - name: Create application directory structure
      file:
        path: "{{ item }}"
        state: directory
        mode: '0755'
      loop:
        - /app
        - /app/logs
        - /app/static
        - /app/templates

    - name: Copy application code
      copy:
        src: "{{ item.src }}"
        dest: "{{ item.dest }}"
        mode: "{{ item.mode | default('0644') }}"
      loop:
        - { src: "app.py", dest: "/app/app.py", mode: "0755" }
        - { src: "requirements.txt", dest: "/app/requirements.txt" }
        - { src: "config.py", dest: "/app/config.py" }
        - { src: "wsgi.py", dest: "/app/wsgi.py" }
      notify: restart application

    - name: Install Python dependencies
      pip:
        requirements: /app/requirements.txt
        virtualenv: /app/venv
        virtualenv_python: python3

    - name: Configure application settings
      template:
        src: app_config.j2
        dest: /app/.env
        mode: '0600'
      notify: restart application

    - name: Set up log rotation
      copy:
        content: |
          /app/logs/*.log {
              daily
              missingok
              rotate 30
              compress
              delaycompress
              notifempty
              copytruncate
          }
        dest: /etc/logrotate.d/app
        mode: '0644'

    - name: Start application with gunicorn
      shell: |
        cd /app
        source venv/bin/activate
        gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:app
      async: 3600
      poll: 0
      register: app_service

  handlers:
    - name: restart application
      shell: pkill -f gunicorn || true

- name: Configure load balancer
  hosts: load-balancer
  vars:
    ansible_connection: containers.podman.podman
    ansible_podman_timeout: 30

  tasks:
    - name: Generate nginx upstream configuration
      template:
        src: nginx_upstream.conf.j2
        dest: /etc/nginx/conf.d/upstream.conf
        mode: '0644'
      notify: reload nginx

    - name: Configure SSL certificates
      copy:
        src: "{{ item.src }}"
        dest: "{{ item.dest }}"
        mode: '0600'
      loop:
        - { src: "ssl/app.crt", dest: "/etc/ssl/certs/app.crt" }
        - { src: "ssl/app.key", dest: "/etc/ssl/private/app.key" }
      notify: reload nginx

    - name: Configure nginx main site
      template:
        src: nginx_site.conf.j2
        dest: /etc/nginx/conf.d/default.conf
        mode: '0644'
      notify: reload nginx

  handlers:
    - name: reload nginx
      service:
        name: nginx
        state: reloaded
```

### Example 2: Advanced Image Building Pipeline

```yaml
---
- name: Advanced container image building pipeline
  hosts: localhost
  gather_facts: false
  vars:
    base_image: "alpine:3.18"
    build_args:
      VERSION: "1.0.0"
      BUILD_DATE: "{{ ansible_date_time.iso8601 }}"
      COMMIT_SHA: "{{ lookup('env', 'GITHUB_SHA') | default('local') }}"

  tasks:
    - name: Create build context directory
      file:
        path: "{{ item }}"
        state: directory
        mode: '0755'
      loop:
        - /tmp/build-context
        - /tmp/build-context/src
        - /tmp/build-context/config
        - /tmp/build-context/scripts

    - name: Copy build files
      copy:
        src: "{{ item.src }}"
        dest: "{{ item.dest }}"
        mode: "{{ item.mode | default('0644') }}"
      loop:
        - { src: "src/", dest: "/tmp/build-context/src/", mode: "0755" }
        - { src: "config/", dest: "/tmp/build-context/config/" }
        - { src: "scripts/", dest: "/tmp/build-context/scripts/", mode: "0755" }
        - { src: "requirements.txt", dest: "/tmp/build-context/" }
        - { src: "Dockerfile", dest: "/tmp/build-context/" }

    - name: Create multi-stage build containers
      shell: |
        buildah from --name build-stage {{ base_image }}
        buildah from --name runtime-stage {{ base_image }}
      register: build_containers

    - name: Mount build context
      shell: |
        buildah copy build-stage /tmp/build-context /build
        buildah config --workingdir /build build-stage

- name: Configure build stage
  hosts: build-stage
  vars:
    ansible_connection: containers.podman.buildah
    ansible_host: build-stage
    ansible_buildah_working_dir: /build
    ansible_buildah_extra_env:
      BUILD_MODE: "production"
      PYTHONPATH: "/build/src"
    ansible_buildah_timeout: 300

  tasks:
    - name: Install build dependencies
      apk:
        name:
          - python3
          - py3-pip
          - python3-dev
          - gcc
          - musl-dev
          - libffi-dev
          - openssl-dev
          - make
          - git
        state: present
        update_cache: true

    - name: Create virtual environment
      shell: python3 -m venv /build/venv

    - name: Upgrade pip and install build tools
      pip:
        name:
          - pip
          - wheel
          - setuptools
        state: latest
        virtualenv: /build/venv

    - name: Install Python dependencies
      pip:
        requirements: /build/requirements.txt
        virtualenv: /build/venv

    - name: Compile application
      shell: |
        source /build/venv/bin/activate
        python setup.py build_ext --inplace
        python -m compileall src/
      args:
        chdir: /build

    - name: Run tests
      shell: |
        source /build/venv/bin/activate
        python -m pytest tests/ -v
      args:
        chdir: /build

    - name: Create distribution package
      shell: |
        source /build/venv/bin/activate
        python setup.py sdist bdist_wheel
      args:
        chdir: /build

    - name: Prepare runtime artifacts
      shell: |
        mkdir -p /build/runtime-artifacts
        cp -r src/ /build/runtime-artifacts/
        cp -r venv/ /build/runtime-artifacts/
        cp requirements.txt /build/runtime-artifacts/
        cp scripts/entrypoint.sh /build/runtime-artifacts/
      args:
        chdir: /build

- name: Configure runtime stage
  hosts: runtime-stage
  vars:
    ansible_connection: containers.podman.buildah
    ansible_host: runtime-stage
    ansible_buildah_working_dir: /app
    ansible_buildah_extra_env:
      PYTHONPATH: "/app/src"
      FLASK_ENV: "production"
    ansible_buildah_auto_commit: false

  tasks:
    - name: Install runtime dependencies only
      apk:
        name:
          - python3
          - py3-pip
          - curl
          - ca-certificates
        state: present
        update_cache: true

    - name: Create application user
      user:
        name: appuser
        shell: /bin/sh
        home: /app
        create_home: true
        system: true

    - name: Create application directories
      file:
        path: "{{ item }}"
        state: directory
        owner: appuser
        group: appuser
        mode: '0755'
      loop:
        - /app
        - /app/logs
        - /app/data
        - /app/tmp

    - name: Copy runtime artifacts from build stage
      shell: |
        buildah copy --from build-stage runtime-stage /build/runtime-artifacts /app

    - name: Set proper ownership
      file:
        path: /app
        owner: appuser
        group: appuser
        recurse: true

    - name: Configure entrypoint
      shell: |
        buildah config --user appuser runtime-stage
        buildah config --workingdir /app runtime-stage
        buildah config --entrypoint '["./entrypoint.sh"]' runtime-stage
        buildah config --cmd '["python", "src/app.py"]' runtime-stage

    - name: Set labels
      shell: |
        buildah config --label version="{{ build_args.VERSION }}" runtime-stage
        buildah config --label build-date="{{ build_args.BUILD_DATE }}" runtime-stage
        buildah config --label commit-sha="{{ build_args.COMMIT_SHA }}" runtime-stage
        buildah config --label maintainer="DevOps Team" runtime-stage

    - name: Configure health check
      shell: |
        buildah config --healthcheck 'CMD curl -f http://localhost:5000/health || exit 1' runtime-stage
        buildah config --healthcheck-interval 30s runtime-stage
        buildah config --healthcheck-timeout 10s runtime-stage
        buildah config --healthcheck-retries 3 runtime-stage

- name: Finalize and tag image
  hosts: localhost
  gather_facts: false

  tasks:
    - name: Commit final image
      shell: |
        buildah commit runtime-stage myapp:{{ build_args.VERSION }}
        buildah commit runtime-stage myapp:latest

    - name: Tag for registry
      shell: |
        buildah tag myapp:{{ build_args.VERSION }} registry.example.com/myapp:{{ build_args.VERSION }}
        buildah tag myapp:latest registry.example.com/myapp:latest
      when: lookup('env', 'REGISTRY_PUSH') == 'true'

    - name: Push to registry
      shell: |
        buildah push registry.example.com/myapp:{{ build_args.VERSION }}
        buildah push registry.example.com/myapp:latest
      when: lookup('env', 'REGISTRY_PUSH') == 'true'

    - name: Clean up build containers
      shell: |
        buildah rm build-stage runtime-stage

    - name: Clean up build context
      file:
        path: /tmp/build-context
        state: absent

    - name: Display image information
      shell: podman inspect myapp:{{ build_args.VERSION }}
      register: image_info

    - name: Show build summary
      debug:
        msg: |
          Build completed successfully!
          Image: myapp:{{ build_args.VERSION }}
          Size: {{ (image_info.stdout | from_json)[0].Size | human_readable }}
          Created: {{ (image_info.stdout | from_json)[0].Created }}
          Labels: {{ (image_info.stdout | from_json)[0].Config.Labels }}
```

### Example 3: Container Development Environment

```yaml
---
- name: Set up development environment
  hosts: localhost
  gather_facts: false
  vars:
    dev_containers:
      - name: dev-database
        image: postgres:13
        ports: ["5432:5432"]
        env:
          POSTGRES_DB: devdb
          POSTGRES_USER: developer
          POSTGRES_PASSWORD: devpass
      - name: dev-redis
        image: redis:alpine
        ports: ["6379:6379"]
      - name: dev-workspace
        image: ubuntu:22.04
        command: sleep infinity
        ports: ["8080:8080", "3000:3000"]
        volumes:
          - "${PWD}:/workspace"

  tasks:
    - name: Create development network
      containers.podman.podman_network:
        name: dev-network
        state: present

    - name: Start development containers
      containers.podman.podman_container:
        name: "{{ item.name }}"
        image: "{{ item.image }}"
        state: started
        command: "{{ item.command | default(omit) }}"
        ports: "{{ item.ports | default([]) }}"
        env: "{{ item.env | default({}) }}"
        volumes: "{{ item.volumes | default([]) }}"
        networks:
          - name: dev-network
      loop: "{{ dev_containers }}"

- name: Configure development workspace
  hosts: dev-workspace
  vars:
    ansible_connection: containers.podman.podman
    ansible_host: dev-workspace
    ansible_podman_extra_env:
      TERM: "xterm-256color"
      EDITOR: "vim"
    ansible_podman_timeout: 120

  tasks:
    - name: Update package cache
      apt:
        update_cache: true

    - name: Install development tools
      apt:
        name:
          - curl
          - wget
          - git
          - vim
          - tmux
          - zsh
          - python3
          - python3-pip
          - nodejs
          - npm
          - build-essential
          - postgresql-client
          - redis-tools
        state: present

    - name: Install Python development packages
      pip:
        name:
          - ipython
          - jupyter
          - black
          - flake8
          - pytest
          - requests
          - sqlalchemy
          - redis
        state: present

    - name: Configure Git
      git_config:
        name: "{{ item.name }}"
        value: "{{ item.value }}"
        scope: global
      loop:
        - { name: "user.name", value: "Developer" }
        - { name: "user.email", value: "dev@example.com" }
        - { name: "init.defaultBranch", value: "main" }

    - name: Set up shell environment
      copy:
        content: |
          export PATH=$PATH:/workspace/bin
          export PYTHONPATH=/workspace/src
          export DATABASE_URL=postgresql://developer:devpass@dev-database:5432/devdb
          export REDIS_URL=redis://dev-redis:6379/0

          alias ll='ls -la'
          alias ..='cd ..'
          alias gs='git status'
          alias gd='git diff'
          alias gc='git commit'
          alias gp='git push'

          # Auto-activate virtual environment if it exists
          if [ -d "/workspace/venv" ]; then
              source /workspace/venv/bin/activate
          fi
        dest: /root/.bashrc
        mode: '0644'

    - name: Create workspace directories
      file:
        path: "{{ item }}"
        state: directory
        mode: '0755'
      loop:
        - /workspace/src
        - /workspace/tests
        - /workspace/docs
        - /workspace/bin
        - /workspace/config

    - name: Install oh-my-zsh
      shell: |
        sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" || true
        chsh -s $(which zsh)
      ignore_errors: true

    - name: Start Jupyter notebook server
      shell: |
        cd /workspace
        nohup jupyter notebook --ip=0.0.0.0 --port=8080 --no-browser --allow-root &
      async: 10
      poll: 0
      ignore_errors: true

- name: Verify development environment
  hosts: localhost
  gather_facts: false

  tasks:
    - name: Test database connection
      shell: |
        podman exec dev-workspace psql postgresql://developer:devpass@dev-database:5432/devdb -c "SELECT version();"
      register: db_test
      ignore_errors: true

    - name: Test Redis connection
      shell: |
        podman exec dev-workspace redis-cli -h dev-redis ping
      register: redis_test
      ignore_errors: true

    - name: Display environment status
      debug:
        msg: |
          Development environment ready!

          Services:
          - Database: {{ 'OK' if db_test.rc == 0 else 'FAILED' }}
          - Redis: {{ 'OK' if redis_test.rc == 0 else 'FAILED' }}
          - Workspace: Running

          Access:
          - Jupyter: http://localhost:8080
          - Workspace: podman exec -it dev-workspace /bin/bash
          - Database: psql postgresql://developer:devpass@localhost:5432/devdb

          Workspace mounted at: /workspace
```

## Performance and Best Practices

### Connection Caching

Both plugins internally cache lightweight details (for example, container validation) to reduce overhead. There are no user-facing options to control this.

### Mount Detection

Enable mount detection for efficient file transfers:

```yaml
# Automatically detect shared mounts (default: true)
ansible_podman_mount_detection: true
ansible_buildah_mount_detection: true

# Ignore mount detection errors
ansible_podman_ignore_mount_errors: true
ansible_buildah_ignore_mount_errors: true
```

### Timeout Configuration

Configure optional timeouts (default is 0 = no timeout):

```yaml
# Command timeout in seconds (0 = no timeout)
ansible_podman_timeout: 0
ansible_buildah_timeout: 0
```

### Environment Variable Management

Efficiently pass environment variables:

```yaml
# Method 1: Individual variables
ansible_podman_extra_env:
  API_KEY: "{{ vault_api_key }}"
  DEBUG: "true"
  LOG_LEVEL: "INFO"

# Method 2: From file
ansible_podman_extra_env: "{{ lookup('file', 'env.json') | from_json }}"
```

### Best Practices

1. **Use specific container names**: Avoid generic names to prevent conflicts
2. **Implement health checks**: Use container health checks for reliability
3. **Handle secrets securely**: Use Ansible Vault for sensitive data
4. **Monitor resource usage**: Set appropriate memory and CPU limits
5. **Use multi-stage builds**: Optimize image size with Buildah multi-stage builds
6. **Cache dependencies**: Leverage layer caching for faster builds
7. **Design for fail-fast**: Prefer explicit failed_when/changed_when instead of retries

## Troubleshooting

### Common Issues

#### Container Not Found

```text
Error: Container 'my-container' not found
```

**Solution**: Ensure the container is running and the name/ID is correct.

#### Permission Denied

```text
Error: Permission denied when accessing container
```

**Solution**: Check container permissions or run with appropriate privileges.

#### Timeout Errors

```text
Error: Command execution timed out
```

**Solution**: Increase timeout values or optimize commands.

#### Mount Detection Failures

```text
Warning: Mount detection failed
```

**Solution**: Disable mount detection or ignore mount errors.

### Debug Configuration

Enable verbose logging for troubleshooting:

```yaml
# Enable debug logging
ansible_podman_debug: true
ansible_buildah_debug: true

# Increase verbosity
ansible_verbosity: 3
```

### Testing Connection

Test connection plugin functionality:

```bash
# Test Podman connection
ansible -i inventory -m setup podman_host

# Test Buildah connection
ansible -i inventory -m setup buildah_host

# Run connection tests
./ci/run_connection_test.sh podman
./ci/run_connection_test.sh buildah
```

## Migration from Legacy Plugins

### From Docker Connection Plugin

Replace Docker connection configuration:

```yaml
# Old Docker configuration
ansible_connection: docker
ansible_docker_extra_args: "--user root"

# New Podman configuration
ansible_connection: containers.podman.podman
ansible_podman_extra_env:
  USER: root
```

### From Custom Scripts

Replace custom container execution scripts:

```yaml
# Old custom script approach
- name: Run in container
  shell: podman exec my-container {{ command }}

# New connection plugin approach
- name: Run in container
  hosts: my-container
  vars:
    ansible_connection: containers.podman.podman
  tasks:
    - name: Execute command
      command: "{{ command }}"
```

### Configuration Mapping

| Legacy Option | Podman Plugin | Buildah Plugin |
|---------------|---------------|----------------|
| `ansible_docker_extra_args` | `ansible_podman_extra_env` | `ansible_buildah_extra_env` |
| `ansible_docker_timeout` | `ansible_podman_timeout` | `ansible_buildah_timeout` |
| N/A | `ansible_podman_retries` | `ansible_buildah_retries` |
| N/A | `ansible_podman_mount_detection` | `ansible_buildah_mount_detection` |

---

For more information and examples, see the [official documentation](https://github.com/containers/ansible-podman-collections) and [test cases](tests/integration/targets/).
