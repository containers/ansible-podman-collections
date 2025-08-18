# Copyright (c) 2024 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
import json
import os
import shlex
import tempfile
import time
import hashlib
import sys

from ansible_collections.containers.podman.plugins.module_utils.podman.common import run_podman_command

__metaclass__ = type


class PodmanImageError(Exception):
    """Custom exception for Podman image operations."""


class ImageRepository:
    """Parse and manage image repository information."""

    def __init__(self, name, tag="latest"):
        self.original_name = name
        self.name, self.parsed_tag = self._parse_repository_tag(name)
        self.tag = self.parsed_tag or tag
        self.delimiter = "@" if self.tag.startswith("sha256:") else ":"
        self.full_name = f"{self.name}{self.delimiter}{self.tag}"

    @staticmethod
    def _parse_repository_tag(repo_name):
        """Parse repository name and tag/digest."""
        parts = repo_name.rsplit("@", 1)
        if len(parts) == 2:
            return tuple(parts)
        parts = repo_name.rsplit(":", 1)
        if len(parts) == 2 and "/" not in parts[1]:
            return tuple(parts)
        return repo_name, None


class ContainerFileProcessor:
    """Handle Containerfile/Dockerfile processing and hashing."""

    def __init__(self, build_config, path=None):
        self.build_config = build_config or {}
        self.path = path

    def get_containerfile_contents(self):
        """Get Containerfile contents from various sources."""
        build_file_arg = self.build_config.get("file")
        containerfile_contents = self.build_config.get("container_file")

        container_filename = None
        if build_file_arg:
            container_filename = build_file_arg
        elif self.path and not build_file_arg:
            container_filename = self._find_containerfile_from_context()

        if not containerfile_contents and container_filename and os.access(container_filename, os.R_OK):
            with open(container_filename, "r", encoding='utf-8') as f:
                containerfile_contents = f.read()

        return containerfile_contents

    def _find_containerfile_from_context(self):
        """Find Containerfile/Dockerfile in build context."""
        if not self.path:
            return None

        for filename in ["Containerfile", "Dockerfile"]:
            full_path = os.path.join(self.path, filename)
            if os.path.exists(full_path):
                return full_path
        return None

    def hash_containerfile_contents(self, contents):
        """Generate SHA256 hash of Containerfile contents."""
        if not contents:
            return None

        if sys.version_info < (3, 9):
            return hashlib.sha256(contents.encode()).hexdigest()
        return hashlib.sha256(contents.encode(), usedforsecurity=False).hexdigest()


class PodmanImageInspector:
    """Handle image inspection operations."""

    def __init__(self, module, executable):
        self.module = module
        self.executable = executable

    def inspect_image(self, image_name):
        """Inspect an image and return its data."""
        args = ["inspect", image_name, "--format", "json"]
        rc, out, unused = run_podman_command(self.module, self.executable, args, ignore_errors=True)

        if rc != 0:
            return None

        try:
            image_data = json.loads(out)
            return image_data if image_data else None
        except json.JSONDecodeError:
            self.module.fail_json(msg=f"Failed to parse JSON output from podman inspect: {out}")

    def image_exists(self, image_name):
        """Check if an image exists."""
        rc, out, err = run_podman_command(
            self.module, self.executable, ["image", "exists", image_name], ignore_errors=True
        )
        return rc == 0

    def list_images(self, image_name):
        """List images matching the given name."""
        args = ["image", "ls", image_name, "--format", "json"]
        rc, out, err = run_podman_command(self.module, self.executable, args, ignore_errors=True)

        if rc != 0:
            return []

        try:
            return json.loads(out) or []
        except json.JSONDecodeError:
            self.module.fail_json(msg=f"Failed to parse JSON output from podman image ls: {out}")


class PodmanImageBuilder:
    """Handle image building operations."""

    def __init__(self, module, executable, auth_config=None):
        self.module = module
        self.executable = executable
        self.auth_config = auth_config or {}

    def build_image(self, image_name, build_config, path=None, containerfile_hash=None):
        """Build an image with the given configuration."""
        args = self._construct_build_args(image_name, build_config, path, containerfile_hash)

        # Handle inline container file
        temp_file_path = None
        if build_config.get("container_file"):
            temp_file_path = self._create_temp_containerfile(build_config["container_file"], path)
            args.extend(["--file", temp_file_path])

        try:
            # Return the command that will be executed for podman_actions tracking
            podman_command = " ".join([self.executable] + args)
            rc, out, err = run_podman_command(self.module, self.executable, args, ignore_errors=True)

            if rc != 0:
                self.module.fail_json(msg=f"Failed to build image {image_name}: {out} {err}")

            # Extract image ID from output
            last_id = self._extract_image_id_from_output(out)
            return last_id, out + err, podman_command

        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def _construct_build_args(self, image_name, build_config, path, containerfile_hash):
        """Construct build command arguments."""
        args = ["build", "-t", image_name]

        # Add authentication
        self._add_auth_args(args)

        # Add build-specific arguments
        if build_config.get("force_rm"):
            args.append("--force-rm")

        if build_config.get("format"):
            args.extend(["--format", build_config["format"]])

        if not build_config.get("cache", True):
            args.append("--no-cache")

        if build_config.get("rm", True):
            args.append("--rm")

        # Add annotations
        annotations = build_config.get("annotation") or {}
        for key, value in annotations.items():
            args.extend(["--annotation", f"{key}={value}"])

        # Add containerfile hash as label
        if containerfile_hash:
            args.extend(["--label", f"containerfile.hash={containerfile_hash}"])

        # Add volumes
        volumes = build_config.get("volume") or []
        for volume in volumes:
            if volume:
                args.extend(["--volume", volume])

        # Add build file
        if build_config.get("file"):
            args.extend(["--file", build_config["file"]])

        # Add target
        if build_config.get("target"):
            args.extend(["--target", build_config["target"]])

        # Add extra args
        extra_args = build_config.get("extra_args")
        if extra_args:
            args.extend(shlex.split(extra_args))

        # Add build context path
        if path:
            args.append(path)

        return args

    def _add_auth_args(self, args):
        """Add authentication arguments to command."""
        if self.auth_config.get("validate_certs") is not None:
            if self.auth_config["validate_certs"]:
                args.append("--tls-verify")
            else:
                args.append("--tls-verify=false")

        if self.auth_config.get("ca_cert_dir"):
            args.extend(["--cert-dir", self.auth_config["ca_cert_dir"]])

        if self.auth_config.get("auth_file"):
            args.extend(["--authfile", self.auth_config["auth_file"]])

        if self.auth_config.get("username") and self.auth_config.get("password"):
            cred_string = f"{self.auth_config['username']}:{self.auth_config['password']}"
            args.extend(["--creds", cred_string])

    def _create_temp_containerfile(self, content, path):
        """Create a temporary Containerfile with the given content."""
        if path:
            temp_path = os.path.join(path, f"Containerfile.generated_by_ansible_{time.time()}")
        else:
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"Containerfile.generated_by_ansible_{time.time()}")

        with open(temp_path, "w", encoding='utf-8') as f:
            f.write(content)

        return temp_path

    def _extract_image_id_from_output(self, output):
        """Extract image ID from build output."""
        for line in output.splitlines():
            if line.startswith("-->"):
                parts = line.rsplit(" ", 1)
                if len(parts) > 1:
                    return parts[1]

        # Fallback to last line if no --> found
        lines = output.splitlines()
        return lines[-1] if lines else ""


class PodmanImagePuller:
    """Handle image pulling operations."""

    def __init__(self, module, executable, auth_config=None):
        self.module = module
        self.executable = executable
        self.auth_config = auth_config or {}

    def pull_image(self, image_name, arch=None, pull_extra_args=None):
        """Pull an image from a registry."""
        args = ["pull", image_name]

        if arch:
            args.extend(["--arch", arch])

        self._add_auth_args(args)

        if pull_extra_args:
            args.extend(shlex.split(pull_extra_args))

        # Return the command that will be executed for podman_actions tracking
        podman_command = " ".join([self.executable] + args)
        rc, out, err = run_podman_command(self.module, self.executable, args, ignore_errors=True)

        if rc != 0:
            self.module.fail_json(msg=f"Failed to pull image {image_name}", stderr=err, stdout=out)

        return out.strip(), podman_command

    def _add_auth_args(self, args):
        """Add authentication arguments to command."""
        if self.auth_config.get("validate_certs") is not None:
            if self.auth_config["validate_certs"]:
                args.append("--tls-verify")
            else:
                args.append("--tls-verify=false")

        if self.auth_config.get("ca_cert_dir"):
            args.extend(["--cert-dir", self.auth_config["ca_cert_dir"]])

        if self.auth_config.get("auth_file"):
            args.extend(["--authfile", self.auth_config["auth_file"]])

        if self.auth_config.get("username") and self.auth_config.get("password"):
            cred_string = f"{self.auth_config['username']}:{self.auth_config['password']}"
            args.extend(["--creds", cred_string])


class PodmanImagePusher:
    """Handle image pushing operations."""

    def __init__(self, module, executable, auth_config=None):
        self.module = module
        self.executable = executable
        self.auth_config = auth_config or {}

    def push_image(self, image_name, push_config):
        """Push an image to a registry."""
        transport = (push_config or {}).get("transport")

        # Special handling for scp transport which uses 'podman image scp'
        if transport == "scp":
            args = []

            # Allow passing global --ssh options to podman
            ssh_opts = push_config.get("ssh") if push_config else None
            if ssh_opts:
                args.extend(["--ssh", ssh_opts])

            args.extend(["image", "scp"])

            # Extra args (e.g., --quiet) if provided
            if push_config.get("extra_args"):
                args.extend(shlex.split(push_config["extra_args"]))

            # Source image (local)
            args.append(image_name)

            # Destination host spec
            dest = push_config.get("dest")
            if not dest:
                self.module.fail_json(msg="When using transport 'scp', push_args.dest must be provided")

            # If user did not include '::' in dest, append it to copy into remote storage with same name
            dest_spec = dest if "::" in dest else f"{dest}::"
            args.append(dest_spec)

            action = " ".join(args)
            rc, out, err = run_podman_command(self.module, self.executable, args, ignore_errors=True)
            if rc != 0:
                self.module.fail_json(
                    msg=f"Failed to scp image {image_name} to {dest}", stdout=out, stderr=err, actions=[action]
                )
            return out + err, action

        # Default push behavior for all other transports
        args = ["push"]

        self._add_auth_args(args)
        self._add_push_args(args, push_config)

        args.append(image_name)

        # Build destination
        dest_string = self._build_destination(image_name, push_config)
        args.append(dest_string)
        action = " ".join(args)

        rc, out, err = run_podman_command(self.module, self.executable, args, ignore_errors=True)

        if rc != 0:
            self.module.fail_json(msg=f"Failed to push image {image_name}", stdout=out, stderr=err, actions=[action])

        return out + err, action

    def _add_auth_args(self, args):
        """Add authentication arguments to command."""
        if self.auth_config.get("validate_certs") is not None:
            if self.auth_config["validate_certs"]:
                args.append("--tls-verify")
            else:
                args.append("--tls-verify=false")

        if self.auth_config.get("ca_cert_dir"):
            args.extend(["--cert-dir", self.auth_config["ca_cert_dir"]])

        if self.auth_config.get("auth_file"):
            args.extend(["--authfile", self.auth_config["auth_file"]])

        if self.auth_config.get("username") and self.auth_config.get("password"):
            cred_string = f"{self.auth_config['username']}:{self.auth_config['password']}"
            args.extend(["--creds", cred_string])

    def _add_push_args(self, args, push_config):
        """Add push-specific arguments."""
        if push_config.get("compress"):
            args.append("--compress")

        if push_config.get("format"):
            args.extend(["--format", push_config["format"]])

        if push_config.get("remove_signatures"):
            args.append("--remove-signatures")

        if push_config.get("sign_by"):
            args.extend(["--sign-by", push_config["sign_by"]])

        if push_config.get("extra_args"):
            args.extend(shlex.split(push_config["extra_args"]))

    def _build_destination(self, image_name, push_config):
        """Build the destination string for push."""
        dest = push_config.get("dest") or image_name
        transport = push_config.get("transport")

        if not transport:
            # Handle simple registry destination
            if ":" not in dest and "@" not in dest and len(dest.rstrip("/").split("/")) == 2:
                return f"{dest.rstrip('/')}/{image_name}"
            if "/" not in dest and "@" not in dest and "docker-daemon" not in dest:
                self.module.fail_json(
                    msg="Destination must be a full URL or path to a directory with image name and tag."
                )
            return dest

        # Handle transport-specific destinations
        name_parts = image_name.split("/")
        image_base_name = name_parts[-1].split(":")[0]

        if transport == "docker":
            return f"{transport}://{dest}"
        if transport == "ostree":
            return f"{transport}:{image_base_name}@{dest}"
        if transport == "docker-daemon":
            if ":" not in dest:
                return f"{transport}:{dest}:latest"
            return f"{transport}:{dest}"
        return f"{transport}:{dest}"


class PodmanImageRemover:
    """Handle image removal operations."""

    def __init__(self, module, executable):
        self.module = module
        self.executable = executable

    def remove_image(self, image_name, force=False):
        """Remove an image by name."""
        args = ["rmi", image_name]
        if force:
            args.append("--force")

        # Return the command that will be executed for podman_actions tracking
        podman_command = " ".join([self.executable] + args)
        rc, out, err = run_podman_command(self.module, self.executable, args, ignore_errors=True)

        if rc != 0:
            self.module.fail_json(msg=f"Failed to remove image {image_name}: {err}")

        return out, podman_command

    def remove_image_by_id(self, image_id, force=False):
        """Remove an image by ID."""
        args = ["rmi", image_id]
        if force:
            args.append("--force")

        # Return the command that will be executed for podman_actions tracking
        podman_command = " ".join([self.executable] + args)
        rc, out, err = run_podman_command(self.module, self.executable, args, ignore_errors=True)

        if rc != 0:
            self.module.fail_json(msg=f"Failed to remove image with ID {image_id}: {err}")

        return out, podman_command


class PodmanImageManager:
    """Main image management class that orchestrates all operations."""

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.executable = module.get_bin_path(self.params.get("executable", "podman"), required=True)

        # Initialize repository info
        self.repository = ImageRepository(self.params["name"], self.params.get("tag", "latest"))

        # Initialize components
        self.inspector = PodmanImageInspector(self.module, self.executable)

        auth_config = self._build_auth_config()
        self.builder = PodmanImageBuilder(self.module, self.executable, auth_config)
        self.puller = PodmanImagePuller(self.module, self.executable, auth_config)
        self.pusher = PodmanImagePusher(self.module, self.executable, auth_config)
        self.remover = PodmanImageRemover(self.module, self.executable)

        # Initialize containerfile processor
        self.containerfile_processor = ContainerFileProcessor(self.params.get("build", {}), self.params.get("path"))

        # Results tracking
        self.results = {
            "changed": False,
            "actions": [],
            "podman_actions": [],
            "image": {},
            "stdout": "",
        }

    def _build_auth_config(self):
        """Build authentication configuration."""
        return {
            "validate_certs": self.params.get("validate_certs"),
            "ca_cert_dir": self.params.get("ca_cert_dir"),
            "auth_file": self.params.get("auth_file"),
            "username": self.params.get("username"),
            "password": self.params.get("password"),
        }

    def find_image(self, image_name=None):
        """Find an image and return its information."""
        image_name = image_name or self.repository.full_name

        if not self.inspector.image_exists(image_name):
            return None

        images = self.inspector.list_images(image_name)
        if not images:
            return None

        # Check architecture if specified
        arch = self.params.get("arch")
        if arch:
            inspect_data = self.inspector.inspect_image(image_name)
            if inspect_data and inspect_data[0].get("Architecture") != arch:
                return None

        return images

    def _should_rebuild_image(self, existing_image):
        """Determine if an image should be rebuilt based on Containerfile changes."""
        if not existing_image:
            return True

        if self.params.get("force"):
            return True

        # Check Containerfile hash
        containerfile_contents = self.containerfile_processor.get_containerfile_contents()
        if not containerfile_contents:
            return False

        current_hash = self.containerfile_processor.hash_containerfile_contents(containerfile_contents)
        if not current_hash:
            return False

        # Get existing hash from image labels
        existing_hash = ""
        if existing_image:
            labels = existing_image[0].get("Labels") or {}
            existing_hash = labels.get("containerfile.hash", "")

        return current_hash != existing_hash

    def present(self):
        """Ensure image is present (pull or build if needed)."""
        image = self.find_image()

        if not image or self._should_rebuild_image(image):
            if self.params.get("state") == "build" or self.params.get("path"):
                self._build_image()
            else:
                self._pull_image()

        if self.params.get("push"):
            self._push_image()

        # Update results with final image info
        final_image = self.find_image()
        if final_image:
            self.results["image"] = self.inspector.inspect_image(self.repository.full_name)

    def _build_image(self):
        """Build an image."""
        build_config = self.params.get("build", {})
        path = self.params.get("path")

        # Validate build configuration
        if build_config.get("file") and build_config.get("container_file"):
            self.module.fail_json(msg="Cannot specify both build file and container file content!")

        if not path and not build_config.get("file") and not build_config.get("container_file"):
            self.module.fail_json(msg="Path to build context or file is required when building an image")

        # Get containerfile hash
        containerfile_contents = self.containerfile_processor.get_containerfile_contents()
        containerfile_hash = self.containerfile_processor.hash_containerfile_contents(containerfile_contents)

        # Build the image
        if not self.module.check_mode:
            image_id, output, podman_command = self.builder.build_image(
                self.repository.full_name, build_config, path, containerfile_hash
            )
            self.results["stdout"] = output
            self.results["image"] = self.inspector.inspect_image(image_id)
            self.results["podman_actions"].append(podman_command)

        self.results["changed"] = True
        self.results["actions"].append(f"Built image {self.repository.full_name} from {path or 'context'}")

    def _pull_image(self):
        """Pull an image."""
        if not self.params.get("pull", True):
            self.module.fail_json(msg=f"Image {self.repository.full_name} not found locally and pull is disabled")

        if not self.module.check_mode:
            unused, podman_command = self.puller.pull_image(
                self.repository.full_name, self.params.get("arch"), self.params.get("pull_extra_args")
            )
            self.results["image"] = self.inspector.inspect_image(self.repository.full_name)
            self.results["podman_actions"].append(podman_command)

        self.results["changed"] = True
        self.results["actions"].append(f"Pulled image {self.repository.full_name}")

    def _push_image(self):
        """Push an image."""
        push_config = self.params.get("push_args", {})

        if not self.module.check_mode:
            output, action = self.pusher.push_image(self.repository.full_name, push_config)
            self.results["stdout"] += "\n" + output
            self.results["actions"].append(action)
            self.results["podman_actions"].append(f"{self.executable} {action}")

        self.results["changed"] = True
        self.results["actions"].append(f"Pushed image {self.repository.full_name}")

    def absent(self):
        """Ensure image is absent."""
        image = self.find_image()

        if image:
            if not self.module.check_mode:
                unused, podman_command = self.remover.remove_image(
                    self.repository.full_name, self.params.get("force", False)
                )
                self.results["podman_actions"].append(podman_command)

            self.results["changed"] = True
            self.results["actions"].append(f"Removed image {self.repository.full_name}")
            self.results["image"] = {"state": "Deleted"}
        else:
            # Try removing by ID if provided
            image_id = self._extract_image_id(self.repository.original_name)
            if image_id and self._image_id_exists(image_id):
                if not self.module.check_mode:
                    unused, podman_command = self.remover.remove_image_by_id(image_id, self.params.get("force", False))
                    self.results["podman_actions"].append(podman_command)

                self.results["changed"] = True
                self.results["actions"].append(f"Removed image with ID {image_id}")
                self.results["image"] = {"state": "Deleted"}

    def _extract_image_id(self, name):
        """Extract image ID from name if it looks like an ID."""
        # Remove tag if present
        if ":" in name and not name.startswith("sha256:"):
            name = name.split(":")[0]
        return name

    def _image_id_exists(self, image_id):
        """Check if an image ID exists."""
        args = ["image", "ls", "--quiet", "--no-trunc"]
        rc, out, err = run_podman_command(self.module, self.executable, args, ignore_errors=True)

        if rc != 0:
            return False

        candidates = [line.replace("sha256:", "") for line in out.splitlines()]
        return any(candidate.startswith(image_id) for candidate in candidates)

    def execute(self):
        """Execute the requested operation."""
        state = self.params.get("state", "present")

        if state in ["present", "build"]:
            self.present()
        elif state == "absent":
            self.absent()
        elif state == "quadlet":
            # Quadlet functionality will be handled by the main module
            pass

        return self.results
