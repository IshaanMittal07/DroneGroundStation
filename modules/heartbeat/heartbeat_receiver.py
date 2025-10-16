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

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ):
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        try:
            receiver = HeartbeatReceiver(cls.__private_key, connection, local_logger)
            return True, receiver

        except Exception as e:
            local_logger.error(f"Error creating HeartbeatRecevier: {e}", True)
            return False, None
        
         # Create a HeartbeatReceiver object

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
          # Put your own arguments here
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.local_logger = local_logger
        self.missedHeartBeats = 0 # this is the # of missed heart beats 
        self.status = "Connected" 
        self.DISCONNECT_THRESHOLD = 5 #the max number of 'misses' 


    def run(self)-> str:
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """

        msg = self.connection.recv_match(type='HEARTBEAT', blocking=True, timeout = 1.0)

        if msg and msg.get_type() == "HEARTBEAT":
            self.missedHeartBeats = 0
            self.status = "Connected"
            self.local_logger.info("Received heartbeat", True)

        else:
            self.missedHeartBeats += 1
            self.local_logger.warning(f"Missed heartbeat (count: {self.missedHeartBeats})", True)

            if (self.missedHeartBeats >= self.DISCONNECT_THRESHOLD):
                self.status = "Disconnected"
                self.local_logger.error(f"Connection lost after {self.missedHeartBeats} missed heartbeats", True)
            
        return self.status 


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
