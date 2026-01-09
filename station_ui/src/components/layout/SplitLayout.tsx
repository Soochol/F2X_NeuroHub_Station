/**
 * Split Layout component with resizable right panel.
 * Used for pages that need a main content area with a collapsible side panel.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';

interface SplitLayoutProps {
  /** Main content */
  children: ReactNode;
  /** Right panel content */
  panel: ReactNode;
  /** Panel width in pixels */
  panelWidth: number;
  /** Whether panel is collapsed */
  isCollapsed: boolean;
  /** Callback when panel width changes */
  onResize: (width: number) => void;
  /** Minimum panel width (default: 280) */
  minWidth?: number;
  /** Maximum panel width (default: 600) */
  maxWidth?: number;
  /** Panel title (optional) */
  panelTitle?: string;
}

export function SplitLayout({
  children,
  panel,
  panelWidth,
  isCollapsed,
  onResize,
  minWidth = 280,
  maxWidth = 600,
  panelTitle = 'Details',
}: SplitLayoutProps) {
  const [isResizing, setIsResizing] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const startXRef = useRef(0);
  const startWidthRef = useRef(0);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      setIsResizing(true);
      startXRef.current = e.clientX;
      startWidthRef.current = panelWidth;
    },
    [panelWidth]
  );

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isResizing) return;

      // Calculate new width (dragging left increases width)
      const delta = startXRef.current - e.clientX;
      const newWidth = Math.min(maxWidth, Math.max(minWidth, startWidthRef.current + delta));
      onResize(newWidth);
    },
    [isResizing, minWidth, maxWidth, onResize]
  );

  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
  }, []);

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, handleMouseMove, handleMouseUp]);

  return (
    <div ref={containerRef} className="flex h-full w-full overflow-hidden">
      {/* Main content area */}
      <div
        className="flex-1 overflow-auto transition-all duration-200"
        style={{
          marginRight: isCollapsed ? 0 : panelWidth,
        }}
      >
        {children}
      </div>

      {/* Toggle button removed - panel is now always open */}

      {/* Right panel */}
      <div
        className={`fixed right-0 top-[60px] h-[calc(100vh-60px)] flex flex-col border-l transition-transform duration-200 z-30 ${
          isCollapsed ? 'translate-x-full' : 'translate-x-0'
        }`}
        style={{
          width: panelWidth,
          backgroundColor: 'var(--color-bg-secondary)',
          borderColor: 'var(--color-border-default)',
        }}
      >
        {/* Resize handle */}
        <div
          onMouseDown={handleMouseDown}
          className={`absolute left-0 top-0 h-full w-1 cursor-col-resize transition-colors ${
            isResizing ? 'bg-brand-500' : 'hover:bg-brand-500/50'
          }`}
          style={{ transform: 'translateX(-50%)' }}
        />

        {/* Panel header */}
        <div
          className="flex items-center justify-center px-3 py-2 border-b shrink-0"
          style={{ borderColor: 'var(--color-border-default)' }}
        >
          <span className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>
            {panelTitle}
          </span>
        </div>

        {/* Panel content */}
        <div className="flex-1 overflow-hidden">{panel}</div>
      </div>
    </div>
  );
}
