import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { copyToClipboard } from './clipboard';

describe('copyToClipboard', () => {
    const originalClipboard = navigator.clipboard;
    const originalIsSecureContext = window.isSecureContext;
    const originalExecCommand = document.execCommand;

    beforeEach(() => {
        vi.clearAllMocks();
        // Reset globals
        Object.defineProperty(window, 'isSecureContext', {
            value: true,
            configurable: true,
        });
        // Mock document.execCommand
        document.execCommand = vi.fn().mockReturnValue(true);
        // Mock document.body.appendChild/removeChild to avoid DOM clutter
        vi.spyOn(document.body, 'appendChild').mockImplementation((node) => node);
        vi.spyOn(document.body, 'removeChild').mockImplementation((node) => node);
    });

    afterEach(() => {
        Object.defineProperty(navigator, 'clipboard', {
            value: originalClipboard,
            configurable: true,
        });
        Object.defineProperty(window, 'isSecureContext', {
            value: originalIsSecureContext,
            configurable: true,
        });
        document.execCommand = originalExecCommand;
        vi.restoreAllMocks();
    });

    it('should use navigator.clipboard in secure context', async () => {
        const writeTextMock = vi.fn().mockResolvedValue(undefined);
        Object.defineProperty(navigator, 'clipboard', {
            value: { writeText: writeTextMock },
            configurable: true,
        });

        const result = await copyToClipboard('test text');

        expect(result).toBe(true);
        expect(writeTextMock).toHaveBeenCalledWith('test text');
        expect(document.execCommand).not.toHaveBeenCalled();
    });

    it('should fallback to execCommand in non-secure context', async () => {
        Object.defineProperty(window, 'isSecureContext', {
            value: false,
            configurable: true,
        });
        // Even if navigator.clipboard exists, it shouldn't be used if not secure context
        const writeTextMock = vi.fn();
        Object.defineProperty(navigator, 'clipboard', {
            value: { writeText: writeTextMock },
            configurable: true,
        });

        const result = await copyToClipboard('test text');

        expect(result).toBe(true);
        expect(writeTextMock).not.toHaveBeenCalled();
        expect(document.execCommand).toHaveBeenCalledWith('copy');
    });

    it('should fallback to execCommand if navigator.clipboard is missing', async () => {
        Object.defineProperty(navigator, 'clipboard', {
            value: undefined,
            configurable: true,
        });

        const result = await copyToClipboard('test text');

        expect(result).toBe(true);
        expect(document.execCommand).toHaveBeenCalledWith('copy');
    });

    it('should return false if both methods fail', async () => {
        Object.defineProperty(navigator, 'clipboard', {
            value: undefined,
            configurable: true,
        });
        document.execCommand = vi.fn().mockReturnValue(false);

        const result = await copyToClipboard('test text');

        expect(result).toBe(false);
    });
});
