"""
Bootcamp F2025

Main process to setup and manage all the other working processes
"""

import multiprocessing as mp
import queue
import time

from pymavlink import mavutil

from modules.common.modules.logger import logger
from modules.common.modules.logger import logger_main_setup
from modules.common.modules.read_yaml import read_yaml
from modules.command import command
from modules.command import command_worker
from modules.heartbeat import heartbeat_receiver_worker
from modules.heartbeat import heartbeat_sender_worker
from modules.telemetry import telemetry_worker
from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from utilities.workers import worker_manager


# MAVLink connection
CONNECTION_STRING = "tcp:localhost:12345"

# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
# Set queue max sizes (<= 0 for infinity)
HEART_MAX = 10
TELE_MAX = 10
REPORT_MAX = 10

# Set worker counts
HEART_SEND_WORKER = 1
HEART_REC_WORKER = 1
TELE_WORKER = 1
CMD_WORKER = 1

# Any other constants
TARGET = command.Position(10, 20, 30)
RUNTIME = 100
# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================


def main() -> int:
    """
    Main function.
    """
    # Configuration settings
    result, config = read_yaml.open_config(logger.CONFIG_FILE_PATH)
    if not result:
        print("ERROR: Failed to load configuration file")
        return -1

    assert config is not None

    # Setup main logger
    result, main_logger, _ = logger_main_setup.setup_main_logger(config)
    if not result:
        print("ERROR: Failed to create main logger")
        return -1

    assert main_logger is not None

    # Connect to the drone
    connection = mavutil.mavlink_connection(CONNECTION_STRING)
    connection.wait_heartbeat(timeout=30)

    # =============================================================================================
    #                          ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
    # =============================================================================================
    controller = worker_controller.WorkerController()

    mp_manager = mp.Manager()

    heartbeat_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, HEART_MAX)
    telemetry_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, TELE_MAX)
    report_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, REPORT_MAX)

    # Worker properties
    heartbeat_sender_properties = worker_manager.WorkerProperties(
        class_private_create_key=None,
        controller=controller,
        count=HEART_SEND_WORKER,
        target=heartbeat_sender_worker.heartbeat_sender_worker,
        work_arguments={
            "connection": connection,
            "controller": controller,
        },
        input_queues=[],
        output_queues=[],
    )

    heartbeat_receiver_properties = worker_manager.WorkerProperties(
        class_private_create_key=None,
        controller=controller,
        count=HEART_REC_WORKER,
        target=heartbeat_receiver_worker.heartbeat_receiver_worker,
        work_arguments={
            "connection": connection,
            "heartbeat_queue": heartbeat_queue,
            "controller": controller,
        },
        input_queues=[],
        output_queues=[heartbeat_queue],
    )

    telemetry_properties = worker_manager.WorkerProperties(
        class_private_create_key=None,
        controller=controller,
        count=TELE_WORKER,
        target=telemetry_worker.telemetry_worker,
        work_arguments={
            "connection": connection,
            "telemetry_queue": telemetry_queue,
            "controller": controller,
        },
        input_queues=[],
        output_queues=[telemetry_queue],
    )

    command_properties = worker_manager.WorkerProperties(
        class_private_create_key=None,
        controller=controller,
        count=CMD_WORKER,
        target=command_worker.command_worker,
        work_arguments={
            "connection": connection,
            "target": TARGET,
            "telemetry_queue": telemetry_queue,
            "report_queue": report_queue,
            "controller": controller,
        },
        input_queues=[telemetry_queue],
        output_queues=[report_queue],
    )

    # Create worker managers
    heartbeat_sender_manager = worker_manager.WorkerManager(
        class_private_create_key=None,
        workers=heartbeat_sender_properties,
        worker_properties=heartbeat_sender_properties,
        local_logger=main_logger,
    )
    heartbeat_receiver_manager = worker_manager.WorkerManager(
        class_private_create_key=None,
        workers=heartbeat_receiver_properties,
        worker_properties=heartbeat_receiver_properties,
        local_logger=main_logger,
    )
    telemetry_manager = worker_manager.WorkerManager(
        class_private_create_key=None,
        workers=telemetry_properties,
        worker_properties=telemetry_properties,
        local_logger=main_logger,
    )
    command_manager = worker_manager.WorkerManager(
        class_private_create_key=None,
        workers=command_properties,
        worker_properties=command_properties,
        local_logger=main_logger,
    )

    # Start all workers
    heartbeat_sender_manager.start_workers()
    heartbeat_receiver_manager.start_workers()
    telemetry_manager.start_workers()
    command_manager.start_workers()

    main_logger.info("Started")

    # Main's work: read from all queues that output to main, and log any commands that we make
    # Continue running for 100 seconds or until the drone disconnects
    start_time = time.time()
    while (time.time() - start_time) < RUNTIME:
        if not connection.port or connection.port.closed:
            main_logger.warning("Drone disconnected!", True)
            break

        # Read from report queue
        try:
            if not report_queue.queue.empty():
                report = report_queue.queue.get()
                if report:
                    main_logger.info(f"Command Report: {report}", True)
        except queue.Empty:
            pass

        # Read from heartbeat queue
        try:
            if not heartbeat_queue.queue.empty():
                hb = heartbeat_queue.queue.get()
                if hb:
                    main_logger.info(f"Received Heartbeat: {hb}", True)
        except queue.Empty:
            pass

        time.sleep(0.1)

    # Stop all workers
    controller.request_exit()
    main_logger.info("Requested exit")

    # Drain queues
    report_queue.fill_and_drain_queue()
    telemetry_queue.fill_and_drain_queue()
    heartbeat_queue.fill_and_drain_queue()
    main_logger.info("Queues cleared")

    # Join worker processes
    command_manager.join_workers()
    telemetry_manager.join_workers()
    heartbeat_receiver_manager.join_workers()
    heartbeat_sender_manager.join_workers()

    main_logger.info("Stopped")
    # =============================================================================================
    #                          ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
    # =============================================================================================
    return 0


if __name__ == "__main__":
    result_main = main()
    if result_main < 0:
        print(f"Failed with return code {result_main}")
    else:
        print("Success!")
