# cooldown_manager.py
import asyncio
import logging
from typing import Dict

from logger_config import setup_logger

logger = setup_logger(__name__)


class ActionCooldownManager:
    def __init__(self, cooldown_period: float, cooldown_notify_queue_p1, cooldown_notify_queue_p2):
        """
        Initialize the cooldown manager with a specified cooldown period.

        :param cooldown_period: Time in seconds to prevent actions after a valid action is received.
        """
        self.cooldown_queue_p1 = cooldown_notify_queue_p1
        self.cooldown_queue_p2 = cooldown_notify_queue_p2
        self.cooldown_period = cooldown_period
        self.player_locks: Dict[int, asyncio.Lock] = {}
        logger.info(
            f"Cooldown Manager Initialized Successfully: Action cooldown period set to {self.cooldown_period} seconds.")

    def get_lock(self, player_id: int) -> asyncio.Lock:
        """
        Retrieve the lock associated with a player. Create one if it doesn't exist.

        :param player_id: The ID of the player.
        :return: An asyncio.Lock object.
        """
        if player_id not in self.player_locks:
            self.player_locks[player_id] = asyncio.Lock()
        return self.player_locks[player_id]

    async def acquire_action_slot(self, player_id: int) -> bool:
        """
        Attempt to acquire the action slot for a player. Returns True if successful,
        False if the player is in cooldown.

        :param player_id: The ID of the player.
        :return: Boolean indicating if the action can be processed.
        """
        lock = self.get_lock(player_id)
        if lock.locked():
            return False
        await lock.acquire()
        # Start the cooldown timer (NOT AWAITED INTENTIONALLY)
        asyncio.create_task(self._start_cooldown(player_id, lock))
        return True

    async def _start_cooldown(self, player_id: int, lock: asyncio.Lock):
        """
        Internal method to handle the cooldown period.

        :param player_id: The ID of the player.
        :param lock: The lock associated with the player.
        """
        try:
            await asyncio.sleep(self.cooldown_period)
        finally:
            if lock.locked():
                if player_id == 1:
                    self.cooldown_queue_p1.put_nowait("1_cooldown-end")
                elif player_id == 2:
                    self.cooldown_queue_p2.put_nowait("2_cooldown-end")
                lock.release()
                logger.info(f"Cooldown ended for Player {player_id}.")
