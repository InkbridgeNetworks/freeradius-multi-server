"""multi_server_test.py
This script is used to run tests for a multi-server setup in a CI environment.
It uses Docker Compose to set up the environment and runs tests against it.
"""

import asyncio
import argparse
import os
import signal
import sys
from pathlib import Path

from src import logging_helper
from src.states.state_tools import generate_states
from src.custom_test import (
    Test,
    create_test_logger,
)

DEBUG_LEVEL = 0
VERBOSE_LEVEL = 0

logging_helper.setup_logging()
logger = logging_helper.get_logger()


async def cleanup_and_shutdown() -> None:
    """
    Clean up the tasks by cancelling them all and waiting for them to finish.
    """
    logger.info("Shutting down the tests...")
    logger.debug("Cleaning up tasks and shutting down the event loop...")
    tasks = [
        task
        for task in asyncio.all_tasks()
        if task is not asyncio.current_task()
    ]
    for task in tasks:
        logger.debug("Cancelling task: %s", task.get_name())
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    logger.debug("Cleanup completed.")

    logger.debug("Stopping the event loop...")
    # Stop the event loop if it's running
    if asyncio.get_event_loop().is_running():
        asyncio.get_event_loop().stop()
    logger.debug("Event loop stopped.")


def build_tests(
    loop: asyncio.AbstractEventLoop,
    config: Path | dict,
    compose_file: Path,
    seed: int | None = None,
) -> list[Test]:
    """
    Build a list of Test objects from the configuration.

    Args:
        loop (asyncio.AbstractEventLoop): The event loop to use.
        config (Path | dict): Path to the configuration file/directory or a dictionary
          containing the config.
        compose_file (Path): Path to the Docker Compose file.
        seed (int | None): Seed for randomizing test states.

    Returns:
        list[Test]: List of Test objects.

    Raises:
        ValueError: If the configuration is invalid.
    """
    logger.debug("Building tests")

    tests = []

    if isinstance(config, Path) and config.is_dir():
        for test_file in config.glob("*.yml"):
            test_name = test_file.stem
            test_logger = create_test_logger(test_name, compose_file.stem)
            try:
                timeout, states = generate_states(
                    loop, test_file, test_name, test_logger, seed=seed
                )
                tests.append(
                    Test(
                        name=test_name,
                        states=states,
                        compose_file=compose_file,
                        timeout=timeout,
                        detail_level=VERBOSE_LEVEL,
                        loop=loop,
                        logger=test_logger,
                    )
                )
            except ValueError as e:
                # TODO: Log the error to the correct logger
                logger.error("Invalid configuration in %s: %s", test_file, e)
                logger.debug("Skipping invalid test configuration.")
    else:
        try:
            test_name = "custom_test"
            test_logger = create_test_logger(test_name, compose_file.stem)
            timeout, states = generate_states(
                loop, config, test_name, test_logger, seed=seed
            )
            tests.append(
                Test(
                    name=test_name,
                    states=states,
                    compose_file=compose_file,
                    timeout=timeout,
                    detail_level=VERBOSE_LEVEL,
                    loop=loop,
                    logger=test_logger,
                )
            )
        except ValueError as e:
            raise ValueError(f"Invalid configuration: {e}") from e

    return tests


async def run_tests(tests: list[Test]) -> None:
    """
    Run the provided tests.

    Args:
        tests (list[Test]): List of Test objects to run.
    """
    try:
        async with asyncio.TaskGroup() as tg:
            for test in tests:
                tg.create_task(test.run(VERBOSE_LEVEL >= 3))
    except Exception as e:
        logger.error("An error occurred while running tests: %s", e)

    logger.info("All tests completed.")


def main(compose_source: Path, configs: Path | dict, **kwargs) -> None:
    """
    Main function to run the multi-server tests.

    Args:
        compose_source (Path): Path to the Docker Compose file.
        configs (Path | dict): Path to the test configuration file or a dictionary
            containing the config.
        **kwargs: Additional keyword arguments.
    """
    # Run a test in an asynchronous event loop
    loop = asyncio.get_event_loop()

    try:
        # Add a signal handler to gracefully handle shutdown
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig, lambda: asyncio.create_task(cleanup_and_shutdown())
            )

        if compose_source.is_dir():
            # Run tests for each compose file in the directory
            for compose_file in compose_source.glob("*.yml"):
                logger.info("Running tests for compose file: %s", compose_file)

                # Generate the states from the config
                tests = build_tests(
                    loop, configs, compose_file, seed=kwargs.get("seed")
                )

                # Create the test task group
                test_task = loop.create_task(run_tests(tests))

                # Start the shutdown when the test completes
                test_task.add_done_callback(
                    lambda _: asyncio.create_task(cleanup_and_shutdown())
                )
        elif compose_source.is_file():
            # Generate the states from the config
            tests = build_tests(
                loop, configs, compose_source, seed=kwargs.get("seed")
            )

            # Create the test task group
            test_task = loop.create_task(run_tests(tests))

            # Start the shutdown when the test completes
            test_task.add_done_callback(
                lambda _: asyncio.create_task(cleanup_and_shutdown())
            )

        else:
            logger.error(
                "Invalid compose source: %s. Must be a file or directory.",
                compose_source,
            )
            return

        # Run the event loop until all tasks are complete
        loop.run_forever()
    except Exception as e:
        logger.error("An error occurred while running tests: %s", e)
    finally:
        logger.debug("Closing the event loop...")
        loop.close()

    logger.info("Multi-server tests completed.")


def parse_args(args=None, prog=__package__) -> argparse.Namespace:
    """
    Parses command line arguments for the main function.

    Args:
        args (list, optional): List of command line arguments. Defaults to None.
        prog (str, optional): Program name. Defaults to __package__.
    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Run Docker client with specified compose file.",
    )
    parser.add_argument(
        "--compose",
        type=Path,
        dest="compose_source",
        metavar="compose_source",
        help="Path to the Docker Compose file.",
        default=Path(Path.cwd(), "docker-compose.yml"),
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config_file",
        type=str,
        help="Path to the configuration file.",
        default=None,
    )
    parser.add_argument(
        "-t",
        "--test",
        dest="test",
        type=Path,
        help="Path to the test configuration file.",
        default=Path(Path.cwd(), "tests"),
    )
    parser.add_argument(
        "-d",
        "--data",
        dest="data_path",
        type=Path,
        help="Path to the data directory.",
        default=Path(
            os.getenv("DATA_PATH", str(Path(Path.cwd(), "data")))
        ),  # os.getenv wants a string, we want a Path at the end
    )
    parser.add_argument(
        "--filter",
        dest="filter",
        type=str,
        help="Filter test logs by name. Format is a comma separated list of test names.",
        default=None,
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        type=str,
        help="Path to output log file.",
        default=Path(Path.cwd(), "multi_server_test.log"),
    )
    parser.add_argument(
        "-s",
        "--seed",
        dest="seed",
        type=int,
        help="Random seed for shuffling test states.",
        default=None,
    )
    parser.add_argument(
        "--debug",
        "-x",
        dest="debug",
        action="count",
        help="Enable debug logging.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        dest="verbose",
        action="count",
        help="Enable verbose logging.",
    )
    return parser.parse_args(args)


def interface() -> None:
    """
    Interface function to parse arguments and run the main function.
    """
    parsed_args = parse_args()

    if parsed_args.debug:
        logging_helper.add_debug_logging()

        DEBUG_LEVEL = parsed_args.debug
        logger.info("Debug mode enabled. Debug level: %d", DEBUG_LEVEL)

    # Set the DATA_PATH environment variable based on the parsed argument
    if not parsed_args.data_path.exists():
        logger.error(
            "Data path %s does not exist.",
            parsed_args.data_path,
        )
        logger.info("Exiting.")
        sys.exit(1)
    logger.debug("Setting DATA_PATH to %s", parsed_args.data_path)
    os.environ["DATA_PATH"] = str(parsed_args.data_path)

    logging_helper.setup_file_logging(parsed_args.output)
    file_logger = logging_helper.get_file_logger()

    if parsed_args.verbose:
        VERBOSE_LEVEL = parsed_args.verbose
        logger.info("Verbose mode enabled. Verbose level: %d", VERBOSE_LEVEL)

    if parsed_args.filter:
        filter_names = [
            f"Test.{name.strip()}" for name in parsed_args.filter.split(",")
        ]

        # Add a filter to the logger to only show messages that contain the filter string
        logger.debug("Adding name filters %s", filter_names)

        logging_helper.add_name_filter(filter_names)
        logging_helper.add_message_filter(filter_names, logger_obj=file_logger)

        logger.info("Filtering logs by name: %s", parsed_args.filter)

    if parsed_args.config_file:
        try:
            # Generate the compose and test config files
            from src.config_builder import (
                generate_configs,
                write_yaml_to_file,
            )

            compose_configs, test_configs = generate_configs(
                Path(parsed_args.config_file)
            )
        except (FileNotFoundError, ValueError) as e:
            logger.error("Error generating config files: %s", e)
            sys.exit(1)

        if compose_configs:
            write_yaml_to_file(
                compose_configs,
                Path(Path.cwd(), "docker-compose.yml"),
            )
        if test_configs:
            main(
                compose_source=Path(Path.cwd(), "docker-compose.yml"),
                configs=test_configs,
                seed=parsed_args.seed,
            )
        else:
            main(
                compose_source=Path(Path.cwd(), "docker-compose.yml"),
                configs=parsed_args.test,
                seed=parsed_args.seed,
            )

    else:
        main(
            compose_source=parsed_args.compose_source,
            configs=parsed_args.test,
            seed=parsed_args.seed,
        )


if __name__ == "__main__":
    interface()
