#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "hive-nectar",
#     "pyyaml",
# ]
#
# ///
"""
Hive Multi-Account Reward Claimer
---------------------------------
This script connects to the Hive blockchain using the nectar library and claims rewards for multiple accounts using the authority (posting key) of a single main account.

Features:
- Connects to Hive nodes using a posting key from the environment.
- Loops through a list of Hive accounts and claims any outstanding rewards for each.
- Uses the authority of the main account (the one whose posting key is provided) to claim rewards for all listed accounts.
- Provides informative logging and robust error handling.

Author: thecrazygm
"""

import argparse
import sys
import traceback
from typing import List

from claim_rewards.config import get_posting_key, load_accounts_and_posting_key
from claim_rewards.hive_client import connect_to_hive
from claim_rewards.logging_setup import set_debug_logging, setup_logging

# Set up logging
logger = setup_logging()


def claim_rewards_for_all_accounts(
    accounts: List[str], main_account_name: str, posting_key: str, dry_run: bool = False
) -> None:
    """
    Claim rewards for all accounts in the list using the authority of the main account.

    Args:
        accounts: List of account names to claim rewards for.
        main_account_name: The account whose posting key is used for authority.
        posting_key: The posting key for the main account.
        dry_run: If True, only simulate the claim, do not broadcast.
    """
    logger.info(
        f"Claiming rewards for {len(accounts)} accounts using {main_account_name} authority"
    )

    # Connect to Hive blockchain
    try:
        hive = connect_to_hive(posting_key)
    except Exception as e:
        logger.error(f"Failed to connect to Hive blockchain: {e}")
        return

    # Instantiate the main account for authority
    logger.debug(f"Instantiating main account object for authority: {main_account_name}")
    try:
        from nectar.account import Account

        main_account = Account(main_account_name, blockchain_instance=hive)
    except Exception as e:
        logger.error(f"Error loading main account {main_account_name}: {e}")
        return

    logger.debug(f"Account list to process: {accounts}")

    # Process each account in the list
    success_count = 0
    for account_name in accounts:
        try:
            logger.debug(f"Processing account: {account_name}")
            # Instantiate the target account object
            target_account = Account(account_name, blockchain_instance=hive)
            logger.debug(f"[{account_name}] Target account instantiated.")

            # Get the reward balances using the nectar property
            rewards = getattr(target_account, "reward_balances", [])
            logger.debug(f"[{account_name}] reward_balances property: {rewards}")

            # If there are no rewards, skip
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
                logger.debug(
                    f"Calling main_account.claim_reward_balance(account={account_name})..."
                )
                main_account.claim_reward_balance(account=account_name)
                logger.info(
                    f"[{account_name}] Rewards claimed successfully using authority of {main_account_name}."
                )
                success_count += 1

        except Exception as e:
            logger.error(f"Error processing account {account_name}: {type(e).__name__}: {e}")
            logger.debug(traceback.format_exc())
            # Try to print account JSON for debugging if possible
            try:
                logger.debug(
                    f"{account_name} account json: {getattr(target_account, 'json', None)}"
                )
            except Exception:
                logger.debug(f"Could not retrieve account JSON for {account_name}")

    logger.info(f"Successfully processed {success_count} out of {len(accounts)} accounts")


def main() -> None:
    """
    Main entry point for the Hive reward claiming script.
    Parses command-line arguments, loads the posting key, connects to Hive, and claims rewards for all accounts.
    """
    # Parse command-line arguments
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

    # Claim rewards for all listed accounts
    claim_rewards_for_all_accounts(accounts, main_account_name, posting_key, dry_run=args.dry_run)


if __name__ == "__main__":
    # Script entry point. Handles any uncaught exceptions gracefully.
    try:
        main()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
