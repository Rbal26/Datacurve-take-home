import docker
from pathlib import Path
import os


def run_tests_in_docker(repo_path: str, test_command: str, timeout: int = 300) -> dict:
    try:
        client = docker.from_env()
        
        abs_repo_path = Path(repo_path).absolute()
        
        if not abs_repo_path.exists():
            return {
                "tests_passed": False,
                "test_exit_code": -1,
                "test_output_snippet": f"Repository path not found: {repo_path}"
            }
        
        full_command = f"cd /app && pip install -q -r requirements.txt 2>/dev/null && {test_command}"
        
        try:
            container = client.containers.run(
                image='python:3.11-slim',
                command=['sh', '-c', full_command],
                volumes={str(abs_repo_path): {'bind': '/app', 'mode': 'ro'}},
                working_dir='/app',
                detach=False,
                stdout=True,
                stderr=True,
                remove=True
            )
            
            output = container.decode('utf-8')
            exit_code = 0
            
        except docker.errors.ContainerError as e:
            output = e.stderr.decode('utf-8') if e.stderr else str(e)
            exit_code = e.exit_status
            
        except Exception as e:
            output = str(e)
            exit_code = -1
        
        output_snippet = output[:2000] if output else "No output"
        
        return {
            "tests_passed": exit_code == 0,
            "test_exit_code": exit_code,
            "test_output_snippet": output_snippet
        }
        
    except docker.errors.DockerException as e:
        return {
            "tests_passed": False,
            "test_exit_code": -1,
            "test_output_snippet": f"Docker error: {str(e)}"
        }
    except Exception as e:
        return {
            "tests_passed": False,
            "test_exit_code": -1,
            "test_output_snippet": f"Unexpected error: {str(e)}"
        }