"""Docker sandbox — isolated environment for running generated prototypes."""

from __future__ import annotations

import asyncio
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SandboxResult:
    """Result of executing code in the sandbox."""
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    files_created: list[str] = field(default_factory=list)


@dataclass
class Sandbox:
    """Manages an isolated Docker container for code execution.

    Security constraints (from PRD Section 6.4):
    - No outbound network access
    - Resource limits: 2 CPU, 2 GB RAM, 5-min timeout
    - Read-only source mount, write-only output mount
    - Automatic cleanup after execution
    """

    timeout_seconds: int = 300
    memory_limit: str = "2g"
    cpu_count: int = 2
    image: str = "python:3.12-slim"

    async def execute(
        self,
        files: dict[str, str],
        command: str,
        language: str = "python",
    ) -> SandboxResult:
        """Write files to a temp directory and execute inside Docker.

        Args:
            files: Dict of {relative_path: content} to write
            command: Command to run inside the container
            language: "python" or "node" — selects the base image

        Returns:
            SandboxResult with stdout, stderr, exit code.
        """
        image = "node:20-slim" if language in ("typescript", "javascript") else self.image

        with tempfile.TemporaryDirectory(prefix="sandbox_") as tmpdir:
            project_dir = Path(tmpdir) / "project"
            project_dir.mkdir()

            for rel_path, content in files.items():
                file_path = project_dir / rel_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)

            docker_cmd = [
                "docker", "run",
                "--rm",
                "--network=none",
                f"--memory={self.memory_limit}",
                f"--cpus={self.cpu_count}",
                "--read-only", 
                "--tmpfs=/tmp:rw,size=100m",
                "-v", f"{project_dir}:/app:ro",
                "-w", "/app",
                image,
                "sh", "-c", command,
            ]

            try:
                proc = await asyncio.create_subprocess_exec(
                    *docker_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        proc.communicate(),
                        timeout=self.timeout_seconds,
                    )
                    return SandboxResult(
                        exit_code=proc.returncode or 0,
                        stdout=stdout_bytes.decode(errors="replace"),
                        stderr=stderr_bytes.decode(errors="replace"),
                    )
                except asyncio.TimeoutError:
                    proc.kill()
                    return SandboxResult(
                        exit_code=-1,
                        stdout="",
                        stderr=f"Execution timed out after {self.timeout_seconds}s",
                        timed_out=True,
                    )

            except FileNotFoundError:
                return SandboxResult(
                    exit_code=-1,
                    stdout="",
                    stderr="Docker not found. Install Docker Desktop and ensure it's running.",
                )
            except Exception as e:
                return SandboxResult(
                    exit_code=-1,
                    stdout="",
                    stderr=f"Sandbox error: {e}",
                )

    async def check_syntax(self, files: dict[str, str]) -> SandboxResult:
        """Quick syntax check without running the full app."""
        checks = []
        for path in files:
            if path.endswith(".py"):
                checks.append(f"python -m py_compile /app/{path}")

        if not checks:
            return SandboxResult(exit_code=0, stdout="No Python files to check", stderr="")

        command = " && ".join(checks)
        return await self.execute(files, command)
