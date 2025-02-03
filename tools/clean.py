# Author: Wojciech Miskowicz
#
# Description:
# Based on work of Piotr Kaczmarczyk, PhD, AGH University of Krakow.
# Remove untracked files from the project.
# To work properly, a git repository in the project directory is required.
# Run from the project root directory.

import os
import subprocess
import sys

# Load ROOT_DIR from .env file
ENV_FILE = ".env"
ROOT_DIR = None

if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            if line.startswith("ROOT_DIR="):
                ROOT_DIR = line.strip().split("=")[1].strip('"')

if not ROOT_DIR:
    print("Error: ROOT_DIR is not set. Run env.py first to initialize it.")
    sys.exit(1)

# Run git clean -fdX to remove untracked files
try:
    subprocess.run(["git", "clean", "-fdX"], cwd=ROOT_DIR, check=True)
    print("Untracked files removed successfully.")
except subprocess.CalledProcessError:
    print("Error: Failed to clean untracked files. Make sure this is a valid git repository.")
    sys.exit(1)
