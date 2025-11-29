"""
Hive blockchain connectivity module.
Provides functions for connecting to the Hive blockchain and performing common operations.
"""

import logging

from nectar.hive import Hive

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
        logger.info("Connecting to Hive blockchain...")
        # Let Hive handle node initialization internally to avoid duplicate beacon calls
        hive = Hive(keys=[posting_key])
        logger.info("Connected to Hive blockchain.")
        return hive
    except Exception as e:
        logger.error(f"Failed to connect to Hive: {e}")
        raise
