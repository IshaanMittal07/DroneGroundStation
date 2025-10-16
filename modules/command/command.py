"""
Decision-making logic.
"""

import math
from pymavlink import mavutil

from ..common.modules.logger import logger
from ..telemetry import telemetry


class Position:
    """3D vector struct."""

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class Command:  # pylint: disable=too-many-instance-attributes
    """
    Command class to make a decision based on received telemetry,
    and send out commands based upon the data.
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        #target: Position, DONE BC OF PYLINT
        local_logger: logger.Logger,
    ) -> tuple[bool, "Command"]:
        """Fallible create (instantiation) method to create a Command object."""
        try:
            command = Command(cls.__private_key, connection, local_logger)  #removed target before local_logger due to pylint issues
            return True, command
        except Exception as e:  # pylint: disable=broad-exception-caught
            local_logger.error(f"Error creating Command: {e}", True)
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        #target: Position, DONE BC OF PYLINT
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        self.connection = connection
        self.target = None
        self.local_logger = local_logger

        self.velocity_sum = Position(0.0, 0.0, 0.0)
        self.sample_count = 0

    def set_target(self, target: Position) -> None:
        """Sets the 3D target position for the drone to align to."""
        self.target = target

    def run(self, telemetry_data: telemetry.TelemetryData) -> str | None:
        """Make a decision based on received telemetry data."""
        self.velocity_sum.x += telemetry_data.x_velocity or 0
        self.velocity_sum.y += telemetry_data.y_velocity or 0
        self.velocity_sum.z += telemetry_data.z_velocity or 0
        self.sample_count += 1

        avg_vx = self.velocity_sum.x / self.sample_count
        avg_vy = self.velocity_sum.y / self.sample_count
        avg_vz = self.velocity_sum.z / self.sample_count
        self.local_logger.info(
            f"Average velocity so far: ({avg_vx:.2f}, {avg_vy:.2f}, {avg_vz:.2f})", True
        )

        delta_z = self.target.z - telemetry_data.z
        if abs(delta_z) > 0.5:
            self.connection.mav.command_long_send(
                self.connection.target_system,
                self.connection.target_component,
                mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                0,
                1.0,  # ascent/descent speed
                0,
                0,
                0,
                0,
                0,
                self.target.z,
            )
            self.local_logger.info(f"CHANGE ALTITUDE: {delta_z:.2f}", True)
            return f"CHANGE ALTITUDE: {delta_z:.2f}"

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
                yaw_error,
                5.0,  # turning speed
                1,
                1,
                0,
                0,
                0,
            )
            return f"CHANGE YAW: {yaw_error:.2f}"

        return None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
