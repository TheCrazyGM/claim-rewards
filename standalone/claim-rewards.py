#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "hive-nectar",
#     "pyyaml",
#     "rich",
# ]
#
# [tool.uv.sources]
# hive-nectar = { git = "https://github.com/thecrazygm/hive-nectar" }
# ///
"""
Hive Multi-Account Reward Claimer
---------------------------------
This script connects to the Hive blockchain using the nectar library and claims rewards for multiple accounts using the authority (posting key) of a single main account.

Features:
- Connects to Hive nodes using a posting key from the environment or YAML or CLI argument.
- Loops through a list of Hive accounts and claims any outstanding rewards for each.
- Uses the authority of the main account (the one whose posting key is provided) to claim rewards for all listed accounts.
- Provides informative logging and robust error handling.
"""

import argparse
import logging
import os
import sys
import traceback
from typing import List, Optional, Tuple

import yaml
from nectar import Hive
from nectar.account import Account
from nectar.nodelist import NodeList
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback

# Logging setup functions


def setup_logging(level: Optional[int] = None) -> logging.Logger:
    logger = logging.getLogger()
    for handler in logger.handlers:
        logger.removeHandler(handler)
    install_rich_traceback()
    logging.basicConfig(
        level=level or logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_time=True)],
    )
    return logger


def set_debug_logging(logger: logging.Logger) -> None:
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug logging enabled.")


# Configure root logger
logger = setup_logging()

# Configuration functions


def load_accounts_and_posting_key(
    accounts_path: Optional[str] = None,
) -> Tuple[List[str], Optional[str]]:
    if accounts_path:
        try:
            with open(accounts_path, "r") as f:
                data = yaml.safe_load(f)
            logger.info(f"Loaded accounts and posting key from {accounts_path}")
            return data.get("accounts", []), data.get("posting_key")
        except Exception as e:
            logger.error(f"Failed to load accounts from {accounts_path}: {e}")
            sys.exit(1)
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


# Hive client functions


def connect_to_hive(posting_key: str) -> Hive:
    try:
        logger.debug("Initializing NodeList and updating nodes...")
        nodelist = NodeList()
        nodelist.update_nodes()
        nodes = nodelist.get_hive_nodes()
        logger.info(f"Connecting to Hive nodes: {nodes}")
        hive = Hive(keys=[posting_key], node=nodes)
        logger.info("Connected to Hive blockchain.")
        return hive
    except Exception as e:
        logger.error(f"Failed to connect to Hive: {e}")
        raise


# Reward claiming logic


def claim_rewards_for_all_accounts(
    accounts: List[str], main_account_name: str, posting_key: str, dry_run: bool = False
) -> None:
    logger.info(
        f"Claiming rewards for {len(accounts)} accounts using {main_account_name} authority"
    )
    try:
        hive = connect_to_hive(posting_key)
    except Exception as e:
        logger.error(f"Failed to connect to Hive blockchain: {e}")
        return

    try:
        main_account = Account(main_account_name, blockchain_instance=hive)
    except Exception as e:
        logger.error(f"Error loading main account {main_account_name}: {e}")
        return

    success_count = 0
    for account_name in accounts:
        try:
            target_account = Account(account_name, blockchain_instance=hive)
            rewards = getattr(target_account, "reward_balances", [])
            if not rewards or all(getattr(r, "amount", 0) == 0 for r in rewards):
                logger.info(f"[{account_name}] No rewards to claim.")
                continue
            logger.info(f"[{account_name}] Rewards to claim: {rewards}")
            if dry_run:
                logger.info(
                    f"[DRY RUN] Would claim rewards for {account_name} using authority of {main_account_name}."
                )
                logger.debug(
                    f"[DRY RUN] main_account.claim_reward_balance(account={account_name}) would be called here."
                )
                success_count += 1
            else:
                main_account.claim_reward_balance(account=account_name)
                logger.info(
                    f"[{account_name}] Rewards claimed successfully using authority of {main_account_name}."
                )
                success_count += 1
        except Exception as e:
            logger.error(f"Error processing account {account_name}: {type(e).__name__}: {e}")
            logger.debug(traceback.format_exc())
            try:
                logger.debug(
                    f"{account_name} account json: {getattr(target_account, 'json', None)}"
                )
            except Exception:
                logger.debug(f"Could not retrieve account JSON for {account_name}")
    logger.info(f"Successfully processed {success_count} out of {len(accounts)} accounts")


# Main CLI


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Claim rewards for multiple Hive accounts using a single posting key"
    )
    parser.add_argument(
        "-a",
        "--accounts",
        help="Path to YAML file containing accounts list and optional posting key",
    )
    parser.add_argument(
        "-k",
        "--posting_key",
        help="Posting key for the main account (overrides YAML and environment)",
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate claiming rewards without broadcasting"
    )
    args = parser.parse_args()
    if args.debug:
        set_debug_logging(logger)
    accounts, yaml_posting_key = load_accounts_and_posting_key(args.accounts)
    if not accounts:
        logger.error("No accounts found in configuration")
        sys.exit(1)
    posting_key = get_posting_key(args.posting_key, yaml_posting_key)
    main_account_name = accounts[0]
    logger.debug(f"Using main authority account: {main_account_name}")
    claim_rewards_for_all_accounts(accounts, main_account_name, posting_key, dry_run=args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
