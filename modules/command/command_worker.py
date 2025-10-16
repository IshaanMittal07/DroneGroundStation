"""
Command worker to make decisions based on Telemetry Data.
"""
import time
import os
import pathlib

from pymavlink import mavutil

from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from . import command
from ..common.modules.logger import logger
from modules.telemetry import telemetry  



# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def command_worker(
    connection: mavutil.mavfile,
    target: command.Position,
    telemetry_queue: queue_proxy_wrapper.QueueProxyWrapper,
    report_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,  # Place your own arguments here
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.

    args... describe what the arguments are
    """
    # =============================================================================================
    #                          ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
    # =============================================================================================

    # Instantiate logger
    worker_name = pathlib.Path(__file__).stem
    process_id = os.getpid()
    result, local_logger = logger.Logger.create(f"{worker_name}_{process_id}", True)
    if not result:
        print("ERROR: Worker failed to create logger")
        return

    # Get Pylance to stop complaining
    assert local_logger is not None

    local_logger.info("Logger initialized", True)

    # =============================================================================================
    #                          ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
    # =============================================================================================
    # Instantiate class object (command.Command)

    result, cmd = command.Command.create(connection, target, local_logger)
    cmd.set_target(target)
    if not result:
        local_logger.error("Failed to create Command", True)
        return

    local_logger.info("Command Created YAY!", True)

    while not controller.is_exit_requested():
        controller.check_pause()
        if not telemetry_queue.queue.empty():
            telemetry_data = telemetry_queue.queue.get()


            if telemetry_data is None:
                continue

            decision = cmd.run(telemetry_data)

            if result and decision is not None:
                report_queue.queue.put(decision)
        else:
            time.sleep(0.01)

        
    local_logger.info("Command worker exiting", True)


    # Main loop: do work.


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
