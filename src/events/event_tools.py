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
Tools for working with events.
"""

from pathlib import Path
from src import logging_helper

logger = logging_helper.get_logger()


def get_events() -> dict[str, callable]:
    """
    Retrieve available events from the events directory.

    Returns:
        dict[str, callable]: A dictionary mapping event names to their corresponding functions.
    """
    logger.debug("Loading events from events directory.")
    events = {}
    events_dir = Path(__file__).parent
    for event_file in events_dir.glob("*.py"):
        if event_file.name in [
            "__init__.py",
            "AbstractEvents.py",
            "event_tools.py",
        ]:
            continue

        module_name = f"src.events.{event_file.stem}"
        module = __import__(module_name, fromlist=[""])
        events.update(module.get_events())

    logger.debug("Loaded events: %s", list(events.keys()))
    return events
