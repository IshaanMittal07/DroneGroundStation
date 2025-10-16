"""
Command worker to make decisions based on Telemetry Data.
"""

import time
import os
import pathlib

from pymavlink import mavutil
from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from ..common.modules.logger import logger
from . import command


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def command_worker(
    connection: mavutil.mavfile,
    target: command.Position,
    telemetry_queue: queue_proxy_wrapper.QueueProxyWrapper,
    report_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process.

    args... describe what the arguments are
    """
    # =============================================================================================
    #                          ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
    # =============================================================================================

    worker_name = pathlib.Path(__file__).stem
    process_id = os.getpid()
    result, local_logger = logger.Logger.create(f"{worker_name}_{process_id}", True)
    if not result:
        print("ERROR: Worker failed to create logger")
        return

    assert local_logger is not None
    local_logger.info("Logger initialized", True)

    # =============================================================================================
    #                          ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
    # =============================================================================================

    result, cmd = command.Command.create(
        connection, local_logger
    )  # removed target before local_logger due to pylint issues
    if not result or cmd is None:
        local_logger.error("Failed to create Command", True)
        return

    cmd.set_target(target)
    local_logger.info("Command Created YAY!", True)

    while not controller.is_exit_requested():
        controller.check_pause()

        if not telemetry_queue.queue.empty():
            telemetry_data = telemetry_queue.queue.get()

            if telemetry_data is None:
                continue

            decision = cmd.run(telemetry_data)
            if decision is not None:
                report_queue.queue.put(decision)
        else:
            time.sleep(0.01)

    local_logger.info("Command worker exiting", True)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
