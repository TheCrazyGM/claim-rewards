#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.13"
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
import logging
import os
import sys
from typing import Any

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
# Hive node configuration
# ----------------------
NODES_URL = [
    "https://api.syncad.com",
    "https://api.hive.blog",
]


# ---------------------------------
# List of accounts to claim rewards
# ---------------------------------
# The first account in this list is used as the authority (posting key must be for this account)
def load_accounts_and_wif(accounts_path: str = None):
    import os

    import yaml

    if accounts_path:
        try:
            with open(accounts_path, "r") as f:
                data = yaml.safe_load(f)
            logger.info(f"Loaded accounts and WIF from {accounts_path}")
            return data.get("accounts", []), data.get("wif")
        except Exception as e:
            logger.error(f"Failed to load accounts from {accounts_path}: {e}")
            sys.exit(1)
    # Try default accounts.yaml
    if os.path.exists("accounts.yaml"):
        try:
            with open("accounts.yaml", "r") as f:
                data = yaml.safe_load(f)
            logger.info("Loaded accounts and WIF from accounts.yaml")
            return data.get("accounts", []), data.get("wif")
        except Exception as e:
            logger.error(f"Failed to load accounts from accounts.yaml: {e}")
            sys.exit(1)
    logger.error(
        "No account list found. Please provide --accounts or create accounts.yaml in the current directory."
    )
    sys.exit(1)


def get_wif(cli_wif: str = None, yaml_wif: str = None) -> str:
    """
    Retrieve and validate the posting WIF (private key) from CLI, YAML, or environment variables.
    Args:
        cli_wif (str, optional): WIF from command-line argument.
        yaml_wif (str, optional): WIF from YAML config.
    Returns:
        str: The posting WIF.
    """
    logger.debug(
        f"Attempting to retrieve WIF (cli_wif provided: {bool(cli_wif)}, yaml_wif provided: {bool(yaml_wif)})"
    )
    if cli_wif:
        logger.info("Using WIF from --wif argument.")
        wif = cli_wif
    elif yaml_wif:
        logger.info("Using WIF from YAML config file.")
        wif = yaml_wif
    else:
        wif = os.getenv("POSTING_WIF")
        if wif:
            logger.info("Using WIF from POSTING_WIF environment variable.")
    if not wif:
        logger.error(
            "Posting WIF must be provided via --wif, YAML config, or POSTING_WIF env variable."
        )
        sys.exit(1)
    logger.debug("WIF successfully retrieved.")
    return wif


def claim_rewards(hive: Hive, account_name: str) -> None:
    """
    Claim rewards for a single Hive account using the provided Hive instance.
    This function is not used in the main loop, but demonstrates how to claim for one account.

    Args:
        hive (Hive): The connected Hive blockchain instance.
        account_name (str): The account to claim rewards for.
    """
    try:
        # Instantiate the account object
        account = Account(account_name, blockchain_instance=hive)
        # Print available attributes for debugging (useful for development)
        logger.debug(f"[{account_name}] Account attributes: {dir(account)}")

        # Get the reward balances using attribute access
        reward_hive = getattr(account, "reward_hive_balance", None)
        reward_hbd = getattr(account, "reward_hbd_balance", None)
        reward_vests = getattr(account, "reward_vesting_balance", None)

        # If any reward attribute is missing, warn and skip
        if None in (reward_hive, reward_hbd, reward_vests):
            logger.warning(
                f"[{account_name}] One or more reward attributes are missing: "
                f"reward_hive={reward_hive}, reward_hbd={reward_hbd}, reward_vests={reward_vests}"
            )
            return

        logger.info(f"[{account_name}] Today's rewards: {reward_hive} {reward_hbd} {reward_vests}")

        # Claim the rewards if there are any
        if any(
            getattr(reward, "amount", 0) > 0 for reward in [reward_hbd, reward_hive, reward_vests]
        ):
            account.claim_reward_balance()
            logger.info(f"[{account_name}] Rewards claimed successfully.")
        else:
            logger.info(f"[{account_name}] No rewards to claim.")
    except Exception as e:
        logger.error(f"Error claiming rewards for {account_name}: {e}")


def get_balance(account: Account) -> dict[str, Any]:
    """
    Retrieve and log the balances for a given Hive account.
    Args:
        account (Account): The Hive account object.
    Returns:
        dict[str, Any]: The account balances, or an empty dict on error.
    """
    try:
        balance = account.get_balances()
        logger.info(f"Current balances: {balance['available']}")
        return balance
    except Exception as e:
        logger.error(f"Error retrieving balance: {e}")
        return {}


def connect_to_hive(wif: str) -> Hive:
    """
    Establish a connection to the Hive blockchain using the provided posting WIF.
    Automatically selects the best available Hive nodes.
    Args:
        wif (str): The posting private key.
    Returns:
        Hive: A connected Hive blockchain instance.
    """
    try:
        logger.debug("Initializing NodeList and updating nodes...")
        nodelist = NodeList()
        nodelist.update_nodes()
        nodes = nodelist.get_hive_nodes()
        logger.debug(f"Selected Hive nodes: {nodes}")
        hive = Hive(keys=[wif], node=nodes)
        logger.debug("Hive instance created and connected.")
        return hive
    except Exception as e:
        logger.error(f"Failed to connect to Hive: {e}")
        sys.exit(1)


def claim_rewards_for_all_accounts(
    hive: Hive, accounts: list[str], main_account_name: str, dry_run: bool = False
) -> None:
    """
    Claim rewards for all accounts in the list using the authority of the main account.
    This function loops through each account, checks for outstanding rewards,
    and uses the main account's posting authority to claim them.
    Supports dry-run mode to simulate claims.

    Args:
        hive (Hive): The connected Hive blockchain instance.
        accounts (list[str]): List of account names to claim rewards for.
        main_account_name (str): The account whose posting key is used for authority.
        dry_run (bool): If True, only simulate the claim, do not broadcast.
    """
    logger.debug(f"Instantiating main account object for authority: {main_account_name}")
    main_account = Account(main_account_name, blockchain_instance=hive)
    logger.debug(f"Account list to process: {accounts}")
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
            else:
                logger.debug(
                    f"Calling main_account.claim_reward_balance(account={account_name})..."
                )
                main_account.claim_reward_balance(account=account_name)
                logger.info(
                    f"[{account_name}] Rewards claimed successfully using authority of {main_account_name}."
                )
        except Exception as e:
            import traceback

            logger.error(
                f"Error claiming rewards for {account_name} using {main_account_name}: {type(e).__name__}: {e}"
            )
            logger.error(traceback.format_exc())
            # Try to print account JSON for debugging if possible
            try:
                logger.debug(
                    f"{account_name} account json: {getattr(target_account, 'json', None)}"
                )
            except Exception:
                logger.debug(f"Could not retrieve account JSON for {account_name}")


def main():
    """
    Main entry point for the Hive reward claiming script.
    Parses command-line arguments, loads the posting key, connects to Hive, and claims rewards for all accounts.
    """
    parser = argparse.ArgumentParser(
        description="Claim Hive rewards for multiple accounts using one authority."
    )
    parser.add_argument(
        "--wif",
        type=str,
        default=None,
        help="Posting WIF (private key) for authority account. If omitted, uses POSTING_WIF env variable.",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate reward claims without broadcasting transactions.",
    )
    parser.add_argument(
        "--accounts",
        type=str,
        default=None,
        help="Path to YAML file with accounts and/or WIF. If omitted, uses accounts.yaml if available.",
    )
    args = parser.parse_args()

    logger.debug(f"Parsed CLI arguments: {args}")

    # Set logging level if debug flag is used
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled.")

    # Load accounts list and WIF from YAML file or fallback
    accounts, yaml_wif = load_accounts_and_wif(args.accounts)
    # Retrieve the posting WIF from CLI, YAML, or environment
    wif = get_wif(args.wif, yaml_wif)
    # Connect to the Hive blockchain
    logger.debug("Connecting to Hive blockchain...")
    hive = connect_to_hive(wif)
    # Use the first account in the list as the authority
    main_account_name = accounts[0]
    logger.debug(f"Using main authority account: {main_account_name}")
    # Claim rewards for all listed accounts
    claim_rewards_for_all_accounts(hive, accounts, main_account_name, dry_run=args.dry_run)


if __name__ == "__main__":
    # Script entry point. Handles any uncaught exceptions gracefully.
    try:
        main()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
