"""
Telemtry worker that gathers GPS data.
"""

import os
import pathlib
import time

from pymavlink import mavutil

from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from . import telemetry
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def telemetry_worker(
    connection: mavutil.mavfile,
    telemetry_queue: queue_proxy_wrapper.QueueProxyWrapper,  # Place your own arguments here
    controller: worker_controller.WorkerController,
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
    # Instantiate class object (telemetry.Telemetry)

    result, tele = telemetry.Telemetry.create(connection, local_logger)
    if not result:
        local_logger.error("Failed to create Telemetry", True)
        return

    local_logger.info("Telemetry Created YAY!", True)

    # Initialize time_since_boot counter
    time_since_boot = 0

    while not controller.is_exit_requested():
        controller.check_pause()
        result, telemetry_data = tele.run()

        # Skip if telemetry failed
        # Only checks for the result boolean (Review)
        if not result:
            local_logger.warning("Skipping telemetry send due to timeout or None data.", True)
            continue

        # Fixed issue with time intervals now it incremnts by 500 (Review)
        time_since_boot = (time_since_boot + 500) % 5000
        telemetry_data.time_since_boot = time_since_boot

        # Send telemetry
        telemetry_queue.queue.put(telemetry_data)
        local_logger.info(f"Sent telemetry data: {telemetry_data}", True)

        time.sleep(0.1)

    # Main loop: do work.


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
