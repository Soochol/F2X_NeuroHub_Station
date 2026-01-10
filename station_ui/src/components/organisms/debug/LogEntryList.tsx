/**
 * LogEntryList - Log entries display with auto-scroll support.
 * Matches LogsPage design.
 */

import { useEffect, useRef, useCallback, useMemo } from 'react';
import { FileText } from 'lucide-react';
import { useLogStore } from '../../../stores';
import { useDebugPanelStore } from '../../../stores/debugPanelStore';
import { LogEntryRow } from '../../molecules/LogEntryRow';

interface LogEntryListProps {
  /** Batch ID to filter logs */
  batchId: string;
}

export function LogEntryList({ batchId }: LogEntryListProps) {
  const logs = useLogStore((s) => s.logs);
  const { selectedStep, logLevel, searchQuery, autoScroll, setAutoScroll } =
    useDebugPanelStore();

  const containerRef = useRef<HTMLDivElement>(null);
  const prevLogsLengthRef = useRef(logs.length);

  // Filter logs based on current filters
  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      // Filter by batch ID
      if (log.batchId !== batchId) return false;

      // Filter by log level
      if (logLevel && log.level !== logLevel) return false;

      // Filter by search query
      if (searchQuery && !log.message.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }

      // Note: Step filtering would require step name in log entries
      // For now, we search for step name in the message
      if (selectedStep && !log.message.toLowerCase().includes(selectedStep.toLowerCase())) {
        return false;
      }

      return true;
    });
  }, [logs, batchId, selectedStep, logLevel, searchQuery]);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && containerRef.current && logs.length > prevLogsLengthRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
    prevLogsLengthRef.current = logs.length;
  }, [logs.length, autoScroll]);

  // Handle scroll to detect if user scrolled up
  const handleScroll = useCallback(() => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
    if (isAtBottom !== autoScroll) {
      setAutoScroll(isAtBottom);
    }
  }, [autoScroll, setAutoScroll]);

  return (
    <div className="relative flex flex-col h-full">
      {/* Header with entry count */}
      <div
        className="flex items-center justify-between px-3 py-2 border-b"
        style={{
          color: 'var(--color-text-secondary)',
          borderColor: 'var(--color-border-default)',
        }}
      >
        <span className="text-sm">
          Real-time Logs ({filteredLogs.length} entries)
        </span>
        {!autoScroll && (
          <span className="text-xs text-yellow-400">Auto-scroll paused</span>
        )}
      </div>

      {/* Log entries */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto font-mono text-sm"
        style={{ backgroundColor: 'var(--color-bg-secondary)' }}
      >
        {filteredLogs.length === 0 ? (
          <div
            className="flex flex-col items-center justify-center py-12"
            style={{ color: 'var(--color-text-tertiary)' }}
          >
            <FileText className="w-8 h-8 mb-2 opacity-50" />
            <p className="text-sm">
              {selectedStep || logLevel || searchQuery
                ? 'No logs match filters'
                : 'No logs yet. Waiting for activity...'}
            </p>
          </div>
        ) : (
          <div className="p-2">
            {filteredLogs.map((log, index) => (
              <LogEntryRow key={log.id ?? index} log={log} showBatchId={false} />
            ))}
          </div>
        )}
      </div>

      {/* Log Level Legend */}
      <div
        className="flex items-center gap-4 px-3 py-2 text-xs border-t"
        style={{
          color: 'var(--color-text-secondary)',
          borderColor: 'var(--color-border-default)',
          backgroundColor: 'var(--color-bg-tertiary)',
        }}
      >
        <span>Log Levels:</span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-zinc-500" />
          Debug
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-blue-500" />
          Info
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-yellow-500" />
          Warning
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-red-500" />
          Error
        </span>
      </div>
    </div>
  );
}
