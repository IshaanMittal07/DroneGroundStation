"""
Heartbeat receiving logic.
"""

from pymavlink import mavutil
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class HeartbeatReceiver:
    """
    HeartbeatReceiver class to send a heartbeat
    """

    __private_key = object()
    DISCONNECT_THRESHOLD = 5  # max number of missed heartbeats

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> tuple[bool, "HeartbeatReceiver"]:
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        try:
            receiver = HeartbeatReceiver(cls.__private_key, connection, local_logger)
            return True, receiver
        except Exception as e:  # pylint: disable=broad-exception-caught
            local_logger.error(f"Error creating HeartbeatReceiver: {e}", True)
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        self.connection = connection
        self.local_logger = local_logger
        self.missed_heartbeats = 0  # number of missed heartbeats
        self.status = "Connected"

    def run(self) -> str:
        """
        Attempt to receive a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        msg = self.connection.recv_match(type="HEARTBEAT", blocking=True, timeout=1.0)

        if msg and msg.get_type() == "HEARTBEAT":
            self.missed_heartbeats = 0
            self.status = "Connected"
            self.local_logger.info("Received heartbeat", True)
        else:
            self.missed_heartbeats += 1
            self.local_logger.warning(f"Missed heartbeat (count: {self.missed_heartbeats})", True)

            if self.missed_heartbeats >= self.DISCONNECT_THRESHOLD:
                self.status = "Disconnected"
                self.local_logger.error(
                    f"Connection lost after {self.missed_heartbeats} missed heartbeats", True
                )

        return self.status


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
