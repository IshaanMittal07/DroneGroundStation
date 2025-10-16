"""
Telemetry gathering logic.
"""

import time

from pymavlink import mavutil

from ..common.modules.logger import logger


class TelemetryData:  # pylint: disable=too-many-instance-attributes
    """
    Python struct to represent Telemtry Data. Contains the most recent attitude and position reading.
    """

    def __init__(
        self,
        time_since_boot: int | None = None,  # ms
        x: float | None = None,  # m
        y: float | None = None,  # m
        z: float | None = None,  # m
        x_velocity: float | None = None,  # m/s
        y_velocity: float | None = None,  # m/s
        z_velocity: float | None = None,  # m/s
        roll: float | None = None,  # rad
        pitch: float | None = None,  # rad
        yaw: float | None = None,  # rad
        roll_speed: float | None = None,  # rad/s
        pitch_speed: float | None = None,  # rad/s
        yaw_speed: float | None = None,  # rad/s
    ) -> None:
        self.time_since_boot = time_since_boot
        self.x = x
        self.y = y
        self.z = z
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity
        self.z_velocity = z_velocity
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.roll_speed = roll_speed
        self.pitch_speed = pitch_speed
        self.yaw_speed = yaw_speed

    def __str__(self) -> str:
        return f"""{{
            time_since_boot: {self.time_since_boot},
            x: {self.x},
            y: {self.y},
            z: {self.z},
            x_velocity: {self.x_velocity},
            y_velocity: {self.y_velocity},
            z_velocity: {self.z_velocity},
            roll: {self.roll},
            pitch: {self.pitch},
            yaw: {self.yaw},
            roll_speed: {self.roll_speed},
            pitch_speed: {self.pitch_speed},
            yaw_speed: {self.yaw_speed}
        }}"""


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class Telemetry:
    """
    Telemetry class to read position and attitude (orientation).
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    )-> tuple[bool, "Command"]:
        """
        Falliable create (instantiation) method to create a Telemetry object.
        """
        try:
            telemetry = Telemetry(
                cls.__private_key, connection, local_logger
            )  # Create a Telemetry object
            return True, telemetry

        except Exception as e:
            local_logger.error(f"Error creating Telemtery: {e}", True)
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.local_logger = local_logger

    def run(self) -> str:
        """
        Receive LOCAL_POSITION_NED and ATTITUDE messages from the drone,
        combining them together to form a single TelemetryData object.
        """
        try:
            msgLoc = self.connection.recv_match(
                type="LOCAL_POSITION_NED", blocking=True, timeout=1.0
            )  # Read MAVLink message LOCAL_POSITION_NED (32)
            msgAtt = self.connection.recv_match(
                type="ATTITUDE", blocking=True, timeout=1.0
            )  # Read MAVLink message ATTITUDE (30)

            # check if both were recevived
            if not msgLoc or not msgAtt:
                self.local_logger.warning(
                    "Did not receive both ATTITUDE and LOCAL_POSITION_NED within timeout."
                )
                return False, None

            # extract attitude data
            roll = msgAtt.roll
            pitch = msgAtt.pitch
            yaw = msgAtt.yaw
            roll_speed = msgAtt.rollspeed
            pitch_speed = msgAtt.pitchspeed
            yaw_speed = msgAtt.yawspeed
            time_att = getattr(msgAtt, "time_boot_ms", 0) / 1000.0  # convert ms to seconds

            # Extract position data
            x = msgLoc.x
            y = msgLoc.y
            z = msgLoc.z
            x_velocity = msgLoc.vx
            y_velocity = msgLoc.vy
            z_velocity = msgLoc.vz
            time_loc = getattr(msgLoc, "time_boot_ms", 0) / 1000.0

            latest_time = max(time_att, time_loc)

            # Combine into one Telemtery Data object
            telemetry_data = TelemetryData(
                time_since_boot=latest_time,
                x=x,
                y=y,
                z=z,
                x_velocity=x_velocity,
                y_velocity=y_velocity,
                z_velocity=z_velocity,
                roll=roll,
                pitch=pitch,
                yaw=yaw,
                roll_speed=roll_speed,
                pitch_speed=pitch_speed,
                yaw_speed=yaw_speed,
            )

            self.local_logger.info(f"TelemetryDat created: {telemetry_data}")

            return True, telemetry_data

        except Exception as e:
            self.local_logger.error(f"Error in Telemetry.run(): {e}", True)
            return False, None

        # Return the most recent of both, and use the most recent message's timestamp


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
