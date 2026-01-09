/**
 * LogFilters - Filter controls for debug log panel.
 * Matches LogsPage filter section design.
 */

import { Filter, Pause, Play } from 'lucide-react';
import { useDebugPanelStore } from '../../../stores/debugPanelStore';
import { Select } from '../../atoms/Select';
import { Input } from '../../atoms/Input';
import { Button } from '../../atoms/Button';
import type { LogLevel } from '../../../types';

interface LogFiltersProps {
  /** Available step names for filtering */
  stepNames: string[];
  /** Whether auto-scroll is enabled */
  autoScroll: boolean;
  /** Callback to toggle auto-scroll */
  onToggleAutoScroll: () => void;
}

const levelOptions = [
  { value: '', label: 'All Levels' },
  { value: 'debug', label: 'Debug' },
  { value: 'info', label: 'Info' },
  { value: 'warning', label: 'Warning' },
  { value: 'error', label: 'Error' },
];

export function LogFilters({ stepNames, autoScroll, onToggleAutoScroll }: LogFiltersProps) {
  const { selectedStep, logLevel, searchQuery, setSelectedStep, setLogLevel, setSearchQuery } =
    useDebugPanelStore();

  const stepOptions = [
    { value: '', label: 'All Steps' },
    ...stepNames.map((name) => ({ value: name, label: name })),
  ];

  return (
    <div
      className="p-3 rounded-lg border m-2"
      style={{
        backgroundColor: 'var(--color-bg-secondary)',
        borderColor: 'var(--color-border-default)',
      }}
    >
      {/* Filters label */}
      <div className="flex items-center gap-2 mb-3">
        <Filter className="w-4 h-4" style={{ color: 'var(--color-text-secondary)' }} />
        <span className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>
          Filters
        </span>
      </div>

      {/* Grid layout: Step / Level / Search / Auto-scroll button */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
        <Select
          value={selectedStep || ''}
          onChange={(e) => setSelectedStep(e.target.value || null)}
          className="text-xs"
          placeholder="All Steps"
          options={stepOptions}
        />
        <Select
          value={logLevel || ''}
          onChange={(e) => setLogLevel((e.target.value as LogLevel) || null)}
          className="text-xs"
          placeholder="All Levels"
          options={levelOptions}
        />
        <Input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search logs..."
          className="text-xs"
        />
        <div className="flex items-center justify-end">
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleAutoScroll}
            title={autoScroll ? 'Pause auto-scroll' : 'Resume auto-scroll'}
          >
            {autoScroll ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </Button>
        </div>
      </div>
    </div>
  );
}
