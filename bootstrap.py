#!/usr/bin/env python3
"""
Bootstrap Script.

Initializes the virtual environment and installs dependencies.
Safely detects existing environments to prevent destructive overwrites.
"""

import os
import sys
import venv
import subprocess
from pathlib import Path

def main() -> None:
    print("Initializing VPNResearchLab Environment...")
    base_dir = Path(__file__).resolve().parent
    venv_dir = base_dir / ".venv"

    if sys.platform == "win32":
        python_path = venv_dir / "Scripts" / "python.exe"
    else:
        python_path = venv_dir / "bin" / "python"

    if python_path.exists():
        print("[+] Existing virtual environment detected.")
    else:
        print("[*] Creating Python virtual environment...")
        venv.create(venv_dir, with_pip=True)
        print("[+] Virtual environment created successfully.")

    # Determine pip path
    if sys.platform == "win32":
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        pip_exe = venv_dir / "bin" / "pip"

    if not pip_exe.exists():
        print(f"[-] FATAL: Pip executable not found at {pip_exe}")
        sys.exit(1)

    print("[*] Upgrading pip...")
    subprocess.run([str(pip_exe), "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)

    print("[*] Installing requirements...")
    req_file = base_dir / "requirements.txt"
    if req_file.exists():
        subprocess.run([str(pip_exe), "install", "-r", str(req_file)], check=True)
        print("[+] Dependencies installed successfully.")
    else:
        print("[-] WARNING: requirements.txt not found. Skipping dependency installation.")

    print("\nBootstrap complete. Activate your environment:")
    if sys.platform == "win32":
        print("    .venv\\Scripts\\activate")
    else:
        print("    source .venv/bin/activate")


if __name__ == "__main__":
    main()