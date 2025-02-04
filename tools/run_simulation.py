# Author: Wojciech Miskowicz
#
# Description:
# Based on work of Piotr Kaczmarczyk, PhD, AGH University of Krakow.
# This script runs simulations outside Vivado, making them faster.
# For usage details, run the script with no arguments.
# For more information see: AMD Xilinx UG 900:
# https://docs.xilinx.com/r/en-US/ug900-vivado-logic-simulation/Simulating-in-Batch-or-Scripted-Mode-in-Vivado-Simulator
# To work properly, a git repository in the project directory is required.
# Run from the project root directory.

import os
import sys
import subprocess
import glob
import argparse
import colorama

# Load ROOT_DIR and VIVADO_SETUP from .env file
ENV_FILE = ".env"
ROOT_DIR = None
VIVADO_SETUP = None

colorama.init(autoreset=True)

if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            key, value = line.strip().split("=")
            value = value.strip('"')
            if key == "ROOT_DIR":
                ROOT_DIR = value
            elif key == "VIVADO_SETUP":
                VIVADO_SETUP = value

if not ROOT_DIR:
    print("Error: ROOT_DIR is not set. Run env.py first to initialize it.")
    sys.exit(1)

if not VIVADO_SETUP:
    print("Error: VIVADO_SETUP is not set in .env. Run env.py first to initialize it.")
    sys.exit(1)

SIM_DIR = os.path.join(ROOT_DIR, "sim")
BUILD_DIR = os.path.join(SIM_DIR, "build")

# Ensure build directory exists
os.makedirs(BUILD_DIR, exist_ok=True)

# Vivado setup command
SETUP_CMD = f'call "{VIVADO_SETUP}" && '

def list_available_tests():
    """List all available tests in the sim directory, excluding non-test folders."""
    tests = [name for name in os.listdir(SIM_DIR) if os.path.isdir(os.path.join(SIM_DIR, name))
             and name not in ["build", "common"]]
    if tests:
        print("\n".join(tests))
    else:
        print("No tests found.")
    sys.exit(0)

def execute_test(test_name, show_gui):
    """Run the specified test with or without GUI."""
    # Clean untracked files
    subprocess.run(["git", "clean", "-fXd", "."], cwd=SIM_DIR)

    test_path = os.path.join(SIM_DIR, test_name)
    project_file = os.path.join(test_path, f"{test_name}.prj")

    # Check if glbl.v is included
    compile_glbl = "work.glbl" if "glbl.v" in open(project_file).read() else ""

    xelab_opts = f"work.{test_name}_tb {compile_glbl} -snapshot {test_name}_tb -prj {project_file} -timescale 1ns/1ps -L unisims_ver"

    # Run simulation
    if show_gui:
        subprocess.run(f'cmd.exe /c "{SETUP_CMD} xelab {xelab_opts} -debug typical"', cwd=BUILD_DIR)
        subprocess.run(f'cmd.exe /c "{SETUP_CMD} xsim {test_name}_tb -gui -t {os.path.join(ROOT_DIR, "tools", "sim_cmd.tcl")}"', cwd=BUILD_DIR)
    else:
        process = subprocess.run(f'cmd.exe /c "{SETUP_CMD} xelab {xelab_opts} -standalone -runall"',
                                 cwd=BUILD_DIR, stdout=subprocess.PIPE, text=True)
        log_file = os.path.join(BUILD_DIR, "xsim.log")

        if not os.path.exists(log_file):
            print(colorama.Fore.RED + f"[{test_name}] FAILED (xsim.log not found)")
            return

        with open(log_file, "r") as f:
            log_output = f.read().lower()


        # Check for failure indicators
        failed_keywords = ["fatal", "error", "critical", "failed"]
        passed_keywords = ["test passed"]

        is_failed = any(keyword in log_output for keyword in failed_keywords)
        is_passed = any(keyword in log_output for keyword in passed_keywords)

        # Print the result in color
        if not is_failed:
            print(colorama.Fore.GREEN + f"[{test_name}] PASSED ")
        else:
            print(colorama.Fore.RED + f"[{test_name}] FAILED ")
            with open(log_file, "r") as f:
                for line in f:
                    if any(keyword in line.lower() for keyword in ["fatal", "error"]):
                        print(colorama.Fore.RED + ">> " + line.strip())

def run_all():
    """Run all available tests and summarize results."""
    tests = [name for name in os.listdir(SIM_DIR) if os.path.isdir(os.path.join(SIM_DIR, name))
             and name not in ["build", "common"]]
    
    if not tests:
        print("No tests found.")
        sys.exit(1)

    for test in tests:
        print(f"Running {test}: ", end="")
        process = subprocess.run(["python", __file__, "-t", test], stdout=subprocess.PIPE, text=True)
        error_count = process.stdout.lower().count("error")
        
        if error_count == 0:
            print(colorama.Fore.GREEN + "PASSED")
        else:
            print(colorama.Fore.GREEN + "FAILED")
    sys.exit(0)

# Argument parsing
parser = argparse.ArgumentParser(description="Run Vivado simulations outside Vivado for faster execution.")
parser.add_argument("-l", action="store_true", help="List available tests")
parser.add_argument("-t", type=str, help="Run the specified test")
parser.add_argument("-g", action="store_true", help="Show GUI (use with -t)")
parser.add_argument("-a", action="store_true", help="Run all available tests")

args = parser.parse_args()

if args.l:
    list_available_tests()
elif args.a:
    run_all()
elif args.t:
    execute_test(args.t, args.g)
else:
    parser.print_help()
    sys.exit(1)
