"""
Hive blockchain connectivity module.
Provides functions for connecting to the Hive blockchain and performing common operations.
"""

import logging

from nectar import Hive
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
