"""Copyright (C) 2026 Network RADIUS SAS (legal@networkradius.com)

This software may not be redistributed in any form without the prior
written consent of Network RADIUS.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE."""

"""
Setup utils for creating directories and such
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional


def setup_virtualenv(
    venv_path: Path, requirements_file: Optional[Path] = None
) -> None:
    """
    Sets up a Python virtual environment and installs dependencies.

    Args:
        venv_path (Path): The path where the virtual environment will be created.
        requirements_file (Optional[Path]): The path to the requirements file. If None, defaults
            to 'requirements.txt' in the current directory.
    """
    # If a venv already exists (likely), skip creation
    if venv_path.exists():
        print(f"Virtual environment at {venv_path} already exists. Skipping creation.")
        return

    if requirements_file is None:
        requirements_file = Path("requirements.txt")

    # Create virtual environment
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)

    # Activate virtual environment and install dependencies
    activate_script = venv_path / "bin" / "activate"

    # Empty the log file before installation
    with open("config.log", "w", encoding="utf-8") as log_file:
        log_file.write("")

    command = f"source {activate_script} && pip install -r {requirements_file} -q --log config.log"
    subprocess.run(command, shell=True, executable="/bin/bash", check=True)


def create_util_script() -> None:
    """
    Creates a utility script to activate the virtual environment.
    """
    script_content = """apt-get install -y iputils-ping iproute2 ipcalc
IP_CIDR=$(ip -o -f inet addr show eth0 | awk '{print $4}')
TEST_SUBNET=$(ipcalc -n "$IP_CIDR" | grep Network | awk '{print $2}')
export TEST_SUBNET
echo "TEST_SUBNET=$TEST_SUBNET" >> /etc/environment
echo "Detected TEST_SUBNET: $TEST_SUBNET"
"""

    # Create the freeradius directory if it doesn't exist
    os.makedirs(Path("data", "freeradius"), exist_ok=True)

    with open(
        Path("data", "freeradius", "env-setup.sh"), "w", encoding="utf-8"
    ) as script_file:
        script_file.write(script_content)

    # Fix the permissions
    os.chmod(Path("data", "freeradius", "env-setup.sh"), 0o755)


def create_directory(path: Path) -> None:
    """
    Creates a directory if it does not exist.

    Args:
        path (Path): The path of the directory to create.
    """
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """
    Main function to set up the virtual environment and create necessary directories.
    """
    venv_path = Path(".venv")
    requirements_file = Path("requirements.txt")
    setup_virtualenv(venv_path, requirements_file)

    directories = ["data", "tests", "environments"]

    for dir_name in directories:
        dir_path = Path(dir_name)
        create_directory(dir_path)
        print(f"Created directory: {dir_path}")

    # Create the utility script
    create_util_script()
    print("Created utility script at data/freeradius/env-setup.sh")

if __name__ == "__main__":
    main()
