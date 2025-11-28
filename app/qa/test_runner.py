from pathlib import Path
import docker
import socket
from typing import Optional
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def _get_host_sample_repo_path() -> Optional[Path]:
    try:
        client = docker.from_env()
        hostname = socket.gethostname()
        container = client.containers.get(hostname)
        mounts = container.attrs.get("Mounts", [])
        for mount in mounts:
            if mount.get("Destination") == "/app/sample_repo":
                source = mount.get("Source")
                if source:
                    return Path(source)
    except Exception as e:
        logger.debug(f"Failed to detect host sample_repo path: {e}")
    return None


def run_tests_in_docker(repo_path: str, test_command: str, timeout: int = 300) -> dict:
    try:
        logger.info(f"Starting Docker test execution: repo={repo_path}, command={test_command}")
        client = docker.from_env()

        is_host_path = False

        if repo_path == "sample_repo":
            host_repo_path = _get_host_sample_repo_path()
            if host_repo_path is not None:
                abs_repo_path = host_repo_path
                is_host_path = True
                logger.info(f"Using host sample_repo path: {abs_repo_path}")
            else:
                abs_repo_path = Path(repo_path).absolute()
        else:
            abs_repo_path = Path(repo_path).absolute()

        if not is_host_path and not abs_repo_path.exists():
            logger.error(f"Repository path not found: {abs_repo_path}")
            return {
                "tests_passed": False,
                "test_exit_code": -1,
                "test_output_snippet": f"Repository path not found: {abs_repo_path}"
            }

        full_command = f"cd /app && pip install -q -r requirements.txt 2>/dev/null && {test_command}"

        try:
            container = client.containers.run(
                image="python:3.11-slim",
                command=["sh", "-c", full_command],
                volumes={str(abs_repo_path): {"bind": "/app", "mode": "ro"}},
                working_dir="/app",
                detach=False,
                stdout=True,
                stderr=True,
                remove=True
            )
            output = container.decode("utf-8")
            exit_code = 0
        except docker.errors.ContainerError as e:
            output = e.stderr.decode("utf-8") if e.stderr else str(e)
            exit_code = e.exit_status
        except Exception as e:
            output = str(e)
            exit_code = -1

        output_snippet = output[:2000] if output else "No output"

        logger.info(f"Docker tests completed: exit_code={exit_code}")

        return {
            "tests_passed": exit_code == 0,
            "test_exit_code": exit_code,
            "test_output_snippet": output_snippet
        }

    except docker.errors.DockerException as e:
        logger.error(f"Docker error: {str(e)}")
        return {
            "tests_passed": False,
            "test_exit_code": -1,
            "test_output_snippet": f"Docker error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error during test execution: {str(e)}")
        return {
            "tests_passed": False,
            "test_exit_code": -1,
            "test_output_snippet": f"Unexpected error: {str(e)}"
        }