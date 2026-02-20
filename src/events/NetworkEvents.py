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

"""Network Events for Multi-Server CI tests."""

from typing import Union
import asyncio
from functools import singledispatch
import logging

from python_on_whales import Network, Container, docker
from python_on_whales.exceptions import DockerException

ValidNetwork = Union[Network, str]
ValidContainer = Union[Container, str]

EVENTS_MAP = {}  # A mapping of event names to their functions.


@singledispatch
def disconnect(network: ValidNetwork, targets: list[ValidContainer]) -> None:
    """
    Simulate network disconnection.

    Args:
        network (ValidNetwork): The network to disconnect from.
        targets (list[ValidContainer]): List of valid containers to disconnect.
    """
    for target in targets:
        docker.network.disconnect(network, target)


@disconnect.register
def _(network: ValidNetwork, source: ValidContainer) -> None:
    """
    Simulate network disconnection.

    Args:
        network (ValidNetwork): The network to disconnect from.
        source (ValidContainer): The valid container to disconnect.
    """
    docker.network.disconnect(network, source)


@disconnect.register
async def _(
    network: ValidNetwork, targets: list[ValidContainer], timeout: int
) -> None:
    """
    Simulate network disconnection with a timeout.

    Args:
        network (ValidNetwork): The network to disconnect from.
        targets (list[ValidContainer]): List of valid containers to disconnect.
        timeout (int): Time in seconds to wait before reconnecting.
    """
    for target in targets:
        docker.network.disconnect(network, target)

    await asyncio.sleep(timeout)
    reconnect(network, targets)


@disconnect.register
async def _(
    network: ValidNetwork, source: ValidContainer, timeout: int
) -> None:
    """
    Simulate network disconnection with a timeout.

    Args:
        network (ValidNetwork): The network to disconnect from.
        source (ValidContainer): The valid container to disconnect.
        timeout (int): Time in seconds to wait before reconnecting.
    """
    await disconnect(network, source, timeout=timeout)


EVENTS_MAP.update({"disconnect": disconnect, "network_disconnect": disconnect})


def reconnect(network: ValidNetwork, targets: list[ValidContainer]) -> None:
    """
    Simulate network reconnection.

    Args:
        network (ValidNetwork): The network to reconnect to.
        targets (list[ValidContainer]): List of valid containers to reconnect.
    """
    for target in targets:
        docker.network.connect(network, target)


EVENTS_MAP.update({"reconnect": reconnect, "network_reconnect": reconnect})


def packet_loss(
    source: ValidContainer, interface: str, loss: float, logger: logging.Logger
) -> None:
    """
    Simulate packet loss on specified containers.

    Args:
        targets (list[ValidContainer]): List of valid containers to apply packet loss.
        interface (str): The network interface to apply packet loss on.
        loss (float): Percentage of packet loss to simulate.
    """
    docker.execute(
        source,
        [
            "bash",
            "-c",
            f"tc qdisc replace dev {interface} root netem loss {loss}%",
        ],
        detach=True,
    )

    # Verify that the packet loss is applied
    result = docker.execute(
        source,
        ["tc", "qdisc", "show", "dev", interface],
        detach=False,
    )

    if f"loss {loss}%" not in result:
        logger.error(
            f"Failed to verify packet loss on {source} ({interface})."
        )
        logger.debug(f"tc output:\n{result}")
        return

    logger.debug(f"Applied {loss}% packet loss on {source} ({interface})")
    return


EVENTS_MAP.update({"packet_loss": packet_loss})


def get_events() -> dict[str, callable]:
    """
    Returns a dictionary of available network events that can be performed on containers.

    Returns:
        dict[str, callable]: A dictionary mapping event names to their corresponding functions.
    """
    return EVENTS_MAP
