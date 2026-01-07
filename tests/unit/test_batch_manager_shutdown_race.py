
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from station_service.batch.manager import BatchManager
from station_service.core.events import EventEmitter
from station_service.core.exceptions import IPCTimeoutError
from station_service.models.config import StationConfig

class TestBatchManagerShutdownRace:
    @pytest.fixture
    def event_emitter(self):
        return EventEmitter()

    @pytest.fixture
    def mock_ipc_server(self):
        mock = MagicMock()
        mock.router_address = "tcp://127.0.0.1:5555"
        mock.sub_address = "tcp://127.0.0.1:5557"
        mock.is_running = True
        mock.start = AsyncMock()
        mock.stop = AsyncMock()
        mock.unregister_worker = MagicMock()
        return mock

    @pytest.fixture
    def batch_manager(self, station_config, mock_ipc_server, event_emitter):
        return BatchManager(
            config=station_config,
            ipc_server=mock_ipc_server,
            event_emitter=event_emitter,
        )

    @pytest.mark.asyncio
    async def test_start_batch_race_condition(
        self, batch_manager, batch_config
    ):
        """
        Test that start_batch handles the race condition where the batch is removed
        from _batches (e.g. by monitor loop) while waiting for connection.
        """
        await batch_manager.start()
        batch_id = batch_config.id

        # Mock BatchProcess
        with patch("station_service.batch.manager.BatchProcess") as MockBatchProcess:
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.start = AsyncMock()
            mock_process.stop = AsyncMock()
            MockBatchProcess.return_value = mock_process

            # Mock wait_for_worker to simulate timeout AND removal of batch
            async def side_effect_wait(*args, **kwargs):
                # Simulate the race: remove batch from manager before raising timeout
                # This mimics _monitor_loop detecting crash and removing it
                if batch_id in batch_manager._batches:
                    batch_manager._batches.pop(batch_id)
                
                # Now raise timeout as if connection failed
                raise IPCTimeoutError("Simulated timeout", 1000)

            batch_manager._ipc_server.wait_for_worker = AsyncMock(side_effect=side_effect_wait)

            # This should NOT raise KeyError, but should raise BatchError (from re-raised timeout)
            # or IPCTimeoutError depending on implementation. 
            # In current implementation it catches IPCTimeoutError and raises BatchError.
            # The key is that it shouldn't raise KeyError.
            from station_service.core.exceptions import BatchError
            
            try:
                await batch_manager.start_batch(batch_id)
            except BatchError:
                # Expected error
                pass
            except KeyError:
                pytest.fail("Raised KeyError! Race condition fix failed.")
            except Exception as e:
                pytest.fail(f"Raised unexpected exception: {type(e).__name__}: {e}")

        await batch_manager.stop()
