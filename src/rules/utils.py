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

"""Utility functions for rule processing."""

import logging
import json
import base64
from typing import Any
import string


def sanitize_binary_fields(data: Any) -> Any:
    """
    Recursively traverse a JSON-like structure and Base64-encode any
    field that contains non-UTF-8-safe characters.

    Args:
        data (Any): The JSON-like structure (dict, list, or str).

    Returns:
        Any: The sanitized structure with binary fields encoded.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = sanitize_binary_fields(value)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            data[i] = sanitize_binary_fields(item)
    elif isinstance(data, str):
        text_chars = (
            string.ascii_letters
            + string.digits
            + string.punctuation
            + string.whitespace
        )

        if all(c in text_chars for c in data):
            data.encode("utf-8")
        else:
            # Contains non-UTF-8-safe characters, encode to Base64
            data_bytes = data.encode("latin1", errors="ignore")
            data = base64.b64encode(data_bytes).decode("ascii")
    return data


def safe_json_load(logger: logging.Logger, raw_data: bytes | str) -> dict:
    """
    Convert raw bytes to a JSON object safely by replacing problematic patterns.

    Args:
        logger (logging.Logger): Logger for debug output.
        raw_data (bytes | str): The raw data to be converted.

    Returns:
        dict: The parsed JSON object.
    """
    try:
        if isinstance(raw_data, bytes):
            # string = raw_data.decode("ascii")
            string = raw_data.decode("latin-1")
        elif isinstance(raw_data, str):
            string = raw_data
        else:
            logger.debug(
                "Invalid data type for JSON loading: %s", type(raw_data)
            )
            return {}

        data = json.loads(string)
        data = sanitize_binary_fields(data)
        return data
    except Exception as e:
        logger.debug("Failed to parse and sanitize JSON: %s", e)
        return {}
