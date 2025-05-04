"""
Configuration handling for Hive reward claiming scripts.
Handles loading accounts and API keys from YAML files or environment variables.
"""

import logging
import os
import sys
from typing import List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


def load_accounts_and_posting_key(
    accounts_path: Optional[str] = None,
) -> Tuple[List[str], Optional[str]]:
    """
    Load accounts list and posting key from YAML file.

    Args:
        accounts_path: Path to YAML config file. If None, tries accounts.yaml in current directory.

    Returns:
        Tuple of (list of account names, posting key)

    Raises:
        SystemExit: If no account list is found or there's an error loading the file.
    """
    if accounts_path:
        try:
            with open(accounts_path, "r") as f:
                data = yaml.safe_load(f)
            logger.info(f"Loaded accounts and posting key from {accounts_path}")
            return data.get("accounts", []), data.get("posting_key")
        except Exception as e:
            logger.error(f"Failed to load accounts from {accounts_path}: {e}")
            sys.exit(1)

    # Try default accounts.yaml
    if os.path.exists("accounts.yaml"):
        try:
            with open("accounts.yaml", "r") as f:
                data = yaml.safe_load(f)
            logger.info("Loaded accounts and posting key from accounts.yaml")
            return data.get("accounts", []), data.get("posting_key")
        except Exception as e:
            logger.error(f"Failed to load accounts from accounts.yaml: {e}")
            sys.exit(1)

    logger.error(
        "No account list found. Please provide --accounts or create accounts.yaml in the current directory."
    )
    sys.exit(1)


def get_posting_key(
    cli_posting_key: Optional[str] = None, yaml_posting_key: Optional[str] = None
) -> str:
    """
    Retrieve and validate the posting key from CLI, YAML, or environment variables.

    Args:
        cli_posting_key: Posting key from command-line argument.
        yaml_posting_key: Posting key from YAML config.

    Returns:
        The posting key.

    Raises:
        SystemExit: If no posting key is found.
    """
    logger.debug(
        f"Attempting to retrieve posting key (cli_posting_key provided: {bool(cli_posting_key)}, "
        f"yaml_posting_key provided: {bool(yaml_posting_key)})"
    )

    if cli_posting_key:
        logger.info("Using posting key from --posting_key argument.")
        posting_key = cli_posting_key
    elif yaml_posting_key:
        logger.info("Using posting key from YAML config file.")
        posting_key = yaml_posting_key
    else:
        posting_key = os.getenv("POSTING_KEY")
        if posting_key:
            logger.info("Using posting key from POSTING_KEY environment variable.")

    if not posting_key:
        logger.error(
            "Posting key must be provided via --posting_key, YAML config, or POSTING_KEY env variable."
        )
        sys.exit(1)

    logger.debug("Posting key successfully retrieved.")
    return posting_key
