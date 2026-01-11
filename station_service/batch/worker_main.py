"""
Batch Worker Entry Point.

This module provides the main entry point for batch worker subprocesses.
It is intentionally separated from main.py to avoid re-importing the FastAPI
application and IPC server initialization when multiprocessing spawns child processes.

CRITICAL: This module must NOT import from station_service.main to prevent
the module-level code (app creation, lifespan registration) from being executed
in worker processes.
"""

import asyncio
import logging
import sys
from typing import Any, Dict, Optional


def worker_main(
    batch_id: str,
    config_dict: Dict[str, Any],
    ipc_router_address: str,
    ipc_sub_address: str,
    backend_config_dict: Optional[Dict[str, Any]] = None,
    workflow_config_dict: Optional[Dict[str, Any]] = None,
    token_info_dict: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Entry point for the batch worker subprocess.

    This function runs in a separate process spawned by multiprocessing.Process.
    It initializes the worker environment, reconstructs configuration from
    serialized dicts, and runs the BatchWorker async main loop.

    Args:
        batch_id: The batch identifier
        config_dict: Serialized batch configuration
        ipc_router_address: IPC router address for commands
        ipc_sub_address: IPC sub address for events
        backend_config_dict: Serialized backend configuration for API integration
        workflow_config_dict: Serialized workflow configuration for 착공/완공
        token_info_dict: Serialized operator token info for JWT authentication

    Note:
        This function is designed to be used as a multiprocessing.Process target.
        It will exit with code 1 on any unhandled exception.
    """
    # Fix for Windows ZMQ compatibility
    # ProactorEventLoop (Windows default) doesn't support add_reader/add_writer
    # which ZMQ asyncio requires for IPC client
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Configure logging for subprocess
    logging.basicConfig(
        level=logging.INFO,
        format=f"[{batch_id}] %(levelname)s: %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Worker process starting for batch {batch_id}")

    try:
        # Import worker class and config models
        # These imports are safe - they don't trigger main.py imports
        from station_service.batch.worker import BatchWorker
        from station_service.models.config import (
            BackendConfig,
            BatchConfig,
            WorkflowConfig,
        )

        # Reconstruct BatchConfig from serialized dict
        logger.debug(f"[worker_main] Reconstructing config for batch {batch_id}")
        logger.debug(f"[worker_main] config_dict keys: {list(config_dict.keys())}")
        logger.debug(
            f"[worker_main] backend_config_dict keys: "
            f"{list(backend_config_dict.keys()) if backend_config_dict else 'None'}"
        )

        try:
            config = BatchConfig(**config_dict)
            logger.debug(f"[worker_main] BatchConfig reconstructed successfully")
        except Exception as e:
            logger.error(
                f"[worker_main] Failed to reconstruct BatchConfig: {e}", exc_info=True
            )
            raise

        # Reconstruct BackendConfig if provided
        backend_config = None
        if backend_config_dict:
            try:
                backend_config = BackendConfig(**backend_config_dict)
                logger.debug(f"[worker_main] BackendConfig reconstructed successfully")
            except Exception as e:
                logger.error(
                    f"[worker_main] Failed to reconstruct BackendConfig: {e}",
                    exc_info=True,
                )
                raise

        # Reconstruct WorkflowConfig if provided
        workflow_config = None
        if workflow_config_dict:
            try:
                workflow_config = WorkflowConfig(**workflow_config_dict)
                logger.debug(
                    f"[worker_main] WorkflowConfig reconstructed successfully"
                )
            except Exception as e:
                logger.error(
                    f"[worker_main] Failed to reconstruct WorkflowConfig: {e}",
                    exc_info=True,
                )
                raise

        # Log backend integration status
        if backend_config:
            logger.info(f"Backend integration enabled: {backend_config.url}")
        else:
            logger.info("Backend integration disabled (no config)")

        # Create and run worker
        worker = BatchWorker(
            batch_id=batch_id,
            config=config,
            ipc_router_address=ipc_router_address,
            ipc_sub_address=ipc_sub_address,
            backend_config=backend_config,
            workflow_config=workflow_config,
            token_info_dict=token_info_dict,
        )

        # Run the async main loop
        # This will block until the worker is shut down
        asyncio.run(worker.run())

    except Exception as e:
        logger.exception(f"Worker process error: {e}")
        sys.exit(1)

    logger.info(f"Worker process exiting for batch {batch_id}")
