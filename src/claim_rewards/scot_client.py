"""
SCOT token operations module.
Provides functions for interacting with SCOT tokens on the Hive-Engine sidechain.
"""

import logging
from typing import Any, Dict, List

import requests
from nectar import Hive
from nectar.account import Account

logger = logging.getLogger(__name__)

# SCOT API configuration
SCOT_API_URL = "https://scot-api.hive-engine.com"


def format_token_amount(amount: float, precision: int) -> str:
    """
    Format a token amount with the correct precision.

    Args:
        amount: The token amount.
        precision: The token precision.

    Returns:
        Formatted token amount as a string.
    """
    if precision == 0:
        return str(int(amount))

    format_str = f"{{:.{precision}f}}"
    formatted = format_str.format(amount)

    # Remove trailing zeros after decimal point
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".") or "0"

    return formatted


def get_scot_rewards(account_name: str) -> List[Dict[str, Any]]:
    """
    Fetch SCOT token rewards for a given account from the SCOT API.

    Args:
        account_name: The Hive account name to fetch rewards for.

    Returns:
        List of tokens with pending rewards, with amounts properly formatted.
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
        hive: The connected Hive blockchain instance.
        account_name: The account to claim rewards for.
        main_account_name: The account whose posting key is used for authority.
        dry_run: If True, only simulate the claim, do not broadcast.

    Returns:
        Whether the claim operation was successful.
    """
    try:
        rewards = get_scot_rewards(account_name)

        if not rewards:
            logger.info(f"[{account_name}] No SCOT token rewards to claim.")
            return True

        # Prepare the list of tokens to claim
        tokens_to_claim = []
        for token in rewards:
            logger.info(f"[{account_name}] {token['symbol']} rewards to claim: {token['pending']}")
            tokens_to_claim.append({"symbol": token["symbol"]})

        if dry_run:
            for token in rewards:
                logger.info(
                    f"[DRY RUN] Would claim {token['pending']} {token['symbol']} for {account_name} using authority of {main_account_name}."
                )
            return True

        # Create the custom_json operation
        logger.debug(f"Creating custom_json operation to claim SCOT rewards for {account_name}")

        # Get the main account to use for posting authority
        Account(main_account_name, blockchain_instance=hive)

        # Broadcast the custom_json operation
        logger.debug(f"Broadcasting custom_json operation for {account_name}")

        # The nectar library expects json_data as a parameter, not json
        tx = hive.custom_json(
            id="scot_claim_token",
            json_data=tokens_to_claim,  # Direct JSON object, not a string
            required_posting_auths=[main_account_name],
        )

        logger.debug(f"Transaction details: {tx}")

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
