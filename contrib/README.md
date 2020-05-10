# Various recipes for running tests and CI

## For CentOS 7

```bash
echo "centos:100000:65536" | sudo tee -a /etc/subuid
echo "centos:100000:65536" | sudo tee -a /etc/subgid
echo 1000 | sudo tee /proc/sys/user/max_user_namespaces
```

## prepare VMs

```bash
ANSIBLE_SSH_RETRIES=3 ansible-playbook ci/playbooks/pre.yml -vv -i $INVENTORY -e ansible_venv=/tmp/test-ansible-venv -e ansible_venv_site_packages=true -e clean_venv=true
```

## build from your branch

```bash
ANSIBLE_SSH_RETRIES=3 ansible-playbook ci/playbooks/build.yml -vv -i $INVENTORY -e ansible_venv=/tmp/test-ansible-venv -e repo_url=https://github.com/sshnaidm/ansible-podman-collections.git -e pr_branch=podmanci
```

## build locally

```bash
ansible-playbook -vv -i localhost, -c local  ci/playbooks/build.yml -e repo_dir=/tmp/temp_collection_home -e repo_url=~/ansible-podman-collections/ -e ansible_venv=~/test-ansible-venv/
```

## build locally with bash

```bash
rm -rf /tmp/just_new_collection
~/.local/bin/ansible-galaxy collection build --output-path /tmp/just_new_collection --force
~/.local/bin/ansible-galaxy collection install -vvv --force /tmp/just_new_collection/*.tar.gz
# for root
#sudo ~/.local/bin/ansible-galaxy collection install -vvv --force /tmp/just_new_collection/*.tar.gz
```

## build remotely from PR

```bash
ANSIBLE_SSH_RETRIES=3 ansible-playbook ci/playbooks/build.yml -vv -i $INVENTORY -e ansible_venv=/tmp/test-ansible-venv -e pr=19
```

## run connection tests on remote VMs

```bash
ANSIBLE_SSH_RETRIES=3 ansible-playbook ci/playbooks/connection_test.yml -vv -i $INVENTORY -e ansible_venv=/tmp/test-ansible-venv
```

## run example podman_container test on remote VMs

```bash
ANSIBLE_SSH_RETRIES=3 ansible-playbook ci/playbooks/containers_test.yml -vv -i $INVENTORY -e ansible_venv=/tmp/test-ansible-venv -e test=podman_container
```

## run test of local collection on remote VMs

```bash
ANSIBLE_SSH_RETRIES=3 ANSIBLE_ROLES_PATH=tests/integration/targets ansible-playbook ci/playbooks/containers/podman_container.yml -vv -i $INVENTORY
```
