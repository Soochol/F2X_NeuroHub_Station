/**
 * Batches page - Batch monitoring and control.
 * Enhanced with create batch wizard and statistics panel.
 * Detail view is now a separate page (/batches/:batchId).
 */

import { useEffect, useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layers, Plus, WifiOff } from 'lucide-react';
import {
  useBatchList,
  useWebSocket,
  useSequenceList,
  useCreateBatches,
  useAllBatchStatistics,
  useStartBatch,
  useStartSequence,
  useStopBatch,
  useWorkflowConfig,
} from '../hooks';
import { useBatchStore } from '../stores/batchStore';
import { useLogStore } from '../stores/logStore';
import { useConnectionStore } from '../stores/connectionStore';
import { BatchList } from '../components/organisms/batches/BatchList';
import { CreateBatchWizard } from '../components/organisms/batches/CreateBatchWizard';
import { BatchStatisticsPanel } from '../components/organisms/batches/BatchStatisticsPanel';
import { Button } from '../components/atoms/Button';
import { LoadingOverlay } from '../components/atoms/LoadingSpinner';
import { getBatchDetailRoute } from '../constants';
import type { CreateBatchRequest, SequencePackage, BatchDetail } from '../types';
import { getSequence } from '../api/endpoints/sequences';
import { getBatch as fetchBatchFromApi } from '../api/endpoints/batches';
import { validateWip } from '../api/endpoints/system';
import { WipInputModal } from '../components/molecules';
import { toast } from '../utils/toast';

export function BatchesPage() {
  const navigate = useNavigate();

  const { data: batches, isLoading: batchesLoading } = useBatchList();
  const { data: sequences } = useSequenceList();
  const { data: allStatistics } = useAllBatchStatistics();
  const { subscribe, isConnected } = useWebSocket();

  // Connection status for Create Batch button
  const websocketStatus = useConnectionStore((state) => state.websocketStatus);
  const isServerConnected = isConnected && websocketStatus === 'connected';

  // Subscribe to both batches Map and version counter
  // The version counter ensures re-renders when Map contents change
  const batchesMap = useBatchStore((state) => state.batches);
  const batchesVersion = useBatchStore((state) => state.batchesVersion);
  const batchStatistics = useBatchStore((state) => state.batchStatistics);
  const setAllBatchStatistics = useBatchStore((state) => state.setAllBatchStatistics);
  const isWizardOpen = useBatchStore((state) => state.isWizardOpen);
  const openWizard = useBatchStore((state) => state.openWizard);
  const closeWizard = useBatchStore((state) => state.closeWizard);

  // Sync API statistics to store for real-time updates
  useEffect(() => {
    if (allStatistics) {
      setAllBatchStatistics(allStatistics);
    }
  }, [allStatistics, setAllBatchStatistics]);

  // Convert Map to array - batchesVersion in deps ensures recalculation on updates
  const storeBatches = useMemo(() => {
    const arr = Array.from(batchesMap.values());
    console.log(`[BatchesPage] storeBatches recalc: version=${batchesVersion}, size=${arr.length}`, arr.map(b => `${b.id.slice(0,8)}:${b.status}`));
    return arr;
  }, [batchesMap, batchesVersion]);

  const createBatches = useCreateBatches();
  const startBatch = useStartBatch();
  const startSequence = useStartSequence();
  const stopBatch = useStopBatch();

  // Workflow configuration for WIP modal
  const { data: workflowConfig } = useWorkflowConfig();

  // WIP input modal state
  const [showWipModal, setShowWipModal] = useState(false);
  const [wipError, setWipError] = useState<string | null>(null);
  const [selectedBatchIdForWip, setSelectedBatchIdForWip] = useState<string | null>(null);

  // Subscribe to all batches for real-time updates
  // NOTE: We intentionally don't unsubscribe on cleanup because:
  // 1. React's cleanup runs BEFORE new component's effect, causing a gap where batches are unsubscribed
  // 2. During navigation, this gap causes missed WebSocket messages
  // 3. Subscriptions are idempotent and cleaned up on WebSocket disconnect
  useEffect(() => {
    if (batches && batches.length > 0) {
      const batchIds = batches.map((b) => b.id);
      subscribe(batchIds);
      // No cleanup - subscriptions persist across navigation
    }
  }, [batches, subscribe]);

  // Use store batches if available (more up-to-date from WebSocket)
  const displayBatches = storeBatches.length > 0 ? storeBatches : batches ?? [];

  const handleSelectBatch = (id: string) => {
    navigate(getBatchDetailRoute(id));
  };

  const handleStartSequence = async (batchId: string) => {
    // If workflow is enabled, show WIP input modal first
    if (workflowConfig?.enabled) {
      setSelectedBatchIdForWip(batchId);
      setShowWipModal(true);
      return;
    }

    // Otherwise, start sequence directly
    await doStartSequence(batchId);
  };

  // Actually start the sequence (with optional WIP ID)
  const doStartSequence = async (batchId: string, wipId?: string, wipIntId?: number) => {
    // Clear logs before starting new sequence
    useLogStore.getState().clearLogs();

    // Track if we started the batch so we can stop it on error
    let batchWasStarted = false;

    try {
      // Fetch fresh batch status from API
      const freshBatch = await fetchBatchFromApi(batchId);
      const currentStatus = freshBatch.status;

      // If batch is idle, start batch first then start sequence
      if (currentStatus === 'idle') {
        await startBatch.mutateAsync(batchId);
        batchWasStarted = true;
      }

      // Prepare request with WIP ID if provided
      const request = wipId ? {
        parameters: { wip_id: wipId },
        wip_int_id: wipIntId,
      } : undefined;

      // Then start sequence
      await startSequence.mutateAsync({ batchId, request });
    } catch (error) {
      console.error('Failed to start sequence:', error);

      // If we started the batch but sequence failed, stop the batch
      if (batchWasStarted) {
        try {
          await stopBatch.mutateAsync(batchId);
        } catch (stopError) {
          console.error('Failed to stop batch:', stopError);
        }
      }

      throw error;
    }
  };

  // Handle WIP input modal submit
  const handleWipSubmit = async (wipId: string) => {
    if (!selectedBatchIdForWip) return;
    setWipError(null);

    try {
      // Get batch detail to find processId
      const batchDetail = await fetchBatchFromApi(selectedBatchIdForWip) as BatchDetail;
      const processId = batchDetail.processId ?? (batchDetail.config?.processId as number | undefined);

      if (processId === undefined || processId === null) {
        setWipError('MES Process가 설정되지 않았습니다. Batch 상세 페이지에서 Config 탭에서 MES Process를 설정해주세요.');
        return;
      }

      // Validate WIP
      const validationResult = await validateWip(wipId, processId);

      if (!validationResult.valid) {
        setWipError(validationResult.message || `WIP '${wipId}' not found`);
        return;
      }

      // Check if WIP already PASS for this process
      if (validationResult.hasPassForProcess) {
        setWipError(validationResult.passWarningMessage || '이 WIP는 이미 해당 공정을 PASS했습니다.');
        return;
      }

      // WIP is valid - close modal and start sequence
      setShowWipModal(false);
      setSelectedBatchIdForWip(null);

      await doStartSequence(selectedBatchIdForWip, wipId, validationResult.intId);
    } catch (error) {
      const errorMessage = error instanceof Error
        ? error.message
        : (error as { message?: string })?.message || 'Failed to validate WIP';

      if (showWipModal) {
        setWipError(errorMessage);
      } else {
        toast.error(errorMessage);
      }
    }
  };

  // Handle closing the WIP modal
  const handleWipModalClose = () => {
    setShowWipModal(false);
    setWipError(null);
    setSelectedBatchIdForWip(null);
  };

  const handleStopSequence = async (batchId: string) => {
    try {
      await stopBatch.mutateAsync(batchId);
    } catch (error) {
      console.error('Failed to stop sequence:', error);
    }
  };

  const handleCreateBatches = async (request: CreateBatchRequest) => {
    await createBatches.mutateAsync(request);
    closeWizard();
  };

  const getSequenceDetail = useCallback(async (name: string): Promise<SequencePackage> => {
    return getSequence(name);
  }, []);

  if (batchesLoading) {
    return <LoadingOverlay message="Loading batches..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Layers className="w-6 h-6 text-brand-500" />
          <h2 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Batches</h2>
        </div>
        <div className="flex items-center gap-3">
          {!isServerConnected && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-amber-500/10 border border-amber-500/30">
              <WifiOff className="w-4 h-4 text-amber-500" />
              <span className="text-sm text-amber-500">Server disconnected</span>
            </div>
          )}
          <Button
            variant="primary"
            onClick={openWizard}
            disabled={!isServerConnected}
            title={!isServerConnected ? 'Server connection required to create batches' : undefined}
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Batch
          </Button>
        </div>
      </div>

      {/* Statistics Panel */}
      <BatchStatisticsPanel batches={displayBatches} statistics={batchStatistics} />

      {/* Batch List - Click to view details, controls only in detail page */}
      {/* key forces re-render when batch data changes */}
      <BatchList
        key={`batch-list-${batchesVersion}`}
        batches={displayBatches}
        statistics={batchStatistics}
        onSelect={handleSelectBatch}
        onStartSequence={handleStartSequence}
        onStopSequence={handleStopSequence}
        isStartingSequence={startBatch.isPending || startSequence.isPending}
      />

      {/* Create Batch Wizard Modal */}
      <CreateBatchWizard
        isOpen={isWizardOpen}
        onClose={closeWizard}
        onSubmit={handleCreateBatches}
        sequences={sequences ?? []}
        getSequenceDetail={getSequenceDetail}
        isSubmitting={createBatches.isPending}
      />

      {/* WIP Input Modal */}
      <WipInputModal
        isOpen={showWipModal}
        onClose={handleWipModalClose}
        onSubmit={handleWipSubmit}
        isLoading={startBatch.isPending || startSequence.isPending}
        batchName={selectedBatchIdForWip ? batchesMap.get(selectedBatchIdForWip)?.name : undefined}
        errorMessage={wipError}
      />
    </div>
  );
}
