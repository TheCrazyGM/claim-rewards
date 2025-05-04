#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "hive-nectar",
#     "pyyaml",
#     "requests",
# ]
#
# [tool.uv.sources]
# hive-nectar = { git = "https://github.com/thecrazygm/hive-nectar/" }
# ///

"""
Hive-Engine SCOT Token Reward Claimer
-----------------------------------
This script connects to the Hive blockchain and Hive-Engine sidechain to claim SCOT token rewards
for multiple accounts using the authority (posting key) of a single main account.

Features:
- Connects to Hive nodes using a posting key from the environment, YAML config, or CLI.
- Fetches pending SCOT token rewards from the SCOT API for each account.
- Filters out tokens with zero pending rewards.
- Handles precision conversion for proper display of token amounts.
- Loops through accounts and claims rewards for each token with pending rewards.
- Uses the authority of the main account (the one whose posting key is provided).
- Provides informative logging and robust error handling.
- Supports dry-run mode to simulate claims without broadcasting.

Author: thecrazygm
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List

import requests
from nectar import Hive
from nectar.account import Account
from nectar.nodelist import NodeList

# ---------------------
# Logging configuration
# ---------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ----------------------
# SCOT API configuration
# ----------------------
SCOT_API_URL = "https://scot-api.hive-engine.com"


def redact_config(config: dict) -> dict:
    """
    Return a copy of config with sensitive fields redacted.

    Args:
        config (dict): The configuration dictionary to redact.

    Returns:
        dict: A copy of the config with sensitive fields redacted.
    """
    redacted = dict(config) if isinstance(config, dict) else {}
    for key in ["active_key", "posting_key", "wif", "private_key"]:
        if key in redacted:
            redacted[key] = "***REDACTED***"
    return redacted


def load_accounts_and_posting_key(accounts_path: str = None):
    """
    Load accounts list and posting key from YAML file.
    Args:
        accounts_path (str, optional): Path to YAML config file. If None, tries accounts.yaml in current directory.
    Returns:
        tuple: (list of account names, posting key)
    """
    import yaml

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


def get_posting_key(cli_posting_key: str = None, yaml_posting_key: str = None) -> str:
    """
    Retrieve and validate the posting key (private key) from CLI, YAML, or environment variables.
    Args:
        cli_posting_key (str, optional): Posting key from command-line argument.
        yaml_posting_key (str, optional): Posting key from YAML config.
    Returns:
        str: The posting key.
    """
    logger.debug(
        f"Attempting to retrieve posting key (cli_posting_key provided: {bool(cli_posting_key)}, yaml_posting_key provided: {bool(yaml_posting_key)})"
    )
    if cli_posting_key:
        logger.info("Using posting key from --posting-key argument.")
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
            "Posting key must be provided via --posting-key, YAML config, or POSTING_KEY env variable."
        )
        sys.exit(1)
    logger.debug("Posting key successfully retrieved.")
    return posting_key


def connect_to_hive(posting_key: str) -> Hive:
    """
    Establish a connection to the Hive blockchain using the provided posting key.
    Automatically selects the best available Hive nodes.
    Args:
        posting_key (str): The posting private key.
    Returns:
        Hive: A connected Hive blockchain instance.
    """
    try:
        logger.debug("Initializing NodeList and updating nodes...")
        nodelist = NodeList()
        nodelist.update_nodes()
        nodes = nodelist.get_hive_nodes()
        logger.debug(f"Selected Hive nodes: {nodes}")
        hive = Hive(keys=[posting_key], node=nodes)
        logger.debug("Hive instance created and connected.")
        return hive
    except Exception as e:
        logger.error(f"Failed to connect to Hive: {e}")
        sys.exit(1)


def format_token_amount(amount: float, precision: int) -> str:
    """
    Format a token amount with the correct precision.

    Args:
        amount (float): The token amount.
        precision (int): The token precision.

    Returns:
        str: Formatted token amount as a string.
    """
    format_str = f"{{:.{precision}f}}"
    return format_str.format(amount)


def get_scot_rewards(account_name: str) -> List[Dict[str, Any]]:
    """
    Fetch SCOT token rewards for a given account from the SCOT API.
    Args:
        account_name (str): The Hive account name to fetch rewards for.
    Returns:
        List[Dict[str, Any]]: List of tokens with pending rewards, with amounts properly formatted.
    """
    try:
        logger.debug(f"Fetching SCOT rewards for {account_name}")
        url = f"{SCOT_API_URL}/@{account_name}"
        response = requests.get(url, params={"hive": 1}, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Filter tokens with pending rewards > 0
        pending_rewards = []
        for symbol, token_data in data.items():
            if token_data.get("pending_token", 0) > 0:
                precision = token_data.get("precision", 0)
                pending_amount = token_data.get("pending_token", 0) / (10**precision)
                staked_amount = token_data.get("staked_tokens", 0) / (10**precision)

                pending_rewards.append(
                    {
                        "symbol": symbol,
                        "pending": format_token_amount(pending_amount, precision),
                        "staked": format_token_amount(staked_amount, precision),
                        "precision": precision,
                        "raw_pending": token_data.get("pending_token", 0),
                    }
                )

        return pending_rewards
    except Exception as e:
        logger.error(f"Error fetching SCOT rewards for {account_name}: {e}")
        return []


def claim_scot_rewards_for_account(
    hive: Hive, account_name: str, main_account_name: str, dry_run: bool = False
) -> bool:
    """
    Claim SCOT token rewards for a single account using the posting authority of the main account.
    Args:
        hive (Hive): The connected Hive blockchain instance.
        account_name (str): The account to claim rewards for.
        main_account_name (str): The account whose posting key is used for authority.
        dry_run (bool): If True, only simulate the claim, do not broadcast.
    Returns:
        bool: Whether the claim operation was successful.
    """
    try:
        rewards = get_scot_rewards(account_name)

        if not rewards:
            logger.info(f"[{account_name}] No SCOT token rewards to claim.")
            return True

        # Prepare the list of tokens to claim
        tokens_to_claim = []
        for token in rewards:
            logger.info(
                f"[{account_name}] {token['symbol']} rewards to claim: {token['pending']}"
            )
            tokens_to_claim.append({"symbol": token["symbol"]})

        if dry_run:
            for token in rewards:
                logger.info(
                    f"[DRY RUN] Would claim {token['pending']} {token['symbol']} for {account_name} using authority of {main_account_name}."
                )
            return True

        # Create the custom_json operation
        logger.debug(
            f"Creating custom_json operation to claim SCOT rewards for {account_name}"
        )

        # Get the main account to use for posting authority
        Account(main_account_name, blockchain_instance=hive)

        # Broadcast the custom_json operation
        custom_json_data = {
            "id": "scot_claim_token",
            "required_posting_auths": [main_account_name],
            "required_auths": [],
            "json": json.dumps(tokens_to_claim),
        }

        logger.debug(f"Custom JSON data: {custom_json_data}")

        # Broadcast the transaction
        tx = hive.custom_json(**custom_json_data)

        logger.info(
            f"[{account_name}] SCOT rewards claimed successfully using authority of {main_account_name}."
        )
        logger.debug(f"Transaction details: {tx}")

        return True
    except Exception as e:
        import traceback

        logger.error(
            f"Error claiming SCOT rewards for {account_name} using {main_account_name}: {type(e).__name__}: {e}"
        )
        logger.debug(traceback.format_exc())
        return False


def claim_scot_rewards_for_all_accounts(
    hive: Hive, accounts: list[str], main_account_name: str, dry_run: bool = False
) -> None:
    """
    Claim SCOT token rewards for all accounts in the list using the posting authority of the main account.
    This function loops through each account and claims any pending SCOT token rewards.
    Args:
        hive (Hive): The connected Hive blockchain instance.
        accounts (list[str]): List of account names to claim rewards for.
        main_account_name (str): The account whose posting key is used for authority.
        dry_run (bool): If True, only simulate the claims, do not broadcast.
    """
    logger.debug(f"Account list to process: {accounts}")
    for account_name in accounts:
        try:
            logger.debug(f"Processing account: {account_name}")
            claim_scot_rewards_for_account(hive, account_name, main_account_name, dry_run)
        except Exception as e:
            import traceback
            logger.error(
                f"Error processing account {account_name}: {type(e).__name__}: {e}"
            )
            logger.debug(traceback.format_exc())


def main():
    """
    Main entry point for the Hive-Engine SCOT Token Reward Claimer script.
    Parses command-line arguments, loads the posting key, connects to Hive,
    and claims SCOT token rewards for all accounts in the configuration.
    """
    parser = argparse.ArgumentParser(
        description="Claim Hive-Engine SCOT token rewards for multiple accounts."
    )
    parser.add_argument(
        "-w",
        "--posting-key",
        type=str,
        default=None,
        help="Posting key (private key) for authority account. If omitted, uses POSTING_KEY env variable or YAML config.",
    )
    parser.add_argument(
        "-a",
        "--accounts",
        type=str,
        default=None,
        help="Path to YAML file with accounts and/or posting key. If omitted, uses accounts.yaml if available.",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Simulate reward claims without broadcasting transactions.",
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()

    logger.debug(f"Parsed CLI arguments: {args}")

    # Set logging level if debug flag is used
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled.")

    # Load accounts list and posting key from YAML file or fallback
    accounts, yaml_posting_key = load_accounts_and_posting_key(args.accounts)
    # Retrieve the posting key from CLI, YAML, or environment
    posting_key = get_posting_key(args.posting_key, yaml_posting_key)
    # Connect to the Hive blockchain
    logger.debug("Connecting to Hive blockchain...")
    hive = connect_to_hive(posting_key)
    # Use the first account in the list as the authority
    main_account_name = accounts[0]
    logger.debug(f"Using main authority account: {main_account_name}")
    # Claim SCOT rewards for all listed accounts
    claim_scot_rewards_for_all_accounts(hive, accounts, main_account_name, dry_run=args.dry_run)


if __name__ == "__main__":
    # Script entry point. Handles any uncaught exceptions gracefully.
    try:
        main()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
