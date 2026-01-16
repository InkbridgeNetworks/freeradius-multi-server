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
Module for code events in a multi-server CI environment.
"""

import logging
from typing import Union
from python_on_whales import Container, Network

ValidContainer = Union[Container, str]
ValidNetwork = Union[Network, str]

EVENTS_MAP = {}  # A mapping of event names to their functions.


def code(block: str, source: ValidContainer, logger: logging.Logger) -> None:
    """
    Execute a block of code for an event.

    Args:
        block (str): The code block to execute.
        source (ValidContainer): The container to execute the code in.
        logger (logging.Logger): Logger for debug output.
    """
    # TODO: Implement code safety checks before execution
    logger.debug("Executing code block for event.")

    indented_block = "\n".join(f"    {line}" for line in block.splitlines())
    wrapped_code = f"def _event_func():\n{indented_block}"

    local_vars = {"source": source, "logger": logger}
    try:
        exec(wrapped_code, local_vars)
        local_vars.get("_event_func", lambda: None)()
        logger.debug("Code block executed successfully.")
    except Exception as e:
        logger.error("Error executing code block: %s", e)


EVENTS_MAP.update({"code": code})


def get_events() -> dict[str, callable]:
    """
    Returns a dictionary of available code events.

    Returns:
        dict[str, callable]: A dictionary mapping event names to their corresponding functions.
    """
    return EVENTS_MAP
