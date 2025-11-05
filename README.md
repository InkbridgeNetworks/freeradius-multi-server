# HOW-TO
To use this tool, first clone the repo and run `make configure` to setup the environment and install the dependencies.

## Docker Image
To use this tool, you first need to generate a docker image on your host by first stepping into the FreeRADIUS sub-module with `cd freeradius-server` and running `docker build -t fr-build-ubuntu22 -f scripts/docker/build/ubuntu22/Dockerfile .`.

Next, generate the compose and config files using `python3 -m src.config_builder example.yml.j2`.

## Example
To use the tool, run `make test-framework -- <ARGS>`. For example:
```
make test framework -- -v -t tests/foo.yml
```

# Command Arguments
`-h`, `--help` - Show help text.

`--compose` - Path to the Docker compose file or directory containing compose files to be used for testing. Defaults to the script source folder `environments/`.

`-c`, `--config` - Path to a configuration file. This file can contain the test configs, compose configs, or both, and can be in either yaml or jinja2 format.

`-t`, `--test` - Path to the test configuration file. Defaults to the directory named `tests/`.

`--filter` - Filter test logs by name. Format is a comma separated list of test names.

`-o`, `--output` - Path to output log file for test summaries. Defaults to `multi_server_test.log`.

`-s`, `--seed` - Numeric seed to use for shuffling random tests.

`--debug`, `-x` - Enable debug output.

`--verbose`, `-v` - Enable verbose logging. More "v"'s set a higher verbose level.

# Development
Development notes.

## Validation Rules
Want to help out and write more rules? Great! Here's how:

I have written the rule code to make implementing new rules very easy. Yay! To add a new rule, you first need to add a method to `src/rules/rules.py` to represent your rule. The method will need to match the signature `def <method_name>(logger: logging.Logger, string: str, **kwargs) -> bool`. For example:
```
def foo(x: str, logger: logging.Logger, string: str) -> bool:
        if string == x:
                return True
        return False
```

Then, to allow your rule to be used in the test framework, you will need to add it to the global map of known rules `RULES_MAP`:
```
RULES_MAP.update({"foo": foo, "example": foo})
```
This can be done on the next line after your rule method.

Note: You can add multiple aliases for your rule, but I would recommend adding the name of the method as a bare minimum.

## Events
New events can be added to the `src/events` directory. If there is no suitable events file for your new event, create one.

Similar to how new rules can be added, you write an event method and add it to the `EVENTS_MAP` global variable. The only requirement for the method is that it has a `logger: logging.Logger` parameter. For example:
```
def bar(x: int, source: ValidContainer, logger: logging.Logger) -> None:
        docker.execute(source, ["bash", "-c", f"echo {x}"], detach=False)

EVENTS_MAP.update({"bar": bar})
```

Note: If your event has a `source` parameter, the container the event is listed under will be passed to the event.