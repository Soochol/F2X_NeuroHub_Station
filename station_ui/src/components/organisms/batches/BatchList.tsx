/**
 * Batch list component.
 * Enhanced with statistics display for each batch.
 */

import { useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { List, LayoutGrid, Grid3X3 } from 'lucide-react';
import { BatchCard } from '../../molecules/BatchCard';
import { Select } from '../../atoms/Select';
import { useBatchStore } from '../../../stores/batchStore';
import { useUIStore, type BatchListLayout } from '../../../stores/uiStore';
import type { Batch, BatchStatus, BatchStatistics } from '../../../types';

export interface BatchListProps {
  batches: Batch[];
  statistics?: Map<string, BatchStatistics>;
  onDelete?: (batchId: string) => void;
  onSelect?: (batchId: string) => void;
  onStartSequence?: (batchId: string) => void;
  onStopSequence?: (batchId: string) => void;
  isLoading?: boolean;
  isStartingSequence?: boolean;
}

export function BatchList({ batches, statistics, onDelete, onSelect, onStartSequence, onStopSequence, isLoading, isStartingSequence }: BatchListProps) {
  const { batchId: selectedBatchId } = useParams<{ batchId?: string }>();
  const [statusFilter, setStatusFilter] = useState<BatchStatus | 'all'>('all');

  // Layout state from UI store
  const batchListLayout = useUIStore((state) => state.batchListLayout);
  const setBatchListLayout = useUIStore((state) => state.setBatchListLayout);

  // Get statistics from store if not provided via props
  // Note: Don't use useShallow with Map objects - shallow comparison doesn't work correctly
  const batchStatistics = useBatchStore((state) => state.batchStatistics);
  const batchStats = statistics || batchStatistics;

  // Dynamic grid classes based on layout
  const gridClasses = useMemo(() => {
    switch (batchListLayout) {
      case 'horizontal':
        return 'grid grid-cols-1 md:grid-cols-2 gap-4';
      case 'grid':
        return 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4';
      default:
        return 'grid gap-4';
    }
  }, [batchListLayout]);

  const layoutOptions: { value: BatchListLayout; icon: typeof List; label: string }[] = [
    { value: 'vertical', icon: List, label: 'Vertical' },
    { value: 'horizontal', icon: LayoutGrid, label: 'Horizontal' },
    { value: 'grid', icon: Grid3X3, label: 'Grid' },
  ];

  // Filter by status and sort by slotId (ascending)
  const filteredBatches = useMemo(() => {
    const filtered = statusFilter === 'all' ? batches : batches.filter((b) => b.status === statusFilter);
    // Sort by slotId: batches with slotId come first (ascending), then batches without slotId
    return [...filtered].sort((a, b) => {
      const slotA = a.slotId ?? 999;
      const slotB = b.slotId ?? 999;
      return slotA - slotB;
    });
  }, [batches, statusFilter]);

  const statusOptions = [
    { value: 'all', label: 'All Status' },
    { value: 'idle', label: 'Idle' },
    { value: 'running', label: 'Running' },
    { value: 'completed', label: 'Completed' },
    { value: 'error', label: 'Error' },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>Batches ({filteredBatches.length})</h3>
        <div className="flex items-center gap-3">
          {/* Layout toggle buttons */}
          <div className="flex rounded-lg p-1" style={{ backgroundColor: 'var(--color-bg-tertiary)' }}>
            {layoutOptions.map(({ value, icon: Icon, label }) => (
              <button
                key={value}
                onClick={() => setBatchListLayout(value)}
                className={`p-2 rounded-md transition-colors ${
                  batchListLayout === value
                    ? 'text-white'
                    : 'hover:bg-white/10'
                }`}
                style={{
                  backgroundColor: batchListLayout === value ? 'var(--color-brand-500)' : 'transparent',
                  color: batchListLayout === value ? 'white' : 'var(--color-text-secondary)',
                }}
                title={label}
              >
                <Icon className="w-4 h-4" />
              </button>
            ))}
          </div>
          {/* Status filter */}
          <div className="w-40">
            <Select
              options={statusOptions}
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as BatchStatus | 'all')}
            />
          </div>
        </div>
      </div>

      {filteredBatches.length === 0 ? (
        <div className="p-8 text-center rounded-lg border" style={{ backgroundColor: 'var(--color-bg-secondary)', borderColor: 'var(--color-border-default)', color: 'var(--color-text-tertiary)' }}>
          {statusFilter === 'all' ? 'No batches configured' : `No ${statusFilter} batches`}
        </div>
      ) : (
        <div className={gridClasses}>
          {filteredBatches.map((batch) => (
            <BatchCard
              key={batch.id}
              batch={batch}
              statistics={batchStats.get(batch.id)}
              onDelete={onDelete}
              onSelect={onSelect}
              onStartSequence={onStartSequence}
              onStopSequence={onStopSequence}
              isLoading={isLoading}
              isSelected={batch.id === selectedBatchId}
              isStartingSequence={isStartingSequence}
            />
          ))}
        </div>
      )}
    </div>
  );
}
