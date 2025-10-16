"""
Decision-making logic.
"""

import time
import math

from pymavlink import mavutil

from ..common.modules.logger import logger
from ..telemetry import telemetry


class Position:
    """
    3D vector struct.
    """

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class Command:  # pylint: disable=too-many-instance-attributes
    """
    Command class to make a decision based on recieved telemetry,
    and send out commands based upon the data.
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
    ):
        """
        Falliable create (instantiation) method to create a Command object.
        """
        try:
            command = Command(cls.__private_key, connection, target, local_logger)
            return True, command

        except Exception as e:
            local_logger.error(f"Error creating Command: {e}", True)
            return False, None
        

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        # Do any intializiation here

        self.connection = connection
        self.target = None
        self.local_logger = local_logger

        self.velocity_sum = Position(0.0,0.0,0.0)
        self.sample_count = 0 

    def set_target(self, target):
        """Sets the 3D target position for the drone to align to."""
        self.target = target

    def run(
        self,
        telemetry_data: telemetry.TelemetryData,  # Put your own arguments here
    ):

        #To get the average velocity
        self.velocity_sum.x += telemetry_data.x_velocity or 0 #adding all the instatenous velocites x,y,z
        self.velocity_sum.y += telemetry_data.y_velocity or 0 #the 0 is here to avoide TypeError if the data from the telemetry turns out to be 'None' 
        self.velocity_sum.z += telemetry_data.z_velocity or 0
        self.sample_count += 1 #denominator for average calc

        avg_vx = self.velocity_sum.x / self.sample_count
        avg_vy = self.velocity_sum.y / self.sample_count
        avg_vz = self.velocity_sum.z / self.sample_count
        self.local_logger.info(f"Average velocity so far: ({avg_vx:.2f}, {avg_vy:.2f}, {avg_vz:.2f})", True)

        #Altitude 
        delta_z = self.target.z - telemetry_data.z
        if abs(delta_z) > 0.5:
            self.connection.mav.command_long_send(
                self.connection.target_system,           # target system ID
                self.connection.target_component,        # target component ID
                mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,  # command ID 113
                0,                                       # confirmation
                1.0,                                     # param1: ascent/descent speed (m/s)
                0,                                       # param2: unused
                0,                                       # param3: unused
                0,                                       # param4: unused
                0,                                       # param5: unused
                0,                                       # param6: unused
                self.target.z                            # ✅ param7: target altitude (should be 30)
            )
            self.local_logger.info(f"CHANGE ALTITUDE: {delta_z:.2f}", True)
            return f"CHANGE ALTITUDE: {delta_z:.2f}"


    # --- yaw control ---
        dx = self.target.x - telemetry_data.x
        dy = self.target.y - telemetry_data.y
        desired_yaw = math.degrees(math.atan2(dy, dx))
        current_yaw = math.degrees(telemetry_data.yaw)
        yaw_error = (desired_yaw - current_yaw + 180) % 360 - 180

        if abs(yaw_error) > 5:
            self.connection.mav.command_long_send(
                self.connection.target_system,
                self.connection.target_component,
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,
                yaw_error,  # param1: yaw angle in degrees
                5.0,        # ✅ param2: turn speed (m/s or deg/s expected)
                1,          # param3: direction (1 = CW)
                1,          # param4: relative mode
                0, 0, 0
            )
            return f"CHANGE YAW: {yaw_error:.2f}"

        return None
        
        
            
        """
        Make a decision based on received telemetry data.
        """
        # Log average velocity for this trip so far

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
        # Positive angle is counter-clockwise as in a right handed system


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
