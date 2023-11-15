#!/usr/bin/python
# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r'''
module: podman_play
author:
  - "Sagi Shnaidman (@sshnaidm)"
short_description: Play kubernetes YAML file using podman
notes: []
description:
  - The module reads in a structured file of Kubernetes YAML.
    It will then recreate the pod and containers described in the YAML.
requirements:
  - "Podman installed on host"
options:
  executable:
    description:
      - Name of executable to run, by default 'podman'
    type: str
    default: podman
  kube_file:
    description:
      - Path to file with YAML configuration for a Pod.
    type: path
    required: True
  annotation:
    description:
      - Add an annotation to the container or pod.
    type: dict
    aliases:
      - annotations
  authfile:
    description:
      - Path of the authentication file. Default is ${XDG_RUNTIME_DIR}/containers/auth.json,
        which is set using podman login. If the authorization state is not found there,
        $HOME/.docker/config.json is checked, which is set using docker login.
        Note - You can also override the default path of the authentication file
        by setting the REGISTRY_AUTH_FILE environment variable. export REGISTRY_AUTH_FILE=path
    type: path
  build:
    description:
      - Build images even if they are found in the local storage.
      - It is required to exist subdirectories matching the image names to be build.
    type: bool
  cert_dir:
    description:
      - Use certificates at path (*.crt, *.cert, *.key) to connect to the registry.
        Default certificates directory is /etc/containers/certs.d.
        (This option is not available with the remote Podman client)
    type: path
  configmap:
    description:
      - Use Kubernetes configmap YAML at path to provide a source for environment
        variable values within the containers of the pod.
        Note - The configmap option can be used multiple times to pass multiple
        Kubernetes configmap YAMLs
    type: list
    elements: path
  context_dir:
    description:
      - Use path as the build context directory for each image.
        Requires build option be true.
    type: path
  seccomp_profile_root:
    description:
      - Directory path for seccomp profiles (default is "/var/lib/kubelet/seccomp").
        This option is not available with the remote Podman client
    type: path
  username:
    description:
      - The username and password to use to authenticate with the registry if required.
    type: str
  password:
    description:
      - The username and password to use to authenticate with the registry if required.
    type: str
  log_driver:
    description:
      - Set logging driver for all created containers.
    type: str
  log_opt:
    description:
      - Logging driver specific options. Set custom logging configuration.
    type: dict
    aliases:
      - log_options
    suboptions:
      path:
        description:
          - specify a path to the log file (e.g. /var/log/container/mycontainer.json).
        type: str
        required: false
      max_size:
        description:
          - Specify a max size of the log file (e.g 10mb).
        type: str
        required: false
      tag:
        description:
          - specify a custom log tag for the container. This option is currently supported only by the journald log driver in Podman.
        type: str
        required: false
  log_level:
    description:
      - Set logging level for podman calls. Log messages above specified level
        ("debug"|"info"|"warn"|"error"|"fatal"|"panic") (default "error")
    type: str
    choices:
      - debug
      - info
      - warn
      - error
      - fatal
      - panic
  network:
    description:
      - List of the names of CNI networks the pod should join.
    type: list
    elements: str
  state:
    description:
      - Start the pod after creating it, or to leave it created only.
    type: str
    choices:
      - created
      - started
      - absent
    required: True
  tls_verify:
    description:
      - Require HTTPS and verify certificates when contacting registries (default is true).
        If explicitly set to true, then TLS verification will be used. If set to false,
        then TLS verification will not be used. If not specified, TLS verification will be
        used unless the target registry is listed as an insecure registry in registries.conf.
    type: bool
  debug:
    description:
      - Enable debug for the module.
    type: bool
  recreate:
    description:
      - If pod already exists, delete it and run the new one.
    type: bool
  quiet:
    description:
      - Hide image pulls logs from output.
    type: bool
  userns:
    description:
    - Set the user namespace mode for all the containers in a pod.
      It defaults to the PODMAN_USERNS environment variable.
      An empty value ("") means user namespaces are disabled.
    required: false
    type: str
'''

EXAMPLES = '''
- name: Play kube file
  containers.podman.podman_play:
    kube_file: ~/kube.yaml
    state: started

- name: Recreate pod from a kube file with options
  containers.podman.podman_play:
    kube_file: ~/kube.yaml
    state: started
    recreate: true
    annotations:
      greeting: hello
      greet_to: world
    userns: host
    log_opt:
      path: /tmp/my-container.log
      max_size: 10mb
'''
import re  # noqa: F402
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from ansible.module_utils.basic import AnsibleModule  # noqa: F402


class PodmanKubeManagement:

    def __init__(self, module, executable):
        self.module = module
        self.actions = []
        self.executable = executable
        self.command = [self.executable, 'play', 'kube']
        creds = []
        # pod_name = extract_pod_name(module.params['kube_file'])
        if self.module.params['annotation']:
            for k, v in self.module.params['annotation'].items():
                self.command.extend(['--annotation', '"{k}={v}"'.format(k=k, v=v)])
        if self.module.params['username']:
            creds += [self.module.params['username']]
            if self.module.params['password']:
                creds += [self.module.params['password']]
            creds = ":".join(creds)
            self.command.extend(['--creds=%s' % creds])
        if self.module.params['network']:
            networks = ",".join(self.module.params['network'])
            self.command.extend(['--network=%s' % networks])
        if self.module.params['configmap']:
            configmaps = ",".join(self.module.params['configmap'])
            self.command.extend(['--configmap=%s' % configmaps])
        if self.module.params['log_opt']:
            for k, v in self.module.params['log_opt'].items():
                self.command.extend(['--log-opt', '{k}={v}'.format(k=k.replace('_', '-'), v=v)])
        start = self.module.params['state'] == 'started'
        self.command.extend(['--start=%s' % str(start).lower()])
        for arg, param in {
            '--authfile': 'authfile',
            '--build': 'build',
            '--cert-dir': 'cert_dir',
            '--context-dir': 'context_dir',
            '--log-driver': 'log_driver',
            '--seccomp-profile-root': 'seccomp_profile_root',
            '--tls-verify': 'tls_verify',
            '--log-level': 'log_level',
            '--userns': 'userns',
            '--quiet': 'quiet',
        }.items():
            if self.module.params[param] is not None:
                self.command += ["%s=%s" % (arg, self.module.params[param])]
        self.command += [self.module.params['kube_file']]

    def _command_run(self, cmd):
        rc, out, err = self.module.run_command(cmd)
        self.actions.append(" ".join(cmd))
        if self.module.params['debug']:
            self.module.log('PODMAN-PLAY-KUBE command: %s' % " ".join(cmd))
            self.module.log('PODMAN-PLAY-KUBE stdout: %s' % out)
            self.module.log('PODMAN-PLAY-KUBE stderr: %s' % err)
            self.module.log('PODMAN-PLAY-KUBE rc: %s' % rc)
        return rc, out, err

    def discover_pods(self):
        pod_name = ''
        if self.module.params['kube_file']:
            if HAS_YAML:
                with open(self.module.params['kube_file']) as f:
                    pod = yaml.safe_load(f)
                if 'metadata' in pod:
                    pod_name = pod['metadata'].get('name')
                else:
                    self.module.fail_json(
                        "No metadata in Kube file!\n%s" % pod)
            else:
                with open(self.module.params['kube_file']) as text:
                    # the following formats are matched for a kube name:
                    # should match name field within metadata (2 or 4 spaces in front of name)
                    # the name can be written without quotes, in single or double quotes
                    # the name can contain -_
                    re_pod_name = re.compile(r'^\s{2,4}name: ["|\']?(?P<pod_name>[\w|\-|\_]+)["|\']?', re.MULTILINE)
                    re_pod = re_pod_name.search(text.read())
                    if re_pod:
                        pod_name = re_pod.group(1)
        if not pod_name:
            self.module.fail_json("Deployment doesn't have a name!")
        # Find all pods
        all_pods = ''
        # In case of one pod or replicasets
        for name in ("name=%s$", "name=%s-pod-*"):
            cmd = [self.executable,
                   "pod", "ps", "-q", "--filter", name % pod_name]
            rc, out, err = self._command_run(cmd)
            all_pods += out
        ids = list(set([i for i in all_pods.splitlines() if i]))
        return ids

    def remove_associated_pods(self, pods):
        changed = False
        out_all, err_all = '', ''
        # Delete all pods
        for pod_id in pods:
            rc, out, err = self._command_run(
                [self.executable, "pod", "rm", "-f", pod_id])
            if rc != 0:
                self.module.fail_json("Can NOT delete Pod %s" % pod_id)
            else:
                changed = True
                out_all += out
                err_all += err
        return changed, out_all, err_all

    def pod_recreate(self):
        pods = self.discover_pods()
        self.remove_associated_pods(pods)
        # Create a pod
        rc, out, err = self._command_run(self.command)
        if rc != 0:
            self.module.fail_json("Can NOT create Pod! Error: %s" % err)
        return out, err

    def play(self):
        rc, out, err = self._command_run(self.command)
        if rc != 0 and 'pod already exists' in err:
            if self.module.params['recreate']:
                out, err = self.pod_recreate()
                changed = True
            else:
                changed = False
            err = "\n".join([
                i for i in err.splitlines() if 'pod already exists' not in i])
        elif rc != 0:
            self.module.fail_json(msg="Output: %s\nError=%s" % (out, err))
        else:
            changed = True
        return changed, out, err


def main():
    module = AnsibleModule(
        argument_spec=dict(
            annotation=dict(type='dict', aliases=['annotations']),
            executable=dict(type='str', default='podman'),
            kube_file=dict(type='path', required=True),
            authfile=dict(type='path'),
            build=dict(type='bool'),
            cert_dir=dict(type='path'),
            configmap=dict(type='list', elements='path'),
            context_dir=dict(type='path'),
            seccomp_profile_root=dict(type='path'),
            username=dict(type='str'),
            password=dict(type='str', no_log=True),
            log_driver=dict(type='str'),
            log_opt=dict(type='dict', aliases=['log_options'], options=dict(
                path=dict(type='str'),
                max_size=dict(type='str'),
                tag=dict(type='str'))),
            network=dict(type='list', elements='str'),
            state=dict(
                type='str',
                choices=['started', 'created', 'absent'],
                required=True),
            tls_verify=dict(type='bool'),
            debug=dict(type='bool'),
            quiet=dict(type='bool'),
            recreate=dict(type='bool'),
            userns=dict(type='str'),
            log_level=dict(
                type='str',
                choices=["debug", "info", "warn", "error", "fatal", "panic"]),
        ),
        supports_check_mode=True,
    )

    executable = module.get_bin_path(
        module.params['executable'], required=True)
    manage = PodmanKubeManagement(module, executable)
    if module.params['state'] == 'absent':
        pods = manage.discover_pods()
        changed, out, err = manage.remove_associated_pods(pods)
    else:
        changed, out, err = manage.play()
    results = {
        "changed": changed,
        "stdout": out,
        "stderr": err,
        "actions": manage.actions
    }
    module.exit_json(**results)


if __name__ == '__main__':
    main()
