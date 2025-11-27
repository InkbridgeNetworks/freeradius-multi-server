"""A listener to handle incoming messages from containers."""

from abc import ABC, abstractmethod
import asyncio
from enum import Enum
import logging
from pathlib import Path

from src import logging_helper

class ListenerType(Enum):
    """
    Enum for different listener types.
    """
    SOCKET = 0
    # Add other listener types as needed

class Listener(ABC):
    """
    An abstract base class for listeners that handle incoming messages.
    """

    listener_dest: Path
    msg_queue: asyncio.Queue
    ready_future: asyncio.Future
    logger: logging.Logger

    def __init__(
        self,
        listener_dest: Path,
        msg_queue: asyncio.Queue,
        ready_future: asyncio.Future,
        logger: logging.Logger = logging_helper.get_logger(),
    ) -> None:
        self.listener_dest = listener_dest
        self.msg_queue = msg_queue
        self.ready_future = ready_future
        self.logger = logger
        super().__init__()

    @abstractmethod
    async def start(self) -> None:
        """
        Starts the listener.
        """
        raise NotImplementedError(
            "start method must be implemented by subclasses."
        )

    # async def stop(self) -> bool:
    def stop(self) -> bool:
        """
        Stops and cleans up the listener.

        Returns:
            bool: True if the listener was successfully stopped and cleaned up, False otherwise.
        """
        if self.listener_dest.exists():
            try:
                self.logger.debug(
                    "Removing listener socket at %s", self.listener_dest
                )
                self.listener_dest.unlink()
                self.logger.info(
                    "Listener: Removed logging destination %s",
                    self.listener_dest,
                )
                return True
            except OSError as e:
                self.logger.error(
                    "Listener: Failed to remove logging destination %s: %s",
                    self.listener_dest,
                    e,
                )
                return False
        self.logger.info(
            "Listener: Logging destination %s does not exist, nothing to remove",
            self.listener_dest,
        )
        return True


class SocketListener(Listener):
    """
    A class to represent a listener that handles incoming messages from containers.
    """

    async def __handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """
        Handles incoming client connections and processes messages.

        Args:
            reader (asyncio.StreamReader): Reader for the incoming data.
            writer (asyncio.StreamWriter): Writer for sending responses.
        """
        self.logger.debug("Client connected.")
        try:
            while True:
                data = await reader.readuntil(b"\n")
                message = data.decode().strip()
                self.logger.debug("Received message: %s", message)

                trigger_name, trigger_value = message.split(" ", 1)

                self.msg_queue.put_nowait((trigger_name, trigger_value))
        except asyncio.IncompleteReadError:
            self.logger.debug("Client disconnected.")
        finally:
            writer.close()
            await writer.wait_closed()
            self.logger.debug("Client disconnected.")

    async def start(self) -> None:
        """
        Starts the listener server.
        """
        self.logger.debug("Starting listener on %s", self.listener_dest)

        if self.listener_dest.exists():
            # The path may be a directory if compose tried to mount it as a volume before
            # we created it
            self.logger.debug(
                "Socket path %s exists as a %s, removing it.",
                self.listener_dest,
                "directory" if self.listener_dest.is_dir() else "file",
            )
            if self.listener_dest.is_dir():
                self.listener_dest.rmdir()
            else:
                self.listener_dest.unlink()

        try:
            server = await asyncio.start_unix_server(
                self.__handle_connection,
                path=self.listener_dest,
            )

            # Make sure the socket is world writable so containers can connect
            self.listener_dest.chmod(0o777)
        except PermissionError as e:
            self.logger.error("Permission error starting listener: %s", e)
            return

        self.logger.debug("Listener started, setting ready future.")

        # Notify that the server is ready
        if not self.ready_future.done():
            self.ready_future.set_result(True)

        async with server:
            self.logger.debug("Listener running.")
            await server.serve_forever()
