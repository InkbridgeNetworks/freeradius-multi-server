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

"""Module for RADIUS-related events in a multi-server CI environment."""

import logging
from typing import Union
from python_on_whales import Container, docker


ValidContainer = Union[Container, str]

EVENTS_MAP = {}  # A mapping of event names to their functions.


def access_request(
    source: ValidContainer,
    target: ValidContainer,
    secret: str,
    username: str,
    password: str,
    logger: logging.Logger,
) -> None:
    """
    Simulate a RADIUS access request.

    Args:
        container (ValidContainer): The container to execute the command in.
        command (str): The command to execute.

    Raises:
        python_on_whales.exceptions.NoSuchContainer: If the container does not exist.
    """
    logger.debug(
        "Sending RADIUS access request from %s to %s for user %s",
        source,
        target,
        username,
    )
    command = f"echo {password} | radtest {username} {password} {target} 0 {secret} || true"

    docker.execute(source, ["bash", "-c", command], detach=True)


EVENTS_MAP.update(
    {"access_request": access_request, "radius_request": access_request}
)


def get_events() -> dict[str, callable]:
    """
    Returns a dictionary of available RADIUS events.

    Returns:
        dict[str, callable]: A dictionary mapping event names to their corresponding functions.
    """
    return EVENTS_MAP
