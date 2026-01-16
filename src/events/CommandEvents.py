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

"""Module for handling command events in a multi-server test environment."""

import logging
import re

from typing import Union
from python_on_whales import Container, docker

ValidContainer = Union[Container, str]

EVENTS_MAP = {}  # A mapping of event names to their functions.


def run_command(
    source: ValidContainer,
    command: str,
    logger: logging.Logger,
    test_name: str,
    detach: bool = False,
) -> None:
    """
    Execute a command in a specified container.

    Args:
        container (ValidContainer): The container to execute the command in.
        command (str): The command to execute.
        detach (bool, optional): Whether to run the command in detached mode. Defaults to False.

    Raises:
        python_on_whales.exceptions.NoSuchContainer: If the container does not exist.
    """

    # Using regex, search the command for any ${container_name} patterns and replace them
    # with the actual container name using the docker compose project name as a prefix.
    pattern = re.compile(r"\$\{([a-zA-Z0-9_-]+)\}")
    matches = pattern.findall(command)
    for match in matches:
        full_container_name = f"{test_name}-{match}-1"
        command = command.replace(f"${{{match}}}", full_container_name)

    logger.debug("Running command in %s: %s", source, command)
    docker.execute(source, ["bash", "-c", command], detach=detach)


EVENTS_MAP.update(
    {
        "run_command": run_command,
        "execute_command": run_command,
        "command": run_command,
    }
)


def get_events() -> dict[str, callable]:
    """
    Returns a dictionary of available events that can be performed on containers.

    Returns:
        dict[str, callable]: A dictionary mapping event names to their corresponding functions.
    """
    return EVENTS_MAP
