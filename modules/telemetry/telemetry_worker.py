"""
Telemtry worker that gathers GPS data.
"""

import os
import pathlib

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

    while not controller.is_exit_requested():
        controller.check_pause()
        result, telemetry_data = tele.run()

        # Defensive checks and diagnostics
        if telemetry_data is None:
            local_logger.error("Attempting to enqueue None telemetry_data! Skipping.", True)
            continue

        if result and isinstance(telemetry_data, telemetry.TelemetryData):
            telemetry_queue.queue.put(telemetry_data)
            local_logger.info(f"Sent telemetry data: {telemetry_data}", True)
        else:
            local_logger.warning("Telemetry timeout or invalid data, skipping.", True)

    # Main loop: do work.


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
