import sys
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION_FILE = os.path.join(BASE_DIR, "VERSION")

def get_current_version():
    with open(VERSION_FILE, "r") as f:
        return f.read().strip()

def set_version(new_version):
    with open(VERSION_FILE, "w") as f:
        f.write(new_version + "\n")

def run_command(cmd):
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def release(new_version):
    current = get_current_version()
    print(f"Current version: {current}")
    print(f"New version: {new_version}")
    
    set_version(new_version)
    
    run_command(["git", "add", "VERSION"])
    run_command(["git", "commit", "-m", f"chore: bump version to {new_version}"])
    run_command(["git", "tag", f"v{new_version}"])
    
    print(f"Successfully created release v{new_version}")
    print("Run 'git push --tags' to publish.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python release.py <new_version>")
        print("Example: python release.py 1.0.0-beta")
        sys.exit(1)
        
    release(sys.argv[1])
