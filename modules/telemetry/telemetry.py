"""
Telemetry gathering logic.
"""

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
    ) -> tuple[bool, "Telemetry"]:
        """
        Falliable create (instantiation) method to create a Telemetry object.
        """
        try:
            telemetry = Telemetry(cls.__private_key, connection, local_logger)
            return True, telemetry
        except Exception as e:  # pylint: disable=broad-exception-caught
            local_logger.error(f"Error creating Telemetry: {e}", True)
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"
        self.connection = connection
        self.local_logger = local_logger

    def run(self) -> tuple[bool, TelemetryData | None]:
        """
        Receive LOCAL_POSITION_NED and ATTITUDE messages from the drone,
        combining them together to form a single TelemetryData object.
        """

        #Implemented check to get both LOCAL_POSITION_NED AND ATTITUDE within 1 second (Review) 
        try:
            start_time = time.time()
            msg_loc = msg_att = None

            # Keep trying until both messages are received or 1 second passes
            while time.time() - start_time < 1.0:
                if not msg_loc:
                    msg_loc = self.connection.recv_match(
                        type="LOCAL_POSITION_NED", blocking=False
                    )
                if not msg_att:
                    msg_att = self.connection.recv_match(
                        type="ATTITUDE", blocking=False
                    )
                if msg_loc and msg_att:
                    break
                time.sleep(0.01)

            # Timeout check — didn't get both within 1s
            if not msg_loc or not msg_att:
                self.local_logger.warning(
                    "Did not receive both ATTITUDE and LOCAL_POSITION_NED within 1 second."
                )
                return False, None

            roll = msg_att.roll
            pitch = msg_att.pitch
            yaw = msg_att.yaw
            roll_speed = msg_att.rollspeed
            pitch_speed = msg_att.pitchspeed
            yaw_speed = msg_att.yawspeed
            time_att = getattr(msg_att, "time_boot_ms", 0) #removed division (Review) 

            x = msg_loc.x
            y = msg_loc.y
            z = msg_loc.z
            x_velocity = msg_loc.vx
            y_velocity = msg_loc.vy
            z_velocity = msg_loc.vz
            time_loc = getattr(msg_loc, "time_boot_ms", 0) #removed division (Review) 

            latest_time = max(time_att, time_loc)

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

            self.local_logger.info(f"TelemetryData created: {telemetry_data}")
            return True, telemetry_data

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.local_logger.error(f"Error in Telemetry.run(): {e}", True)
            return False, None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
