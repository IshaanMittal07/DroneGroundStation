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
          # Put your own arguments here
    ) -> "tuple[True, HeartbeatSender] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatSender object.
        """

        try:
            #sender = cls(cls.__private_key, connection, args) cls refers to the class HeartbeatSender itself, the private key is to make sure _init_ in not directly called
            #connection is used to send mavlink messages
            sender = HeartbeatSender(cls.__private_key, connection)
            return True, sender

        except Exception as e:
            print(f"Error creating HeartbeatSender: {e}", True)
            return False, None
        
        # pass  # Create a HeartbeatSender object

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        
    ):
        assert key is HeartbeatSender.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection #initalizing the connection

    def run(self):
        """
        Attempt to send a heartbeat message.
        """
       # try:
            # Send a heartbeat message
        self.connection.mav.heartbeat_send(   #Hi, I’m a Ground Control Station, I’m active, and I’m not an autopilot.”
            mavutil.mavlink.MAV_TYPE_GCS,               
            mavutil.mavlink.MAV_AUTOPILOT_INVALID,       
            0,                                           
            0,                                           
            mavutil.mavlink.MAV_STATE_ACTIVE             
        )
       # except Exception as e:
           # local_logger.error(f"Failed to send HEARTBEAT: {e}", True)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
