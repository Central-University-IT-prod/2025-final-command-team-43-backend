import logging
import os
import secrets
from collections.abc import MutableMapping
from typing import Any


def pytest_tavern_beta_before_every_test_run(test_dict: dict, variables: dict) -> None:
    variables["RUN_ID"] = secrets.token_hex(3)
    if "BASE_URL" not in os.environ:
        logging.warning(
            "The BASE_URL environment variable is not set. "
            "Defaulting to http://localhost:9000/api"
        )
        os.environ["BASE_URL"] = "http://localhost:9000/api"


def pytest_tavern_beta_before_every_request(request_args: MutableMapping):
    message = f"Request: {request_args['method']} {request_args['url']}"

    params = request_args.get("params", None)
    if params:
        message += f"\nQuery parameters: {params}"

    message += f"\nRequest body: {request_args.get('json', '<no body>')}"

    logging.info(message)


def pytest_tavern_beta_after_every_response(expected: Any, response: Any) -> None:
    logging.info(f"Response: {response.status_code} {response.text}")
