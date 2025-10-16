"""
Heartbeat sending logic.
"""

from pymavlink import mavutil


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class HeartbeatSender:
    """
    HeartbeatSender class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
    ) -> tuple[bool, "HeartbeatSender"]:
        """
        Falliable create (instantiation) method to create a HeartbeatSender object.
        """
        try:
            sender = HeartbeatSender(cls.__private_key, connection)
            return True, sender
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Error creating HeartbeatSender: {e}", True)
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
    ) -> None:
        assert key is HeartbeatSender.__private_key, "Use create() method"
        self.connection = connection

    def run(self) -> None:
        """
        Attempt to send a heartbeat message.
        """
        try:
            self.connection.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_GCS,
                mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                0,
                0,
                mavutil.mavlink.MAV_STATE_ACTIVE,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Failed to send HEARTBEAT: {e}", True)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
