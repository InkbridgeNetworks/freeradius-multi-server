"""
Tools to build rules from conditions and parameters.
"""

import logging
from src.rules import rules

from src import logging_helper


def build_rule(
    condition: str, params: dict, logger: logging.Logger
) -> callable:
    """
    Build a rule function that can be used to validate events.

    Args:
        condition (str): The condition to build the rule for.
        params (dict): The parameters for the condition.
        logger (logging.Logger): Logger for debugging.

    Returns:
        callable: A function that takes a string and returns True if the rule passes, False otherwise.
    """
    known_rules = rules.rule_methods()
    controls = rules.control_methods()

    normalized_condition = condition.lower()
    normalized_condition = normalized_condition.removeprefix("may_")

    logger.debug("Normalized condition: %s", normalized_condition)

    if normalized_condition in known_rules:
        func = known_rules[normalized_condition]
        rule_params = params

        # TODO: Should the test l
        method = lambda x: func(
            **rule_params, logger=logging_helper.get_logger(), string=x
        )
        method.rule_params = rule_params

        if normalized_condition == "code":
            method.friendly_str = f"{condition.lower()}: code block"
        else:
            method.friendly_str = f"{condition.lower()}: {', '.join(f'{k}={v}' for k, v in rule_params.items())}"

        return method

    if normalized_condition in controls:
        func = controls[normalized_condition]

        methods = []

        for sub_condition in params.keys():
            logger.debug("Sub-condition: %s", sub_condition)
            methods.append(
                build_rule(sub_condition, params[sub_condition], logger)
            )

        logger.debug("Control methods: %s", methods)

        # TODO: Should the test logger be used here?
        method = lambda x: func(
            methods=methods, logger=logging_helper.get_logger(), string=x
        )
        method.rule_params = {"methods": methods}
        method.friendly_str = f"{condition.lower()}: {', '.join(m.friendly_str for m in methods)}"

        return method

    return lambda x: False


def generate_rules_map(state: dict, logger: logging.Logger) -> dict:
    """
    Generate a mapping of triggers to their corresponding validation functions.
    Returns:
        dict: A mapping of triggers to validation functions.
    """

    rules_map = {}
    for trigger in state.get("verify", {}).get("triggers", []):
        trigger_name = list(trigger.keys())[0]

        try:
            for condition in list(trigger.get(trigger_name, {})):
                logger.debug("Condition: %s", condition)
                if trigger_name not in rules_map:
                    rules_map[trigger_name] = []
                rules_map[trigger_name].append(
                    build_rule(
                        condition,
                        trigger.get(trigger_name, {}).get(condition, {}),
                        logger,
                    )
                )
                logger.debug(
                    "Added rule for trigger %s: %s", trigger_name, condition
                )
        except Exception as e:
            logger.error(
                "Error adding rule for trigger %s: %s", trigger_name, e
            )
            continue
    return rules_map
