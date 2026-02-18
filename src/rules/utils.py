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

import base64
import json
import logging


def safe_json_load(logger: logging.Logger, raw_data: bytes | str) -> dict:
    """
    Convert raw bytes to a JSON object safely by Base64-encoding any fields
    that contain non-UTF-8-safe characters.

    Args:
        logger (logging.Logger): Logger for debug output.
        raw_data (bytes | str): The raw data to be converted.

    Returns:
        dict: The parsed JSON object with binary fields encoded.
    """
    try:
        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode("latin1")  # preserves raw bytes

        data = json.loads(raw_data)

        def encode_octets(obj) -> None:
            if isinstance(obj, dict):
                if obj.get("type") == "octets" and "value" in obj:
                    value = obj["value"]

                    # Convert to bytes preserving raw content
                    if isinstance(value, str):
                        value_bytes = value.encode("latin1")
                    elif isinstance(value, bytes):
                        value_bytes = value
                    else:
                        logger.debug(
                            "Unexpected octets value type: %s", type(value)
                        )

                    obj["value"] = base64.b64encode(value_bytes).decode(
                        "ascii"
                    )
                else:
                    for v in obj.values():
                        encode_octets(v)
            elif isinstance(obj, list):
                for item in obj:
                    encode_octets(item)

        encode_octets(data)
        return data

    except Exception as e:
        logger.debug("Failed to parse and sanitize JSON: %s", e)
        return {}
