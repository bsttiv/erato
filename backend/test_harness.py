"""Host checks for the approved INFRA-001 through INFRA-004 harness rules."""
import os
import subprocess


def run(*args, **kwargs):
    return subprocess.run(args, check=False, text=True, capture_output=True, **kwargs)


for case, backend_exit, frontend_exit in [("INFRA-001", 0, 0), ("INFRA-002", 1, 0), ("INFRA-003", 0, 1)]:
    env = dict(os.environ, TEST_BACKEND_COMMAND=f"python -c 'exit({backend_exit})'",
               TEST_FRONTEND_COMMAND=f"node -e 'process.exit({frontend_exit})'")
    result = run("make", "test", env=env)
    expected_success = backend_exit == frontend_exit == 0
    if (result.returncode == 0) != expected_success:
        print(result.stdout, result.stderr)
        raise SystemExit(f"{case}: unexpected exit {result.returncode}")
    print(f"{case}: passed")
    for kind in ("container", "volume"):
        left = run("docker", kind, "ls", "-q", "--filter", "label=com.docker.compose.project=erato-test")
        if left.returncode or left.stdout.strip():
            raise SystemExit(f"INFRA-004: {kind} cleanup failed: {left.stdout} {left.stderr}")
print("INFRA-004: passed after success and both failure paths")
