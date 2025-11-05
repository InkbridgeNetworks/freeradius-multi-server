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
