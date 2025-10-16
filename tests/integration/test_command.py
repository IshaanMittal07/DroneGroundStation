"""
Test the command worker with a mocked drone.
"""

import math
import multiprocessing as mp
import subprocess
import threading
import time

from pymavlink import mavutil

from modules.command import command
from modules.command import command_worker
from modules.common.modules.logger import logger
from modules.common.modules.logger import logger_main_setup
from modules.common.modules.read_yaml import read_yaml
from modules.telemetry import telemetry
from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller


MOCK_DRONE_MODULE = "tests.integration.mock_drones.command_drone"
CONNECTION_STRING = "tcp:localhost:12345"

TELEMETRY_PERIOD = 0.5
TARGET = command.Position(10, 20, 30)
HEIGHT_TOLERANCE = 0.5
Z_SPEED = 1  # m/s
ANGLE_TOLERANCE = 5  # deg
TURNING_SPEED = 5  # deg/s


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def start_drone() -> None:
    """
    Start the mocked drone.
    """
    subprocess.run(["python", "-m", MOCK_DRONE_MODULE], shell=True, check=False)


def stop(
    telemetry_queue: queue_proxy_wrapper.QueueProxyWrapper,
    report_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Stop the workers.
    """
    telemetry_queue.fill_and_drain_queue()
    report_queue.fill_and_drain_queue()
    controller.request_exit()


def read_queue(
    report_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
    _main_logger: logger.Logger,  # renamed to _main_logger to mark unused
) -> None:
    """
    Read and print the output queue.
    """
    while not controller.is_exit_requested():
        if not report_queue.queue.empty():
            report_queue.queue.get()
        time.sleep(0.1)


def put_queue(
    telemetry_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
    path: list,
) -> None:
    """
    Place mocked inputs into the input queue periodically with period TELEMETRY_PERIOD.
    """
    for telemetry_data in path:
        if controller.is_exit_requested():
            break
        if telemetry_data is None:
            print("WARNING: Test tried to queue None telemetry data!")
            continue
        telemetry_queue.queue.put(telemetry_data)
        time.sleep(TELEMETRY_PERIOD)


def main() -> int:
    """
    Start the command worker simulation.
    """
    result, config = read_yaml.open_config(logger.CONFIG_FILE_PATH)
    if not result:
        print("ERROR: Failed to load configuration file")
        return -1

    assert config is not None
    result, main_logger, _ = logger_main_setup.setup_main_logger(config)
    if not result:
        print("ERROR: Failed to create main logger")
        return -1
    assert main_logger is not None

    connection = mavutil.mavlink_connection(CONNECTION_STRING)
    connection.mav.heartbeat_send(
        mavutil.mavlink.MAV_TYPE_GCS,
        mavutil.mavlink.MAV_AUTOPILOT_INVALID,
        0,
        0,
        0,
    )
    main_logger.info("Connected!")

    controller = worker_controller.WorkerController()
    mp_manage = mp.Manager()  # renamed to snake_case (was mpManage)

    report_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manage, 10)
    telemetry_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manage, 10)

    path = [
        telemetry.TelemetryData(x=0, y=0, z=29, yaw=0, x_velocity=0, y_velocity=0, z_velocity=4),
        telemetry.TelemetryData(x=0, y=0, z=31, yaw=0, x_velocity=0, y_velocity=0, z_velocity=-2),
        telemetry.TelemetryData(
            x=0, y=0, z=30.2, yaw=1.1071487177940904, x_velocity=0, y_velocity=0, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=0, y=0, z=29.8, yaw=1.1071487177940904, x_velocity=0, y_velocity=0, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=0, y=0, z=30, yaw=1.1071487177940904, x_velocity=0, y_velocity=0, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=0, y=0, z=30, yaw=1.142055302833977, x_velocity=0, y_velocity=0, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=0, y=0, z=30, yaw=1.072242132754204, x_velocity=0, y_velocity=0, z_velocity=0
        ),
        telemetry.TelemetryData(x=0, y=0, z=30, yaw=0, x_velocity=0, y_velocity=20, z_velocity=0),
        telemetry.TelemetryData(x=10, y=0, z=30, yaw=0, x_velocity=0, y_velocity=20, z_velocity=0),
        telemetry.TelemetryData(x=20, y=0, z=30, yaw=0, x_velocity=0, y_velocity=20, z_velocity=0),
        telemetry.TelemetryData(
            x=30, y=0, z=30, yaw=math.pi / 2, x_velocity=20, y_velocity=0, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=30, y=10, z=30, yaw=math.pi / 2, x_velocity=20, y_velocity=0, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=30, y=20, z=30, yaw=math.pi / 2, x_velocity=20, y_velocity=0, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=30, y=30, z=30, yaw=math.pi, x_velocity=0, y_velocity=-20, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=20, y=30, z=30, yaw=-math.pi, x_velocity=0, y_velocity=-20, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=10, y=30, z=30, yaw=math.pi, x_velocity=0, y_velocity=-20, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=0, y=30, z=30, yaw=-math.pi / 2, x_velocity=-20, y_velocity=0, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=0, y=20, z=30, yaw=-math.pi / 2, x_velocity=-20, y_velocity=0, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=0, y=10, z=30, yaw=-math.pi / 2, x_velocity=-20, y_velocity=0, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=0, y=0, z=30, yaw=math.pi / 2, x_velocity=0, y_velocity=20, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=0, y=10, z=30, yaw=math.pi / 2, x_velocity=0, y_velocity=20, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=0, y=20, z=30, yaw=math.pi / 2, x_velocity=0, y_velocity=20, z_velocity=0
        ),
        telemetry.TelemetryData(x=0, y=30, z=30, yaw=0, x_velocity=20, y_velocity=0, z_velocity=0),
        telemetry.TelemetryData(x=10, y=30, z=30, yaw=0, x_velocity=20, y_velocity=0, z_velocity=0),
        telemetry.TelemetryData(x=20, y=30, z=30, yaw=0, x_velocity=20, y_velocity=0, z_velocity=0),
        telemetry.TelemetryData(
            x=30, y=30, z=30, yaw=-math.pi / 2, x_velocity=0, y_velocity=-20, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=30, y=20, z=30, yaw=-math.pi / 2, x_velocity=0, y_velocity=-20, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=30, y=10, z=30, yaw=-math.pi / 2, x_velocity=0, y_velocity=-20, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=30, y=0, z=30, yaw=-math.pi, x_velocity=-20, y_velocity=0, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=20, y=0, z=30, yaw=math.pi, x_velocity=-20, y_velocity=0, z_velocity=0
        ),
        telemetry.TelemetryData(
            x=10, y=0, z=30, yaw=-math.pi, x_velocity=-20, y_velocity=0, z_velocity=0
        ),
    ]

    threading.Timer(
        TELEMETRY_PERIOD * len(path), stop, (telemetry_queue, report_queue, controller)
    ).start()
    threading.Thread(target=put_queue, args=(telemetry_queue, controller, path)).start()
    threading.Thread(target=read_queue, args=(report_queue, controller, main_logger)).start()

    command_worker.command_worker(connection, TARGET, telemetry_queue, report_queue, controller)
    return 0


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================


if __name__ == "__main__":
    drone_process = mp.Process(target=start_drone)
    drone_process.start()

    result_main = main()
    if result_main < 0:
        print(f"Failed with return code {result_main}")
    else:
        print("Success!")

    drone_process.join()
