/**
 * Clipboard utility to handle copying text to clipboard.
 * Includes a fallback for non-secure contexts (HTTP) where navigator.clipboard is unavailable.
 */

/**
 * Copies text to the clipboard.
 * @param text The string to copy.
 * @returns A promise that resolves to true if successful, false otherwise.
 */
export async function copyToClipboard(text: string): Promise<boolean> {
    // Try modern Clipboard API first (requires secure context)
    if (navigator.clipboard && window.isSecureContext) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.error('Modern clipboard copy failed:', err);
            // Fall through to legacy method
        }
    }

    // Fallback to legacy document.execCommand('copy')
    try {
        const textArea = document.createElement('textarea');
        textArea.value = text;

        // Ensure the textarea is not visible but part of the DOM
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        textArea.style.top = '0';
        document.body.appendChild(textArea);

        textArea.focus();
        textArea.select();

        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);

        return successful;
    } catch (err) {
        console.error('Fallback clipboard copy failed:', err);
        return false;
    }
}
