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
HeartMax = 10
TeleMax = 10
ReportMax = 10

# Set worker counts
HeartSendWorker = 1
HeartRecWorker = 1
TeleWorker = 1
CmdWorker = 1

# Any other constants
TARGET = command.Position(10, 20, 30)
Runtime = 100


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

    # Get Pylance to stop complaining
    assert config is not None

    # Setup main logger
    result, main_logger, _ = logger_main_setup.setup_main_logger(config)
    if not result:
        print("ERROR: Failed to create main logger")
        return -1

    # Get Pylance to stop complaining
    assert main_logger is not None

    # Create a connection to the drone. Assume that this is safe to pass around to all processes
    # In reality, this will not work, but to simplify the bootamp, preetend it is allowed
    # To test, you will run each of your workers individually to see if they work
    # (test "drones" are provided for you test your workers)
    # NOTE: If you want to have type annotations for the connection, it is of type mavutil.mavfile
    connection = mavutil.mavlink_connection(CONNECTION_STRING)
    connection.wait_heartbeat(timeout=30)  # Wait for the "drone" to connect

    # =============================================================================================
    #                          ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
    # =============================================================================================
    # Create a worker controller
    controller = worker_controller.WorkerController()

    # Create a multiprocess manager for synchronized queues
    mpManage = mp.Manager() 

    # Create queues
    heartbeat_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, HeartMax)
    telemetry_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, TeleMax)
    report_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, ReportMax)
    
    # Create worker properties for each worker type (what inputs it takes, how many workers)
    # Heartbeat sender
    heartbeat_sender_properties = worker_manager.WorkerProperties(
        num = HeartSendWorker,
        function = heartbeat_sender_worker.heartbeat_sender_worker,
        arguments={
            "connection": connection,
            "controller": controller,
        },
    )

    # Heartbeat receiver
    heartbeat_receiver_properties = worker_manager.WorkerProperties(
        num = HeartRecdWorker,
        function = heartbeat_receiver_worker.heartbeat_receiver_worker,
        arguments={
            "connection": connection,
            "heartbeat_queue": heartbeat_queue
            "controller": controller,
        },
    )

    # Telemetry
    telemetry_properties = worker_manager.WorkerProperties(
        num = TeleWorker,
        function = telemetry_worker.telemetry_worker,
        arguments={
            "connection": connection,
            "target": TARGET,
            "telemetry_queue": telemtry_queue,
            "report_queue": report_queue, 
            "controller": controller,
        },
    )

    # Command
    command_properties = worker_manager.WorkerProperties(
        num = CmdWorker,
        function = command_worker.command_worker,
        arguments={
            "connection": connection,
            "target": TARGET,
            "telemetry_queue": telemtry_queue,
            "report_queue": report_queue, 
            "controller": controller,
        },
    )
    

    # Create the workers (processes) and obtain their managers
    heartbeat_sender_manager = worker_manager.WorkerManager(heartbeat_sender_properties)
    heartbeat_receiver_manager = worker_manager.WorkerManager(heartbeat_receiver_properties)
    telemetry_manager = worker_manager.WorkerManager(telemetry_properties)
    command_manager = worker_manager.WorkerManager(command_properties)

    # Start worker processes
    heartbeat_sender_manager.start_workers()
    heartbeat_receiver_manager.start_workers()
    telemetry_manager.start_workers()
    command_manager.start_workers()
    

    main_logger.info("Started")

    # Main's work: read from all queues that output to main, and log any commands that we make
    # Continue running for 100 seconds or until the drone disconnects

    start_time = time.time()

    while (time.time() - start_time) < Runtime:
        # If drone disconnected, break early
        if not connection.port or connection.port.closed:
            main_logger.warning("Drone disconnected!", True)
            break

        # Read from report queue (command worker outputs)
        try:
            if not report_queue.queue.empty():
                report = report_queue.queue.get()
                if report is not None:
                    main_logger.info(f"Command Report: {report}", True)
        except queue.Empty:
            pass

        #Read heartbeat updates
        try:
            if not heartbeat_queue.queue.empty():
                hb = heartbeat_queue.queue.get()
                if hb is not None:
                    main_logger.info(f"Received Heartbeat: {hb}", True)
        except queue.Empty:
            pass

        time.sleep(0.1)

    # Stop the processes
    controller.request_exit()

    main_logger.info("Requested exit")

    # Fill and drain queues from END TO START
    report_queue.fill_and_drain_queue()
    telemetry_queue.fill_and_drain_queue()
    heartbeat_queue.fill_and_drain_queue()


    main_logger.info("Queues cleared")

    # Clean up worker processes
    command_manager.join_workers()
    telemetry_manager.join_workers()
    heartbeat_receiver_manager.join_workers()
    heartbeat_sender_manager.join_workers()

    main_logger.info("Stopped")

    # We can reset controller in case we want to reuse it
    # Alternatively, create a new WorkerController instance

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
