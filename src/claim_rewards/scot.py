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
import sys
import traceback

from claim_rewards.config import get_posting_key, load_accounts_and_posting_key
from claim_rewards.hive_client import connect_to_hive
from claim_rewards.logging_setup import set_debug_logging, setup_logging
from claim_rewards.scot_client import claim_scot_rewards_for_account

# Set up logging
logger = setup_logging()


def claim_scot_rewards_for_all_accounts(accounts, main_account_name, posting_key, dry_run=False):
    """
    Claim SCOT token rewards for all accounts in the list using the posting authority of the main account.

    Args:
        accounts: List of account names to claim rewards for.
        main_account_name: The account whose posting key is used for authority.
        posting_key: The posting key for the main account.
        dry_run: If True, only simulate the claims, do not broadcast.
    """
    logger.info(
        f"Claiming SCOT rewards for {len(accounts)} accounts using {main_account_name} authority"
    )

    # Connect to Hive blockchain
    try:
        hive = connect_to_hive(posting_key)
    except Exception as e:
        logger.error(f"Failed to connect to Hive blockchain: {e}")
        return

    # Process each account in the list
    logger.debug(f"Account list to process: {accounts}")
    success_count = 0
    for account_name in accounts:
        logger.debug(f"Processing account: {account_name}")

        try:
            if claim_scot_rewards_for_account(hive, account_name, main_account_name, dry_run):
                success_count += 1
        except Exception as e:
            logger.error(f"Error processing account {account_name}: {type(e).__name__}: {e}")
            logger.debug(traceback.format_exc())

    logger.info(f"Successfully processed {success_count} out of {len(accounts)} accounts")


def main():
    """
    Main entry point for the Hive-Engine SCOT Token Reward Claimer script.
    Parses command-line arguments, loads the posting key, connects to Hive,
    and claims SCOT token rewards for all accounts in the configuration.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Claim SCOT token rewards for multiple Hive accounts using a single posting key"
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
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate claiming rewards without broadcasting",
    )
    args = parser.parse_args()

    # Set logging level if debug flag is used
    if args.debug:
        set_debug_logging(logger)

    # Load accounts list and posting key from YAML file or fallback
    accounts, yaml_posting_key = load_accounts_and_posting_key(args.accounts)

    # Ensure we have at least one account
    if not accounts:
        logger.error("No accounts found in configuration")
        sys.exit(1)

    # Retrieve the posting key from CLI, YAML, or environment
    posting_key = get_posting_key(args.posting_key, yaml_posting_key)

    # Use the first account in the list as the authority
    main_account_name = accounts[0]
    logger.debug(f"Using main authority account: {main_account_name}")

    # Claim SCOT rewards for all listed accounts
    claim_scot_rewards_for_all_accounts(
        accounts, main_account_name, posting_key, dry_run=args.dry_run
    )


if __name__ == "__main__":
    # Script entry point. Handles any uncaught exceptions gracefully.
    try:
        main()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
