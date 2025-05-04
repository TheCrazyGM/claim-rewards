"""
Hive blockchain connectivity module.
Provides functions for connecting to the Hive blockchain and performing common operations.
"""

import logging

from nectar import Hive
from nectar.account import Account
from nectar.nodelist import NodeList

logger = logging.getLogger(__name__)


def connect_to_hive(posting_key: str) -> Hive:
    """
    Establish a connection to the Hive blockchain using the provided posting key.
    Automatically selects the best available Hive nodes.

    Args:
        posting_key: The posting private key.

    Returns:
        A connected Hive blockchain instance.

    Raises:
        SystemExit: If connection fails.
    """
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


def claim_rewards(hive: Hive, account_name: str) -> bool:
    """
    Claim rewards for a single Hive account using the provided Hive instance.

    Args:
        hive: The connected Hive blockchain instance.
        account_name: The account to claim rewards for.

    Returns:
        True if rewards were claimed or there were none to claim, False on error.
    """
    try:
        # Instantiate the account object
        account = Account(account_name, blockchain_instance=hive)
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
            return False

        logger.info(f"[{account_name}] Today's rewards: {reward_hive} {reward_hbd} {reward_vests}")

        # Claim the rewards if there are any
        if any(
            getattr(reward, "amount", 0) > 0 for reward in [reward_hbd, reward_hive, reward_vests]
        ):
            account.claim_reward_balance()
            logger.info(f"[{account_name}] Rewards claimed successfully.")
            return True
        else:
            logger.info(f"[{account_name}] No rewards to claim.")
            return True
    except Exception as e:
        logger.error(f"Error claiming rewards for {account_name}: {e}")
        return False
