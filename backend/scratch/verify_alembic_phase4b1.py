import os
import sys
import subprocess

def run_cmd(cmd):
    print(f"Running: {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {res.returncode}")

def main():
    env = os.environ.copy()
    env["PYTHONPATH"] = "."

    # 1. Upgrade head
    run_cmd(f'"{sys.executable}" -m alembic upgrade head')

    # 2. Downgrade to m1q165rs25o2
    run_cmd(f'"{sys.executable}" -m alembic downgrade m1q165rs25o2')

    # 3. Re-upgrade to head
    run_cmd(f'"{sys.executable}" -m alembic upgrade head')

    print("ALEMBIC MIGRATION UPGRADE/DOWNGRADE/RE-UPGRADE SUCCESSFUL!")

if __name__ == "__main__":
    main()
