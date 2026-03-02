/**
 * Text Extractor - Extract text from video frames using OCR
 * Captures paused video frames and runs Tesseract.js OCR
 */

// Add global styles to prevent ResizeObserver issues
const style = document.createElement('style');
style.textContent = `
    #text-extractor-button {
        all: initial;
        box-sizing: border-box;
        font-family: inherit;
    }
    
    #text-extractor-overlay {
        all: initial;
        box-sizing: border-box;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    #text-extractor-overlay * {
        box-sizing: border-box;
    }
`;
try {
    document.head.appendChild(style);
} catch (e) {
    // If head not available, try body
    setTimeout(() => {
        try {
            document.head.appendChild(style);
        } catch (e2) {
            console.warn('[TextExtractor] Could not add styles');
        }
    }, 100);
}

class TextExtractor {
    constructor() {
        this.videoElement = null;
        this.isProcessing = false;
        this.overlayPanel = null;
        this.worker = null;
        console.log('[TextExtractor] Initialized');
    }

    /**
     * Initialize Tesseract.js worker
     */
    async initTesseract() {
        try {
            if (!this.worker) {
                console.log('[TextExtractor] Loading Tesseract.js worker...');
                const { createWorker } = Tesseract;
                this.worker = await createWorker('eng');
                console.log('[TextExtractor] Tesseract worker loaded successfully');
            }
            return true;
        } catch (error) {
            console.error('[TextExtractor] Failed to initialize Tesseract:', error);
            this.showError('Failed to load OCR engine. Please refresh the page.');
            return false;
        }
    }

    /**
     * Suppress ResizeObserver errors globally
     */
    suppressResizeObserverErrors() {
        const originalError = console.error;
        console.error = function(...args) {
            if (args[0] && typeof args[0] === 'string' && args[0].includes('ResizeObserver')) {
                return; // Suppress ResizeObserver errors
            }
            originalError.apply(console, args);
        };
    }

    /**
     * Detect video element on the page
     */
    detectVideo() {
        console.log('[TextExtractor] Detecting video element...');
        
        // Try different video selectors, with priority for YouTube
        const selectors = [
            'video',
            '.html5-main-video',
            'video.video-stream',
            'ytd-video-container video',
            'video[class*="video"]',
            '[role="region"] video'
        ];

        for (const selector of selectors) {
            const video = document.querySelector(selector);
            if (video && video.videoWidth > 0) {
                console.log('[TextExtractor] Video found with selector:', selector);
                this.videoElement = video;
                this.attachVideoListener();
                this.startPauseDetection();
                return true;
            }
        }

        // If no video found, try finding it in hidden elements
        const allVideos = document.querySelectorAll('video');
        if (allVideos.length > 0) {
            for (const video of allVideos) {
                if (video.videoWidth > 0) {
                    console.log('[TextExtractor] Video found in fallback search');
                    this.videoElement = video;
                    this.attachVideoListener();
                    this.startPauseDetection();
                    return true;
                }
            }
        }

        console.warn('[TextExtractor] No video element found');
        this.showError('No video element detected. Please play a YouTube video first.');
        return false;
    }

    /**
     * Start continuous pause detection for YouTube
     */
    startPauseDetection() {
        console.log('[TextExtractor] Starting pause detection polling...');
        
        let wasPaused = false;
        let detectionInterval = null;
        
        detectionInterval = setInterval(() => {
            if (!this.videoElement) {
                clearInterval(detectionInterval);
                return;
            }
            
            const isPaused = this.videoElement.paused;
            
            // Detect pause state change
            if (isPaused && !wasPaused) {
                console.log('[TextExtractor] Pause detected via polling');
                this.showExtractionButton();
            } else if (!isPaused && wasPaused) {
                console.log('[TextExtractor] Play detected via polling');
                this.hideExtractionButton();
            }
            
            wasPaused = isPaused;
        }, 250); // Reduced frequency to avoid performance issues
    }

    /**
     * Attach pause event listener to video
     */
    attachVideoListener() {
        if (!this.videoElement) return;

        console.log('[TextExtractor] Attaching pause event listener');
        
        this.videoElement.addEventListener('pause', () => {
            console.log('[TextExtractor] Video paused, showing extraction button...');
            this.showExtractionButton();
        }, { once: false });

        // Remove button when video resumes
        this.videoElement.addEventListener('play', () => {
            console.log('[TextExtractor] Video resumed, hiding extraction button');
            this.hideExtractionButton();
        }, { once: false });
    }

    /**
     * Show extraction button on paused video
     */
    showExtractionButton() {
        // Remove existing button if any
        const existing = document.getElementById('text-extractor-button');
        if (existing) {
            existing.style.opacity = '1';
            existing.style.visibility = 'visible';
            existing.style.pointerEvents = 'auto';
            return; // Button already exists, just show it
        }

        // Create button overlay with better positioning for YouTube
        const button = document.createElement('button');
        button.id = 'text-extractor-button';
        button.textContent = '📋 Extract Text';
        button.type = 'button';
        
        // Use a class-based approach to minimize DOM reflows
        button.className = 'text-extractor-btn';
        
        // Set initial position
        const rect = this.videoElement.getBoundingClientRect();
        const topPos = window.scrollY + rect.top + (rect.height / 2) - 25;
        const leftPos = window.scrollX + rect.left + (rect.width / 2) - 100;
        
        button.style.cssText = `
            position: fixed;
            top: ${topPos}px;
            left: ${leftPos}px;
            width: 200px;
            padding: 12px 20px;
            background: linear-gradient(135deg, #2c5282 0%, #1a365d 100%);
            color: white;
            border: 3px solid #4a7c9e;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 6px 20px rgba(0,0,0,0.4);
            z-index: 99999;
            transition: all 0.3s ease;
            opacity: 1 !important;
            visibility: visible !important;
            display: block !important;
            pointer-events: auto !important;
        `;

        button.addEventListener('mouseenter', (e) => {
            if (!e.target) return;
            e.target.style.background = 'linear-gradient(135deg, #2c5282 0%, #0d2438 100%)';
            e.target.style.transform = 'scale(1.08)';
            e.target.style.boxShadow = '0 8px 24px rgba(0,0,0,0.5)';
        }, { passive: true });

        button.addEventListener('mouseleave', (e) => {
            if (!e.target) return;
            e.target.style.background = 'linear-gradient(135deg, #2c5282 0%, #1a365d 100%)';
            e.target.style.transform = 'scale(1)';
            e.target.style.boxShadow = '0 6px 20px rgba(0,0,0,0.4)';
        }, { passive: true });

        button.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            // Send a custom event to the backend to open Firefox
            try {
                // Remove the button as before
                const btn = document.getElementById('text-extractor-button');
                if (btn) btn.remove();

                // Try to send a message to the backend (PyQt) to open Firefox
                if (window.qt && window.qt.webChannelTransport) {
                    // If using QWebChannel, send a signal
                    new QWebChannel(window.qt.webChannelTransport, function(channel) {
                        if (channel.objects && channel.objects.backend) {
                            channel.objects.backend.openFirefox();
                        }
                    });
                } else if (window.pywebview) {
                    // If using pywebview, use its API
                    window.pywebview.api.open_firefox();
                } else {
                    // Fallback: try to post a message for a custom handler
                    window.postMessage({ type: 'open_firefox' }, '*');
                }
            } catch (err) {
                console.error('[TextExtractor] Click handler error:', err);
            }
        }, { passive: false });

        document.body.appendChild(button);
        console.log(`[TextExtractor] Extraction button shown at position (${leftPos}, ${topPos})`);

    }

    /**
     * Hide extraction button
     */
    hideExtractionButton() {
        const button = document.getElementById('text-extractor-button');
        if (button) {
            button.remove();
        }
    }

    /**
     * Capture video frame to canvas
     */
    captureFrame() {
        console.log('[TextExtractor] Capturing frame...');
        
        if (!this.videoElement || this.videoElement.paused === false) {
            throw new Error('Video is not paused');
        }

        try {
            // Create canvas
            const canvas = document.createElement('canvas');
            canvas.width = this.videoElement.videoWidth;
            canvas.height = this.videoElement.videoHeight;

            if (canvas.width === 0 || canvas.height === 0) {
                throw new Error('Video dimensions are invalid');
            }

            // Draw current frame
            const ctx = canvas.getContext('2d');
            ctx.drawImage(this.videoElement, 0, 0);

            console.log(`[TextExtractor] Frame captured: ${canvas.width}x${canvas.height}`);
            return canvas;
        } catch (error) {
            console.error('[TextExtractor] Frame capture failed:', error);
            throw error;
        }
    }

    /**
     * Downscale image for faster OCR
     */
    downscaleImage(canvas, maxWidth = 1024, maxHeight = 768) {
        console.log('[TextExtractor] Downscaling image for OCR...');
        
        const width = canvas.width;
        const height = canvas.height;
        let newWidth = width;
        let newHeight = height;

        // Calculate new dimensions maintaining aspect ratio
        if (width > maxWidth) {
            newWidth = maxWidth;
            newHeight = (height * maxWidth) / width;
        }
        if (newHeight > maxHeight) {
            newHeight = maxHeight;
            newWidth = (newWidth * maxHeight) / newHeight;
        }

        if (newWidth === width && newHeight === height) {
            console.log('[TextExtractor] Image already optimized');
            return canvas;
        }

        const scaledCanvas = document.createElement('canvas');
        scaledCanvas.width = newWidth;
        scaledCanvas.height = newHeight;
        const ctx = scaledCanvas.getContext('2d');
        ctx.drawImage(canvas, 0, 0, newWidth, newHeight);

        console.log(`[TextExtractor] Image downscaled to: ${newWidth}x${newHeight}`);
        return scaledCanvas;
    }

    /**
     * Run OCR on image
     */
    async runOCR(canvas) {
        console.log('[TextExtractor] Starting OCR...');
        
        if (!this.worker) {
            throw new Error('Tesseract worker not initialized');
        }

        try {
            // Convert canvas to image data
            const imageData = canvas.toDataURL('image/png');

            // Downscale for performance
            const scaledCanvas = this.downscaleImage(canvas);
            const scaledImageData = scaledCanvas.toDataURL('image/png');

            // Run OCR
            const { data: { text, confidence } } = await this.worker.recognize(scaledImageData);

            console.log(`[TextExtractor] OCR completed. Confidence: ${confidence.toFixed(2)}%`);
            return {
                text: text.trim(),
                confidence: confidence
            };
        } catch (error) {
            console.error('[TextExtractor] OCR failed:', error);
            throw error;
        }
    }

    /**
     * Capture and extract text flow
     */
    async captureAndExtract() {
        try {
            if (this.isProcessing) {
                console.log('[TextExtractor] Already processing, skipping...');
                return;
            }

            this.isProcessing = true;

            // Show processing animation
            await this.showProcessing();

            // Ensure Tesseract is initialized
            const tessReady = await this.initTesseract();
            if (!tessReady) {
                this.showError('Failed to initialize OCR engine. Please try again.');
                this.isProcessing = false;
                return;
            }

            // Small delay to ensure UI updates
            await new Promise(resolve => setTimeout(resolve, 800));

            // Capture frame
            const canvas = this.captureFrame();

            // Run OCR
            const result = await this.runOCR(canvas);

            // Display result
            this.displayText(result.text, result.confidence);

            console.log('[TextExtractor] Text extraction complete');
        } catch (error) {
            console.error('[TextExtractor] Extraction failed:', error);
            this.showError(`Error: ${error.message}`);
        } finally {
            this.isProcessing = false;
        }
    }

    /**
     * Create overlay panel
     */
    createOverlayPanel() {
        console.log('[TextExtractor] Creating overlay panel...');
        
        const overlay = document.createElement('div');
        overlay.id = 'text-extractor-overlay';
        overlay.innerHTML = `
            <div style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 420px;
                max-height: 600px;
                background: #ffffff;
                border: 3px solid #2c5282;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 6px 24px rgba(0,0,0,0.2);
                z-index: 99998;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                flex-direction: column;
                transition: all 0.3s ease;
            ">
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                    border-bottom: 3px solid #2c5282;
                    padding-bottom: 12px;
                ">
                    <h3 style="margin: 0; font-size: 15px; font-weight: 700; color: #1a365d;">📋 Extracted Text</h3>
                    <button id="close-overlay" style="
                        background: none;
                        border: none;
                        font-size: 26px;
                        cursor: pointer;
                        color: #cbd5e0;
                        padding: 0;
                        width: 28px;
                        height: 28px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        transition: color 0.2s;
                        border-radius: 4px;
                    " onmouseover="this.style.color='#2c5282'; this.style.background='#f0f4f8'" onmouseout="this.style.color='#cbd5e0'; this.style.background='transparent'">×</button>
                </div>
                <div id="text-content" style="
                    flex: 1;
                    color: #333;
                    font-size: 13px;
                    line-height: 1.6;
                    margin-bottom: 15px;
                    overflow-y: auto;
                    border-radius: 6px;
                "></div>
                <div id="confidence-meter" style="
                    display: none;
                    font-size: 12px;
                    color: #2c5282;
                    margin-bottom: 15px;
                "></div>
                <div style="display: flex; gap: 10px;">
                    <button id="copy-text" style="
                        flex: 1;
                        padding: 11px 16px;
                        background: linear-gradient(135deg, #2c5282 0%, #1a365d 100%);
                        color: white;
                        border: 2px solid #2c5282;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 13px;
                        font-weight: 700;
                        transition: all 0.3s;
                    " onmouseover="this.style.background='linear-gradient(135deg, #1a365d 0%, #0d2438 100%)'; this.style.boxShadow='0 4px 12px rgba(44,82,130,0.4)'; this.style.transform='translateY(-2px)'" onmouseout="this.style.background='linear-gradient(135deg, #2c5282 0%, #1a365d 100%)'; this.style.boxShadow='none'; this.style.transform='translateY(0)'">📋 Copy</button>
                    <button id="close-overlay-btn" style="
                        flex: 1;
                        padding: 11px 16px;
                        background: #f0f4f8;
                        color: #2c5282;
                        border: 2px solid #cbd5e0;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 13px;
                        font-weight: 700;
                        transition: all 0.3s;
                    " onmouseover="this.style.background='#e6f0ff'; this.style.borderColor='#4a7c9e'" onmouseout="this.style.background='#f0f4f8'; this.style.borderColor='#cbd5e0'">Close</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Event listeners
        document.getElementById('copy-text').addEventListener('click', () => {
            const text = document.getElementById('text-content').textContent;
            if (text && text.trim().length > 0) {
                navigator.clipboard.writeText(text).then(() => {
                    // Show success feedback
                    const btn = document.getElementById('copy-text');
                    const originalText = btn.textContent;
                    const originalStyle = btn.style.background;
                    btn.textContent = '✓ Copied!';
                    btn.style.background = 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)';
                    btn.style.borderColor = '#4caf50';
                    setTimeout(() => {
                        btn.textContent = originalText;
                        btn.style.background = originalStyle;
                        btn.style.borderColor = '#2c5282';
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy:', err);
                    alert('Failed to copy text to clipboard');
                });
            }
        });

        document.getElementById('close-overlay').addEventListener('click', () => overlay.remove());
        document.getElementById('close-overlay-btn').addEventListener('click', () => overlay.remove());

        this.overlayPanel = overlay;
        return overlay;
    }

    /**
     * Display extracted text
     */
    displayText(text, confidence = 0) {
        console.log('[TextExtractor] Displaying extracted text');
        
        try {
            if (!this.overlayPanel) {
                this.createOverlayPanel();
            }

            // Update text content with enhanced styling
            const contentDiv = document.getElementById('text-content');
            if (!contentDiv) {
                console.warn('[TextExtractor] Content div not found');
                return;
            }
            
            if (text && text.length > 0) {
                contentDiv.innerHTML = `
                    <div style="
                        padding: 10px;
                        background: #f9f9f9;
                        border-radius: 4px;
                        max-height: 350px;
                        overflow-y: auto;
                    ">
                        <p style="
                            margin: 0;
                            color: #333;
                            font-size: 13px;
                            line-height: 1.6;
                        white-space: pre-wrap;
                        word-break: break-word;
                        font-family: 'Segoe UI', sans-serif;
                    ">${text}</p>
                </div>
            `;
        } else {
            contentDiv.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;"><p style="margin: 0;">ℹ️ No text detected in this frame</p></div>';
        }

        // Update confidence meter
        const confidenceDiv = document.getElementById('confidence-meter');
        if (confidence > 0) {
            confidenceDiv.style.display = 'block';
            const confPercentage = (confidence * 100).toFixed(1);
            const confColor = confidence > 0.7 ? '#4caf50' : confidence > 0.5 ? '#ff9800' : '#f44336';
            confidenceDiv.innerHTML = `
                <div style="font-size: 11px; color: #666; margin-bottom: 5px;">
                    Confidence: <span style="color: ${confColor}; font-weight: bold;">${confPercentage}%</span>
                </div>
                <div style="
                    height: 4px;
                    background: #e0e0e0;
                    border-radius: 2px;
                    overflow: hidden;
                ">
                    <div style="
                        height: 100%;
                        background: ${confColor};
                        width: ${confPercentage}%;
                        transition: width 0.3s ease;
                    "></div>
                </div>
            `;
        } else {
            confidenceDiv.style.display = 'none';
        }

        // Reset panel styling
        this.overlayPanel.style.borderColor = '#e0e0e0';
        this.overlayPanel.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        this.overlayPanel.style.display = 'block';
        
        console.log('[TextExtractor] Text displayed successfully');
    }

    /**
     * Show processing state with loading animation
     */
    async showProcessing() {
        if (!this.overlayPanel) {
            this.createOverlayPanel();
        }
        
        const contentDiv = document.getElementById('text-content');
        contentDiv.innerHTML = `
            <div style="text-align: center; padding: 40px 20px;">
                <div style="
                    width: 50px;
                    height: 50px;
                    margin: 0 auto 20px;
                    border: 4px solid #e6f0ff;
                    border-top: 4px solid #2c5282;
                    border-right: 4px solid #4a7c9e;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                "></div>
                <p style="margin: 0; font-size: 14px; font-weight: 700; color: #1a365d;">Processing Frame...</p>
                <p style="margin: 10px 0 0 0; font-size: 11px; color: #4a7c9e;">🔍 Running OCR on video frame</p>
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        `;
        
        // Highlight border
        this.overlayPanel.style.borderColor = '#2c5282';
        this.overlayPanel.style.boxShadow = '0 6px 24px rgba(44, 82, 130, 0.4)';
        this.overlayPanel.style.display = 'block';
        
        console.log('[TextExtractor] Processing state shown with loading animation');
    }

    /**
     * Show error message
     */
    showError(message) {
        console.error('[TextExtractor] Error:', message);
        if (!this.overlayPanel) {
            this.createOverlayPanel();
        }
        const contentDiv = document.getElementById('text-content');
        contentDiv.innerHTML = `
            <div style="
                padding: 20px;
                text-align: center;
                background: #fef2f2;
                border: 2px solid #fecaca;
                border-radius: 6px;
            ">
                <p style="margin: 0 0 8px 0; font-size: 24px;">⚠️</p>
                <p style="margin: 0; color: #dc2626; font-size: 13px; line-height: 1.5; font-weight: 600;">${message}</p>
            </div>
        `;
        this.overlayPanel.style.borderColor = '#dc2626';
        this.overlayPanel.style.display = 'block';
    }

    /**
     * Initialize text extractor on page
     */
    async initialize() {
        console.log('[TextExtractor] Initializing on page...');
        
        try {
            // Wait for page to load
            if (document.readyState !== 'complete') {
                await new Promise(resolve => {
                    window.addEventListener('load', resolve, { once: true });
                    // Fallback timeout
                    setTimeout(resolve, 3000);
                });
            }

            // Initialize Tesseract
            const tessReady = await this.initTesseract();
            if (!tessReady) return;

            // Detect video with retries
            let videoFound = this.detectVideo();
            
            if (!videoFound) {
                // Retry detection after delay for YouTube's lazy loading
                console.log('[TextExtractor] Retrying video detection after 2000ms...');
                setTimeout(() => {
                    if (!this.videoElement) {
                        this.detectVideo();
                    }
                }, 2000);
                
                // Another retry after more time
                setTimeout(() => {
                    if (!this.videoElement) {
                        console.log('[TextExtractor] Final retry after 4000ms...');
                        this.detectVideo();
                    }
                }, 4000);
            }

            console.log('[TextExtractor] Ready for text extraction');
        } catch (error) {
            console.error('[TextExtractor] Initialization failed:', error);
            this.showError('Failed to initialize Text Extractor: ' + error.message);
        }
    }

    /**
     * Cleanup resources
     */
    async cleanup() {
        console.log('[TextExtractor] Cleaning up...');
        if (this.worker) {
            await this.worker.terminate();
            this.worker = null;
        }
    }
}

// Auto-initialize on page load with proper error handling
(async () => {
    console.log('[TextExtractor] Script loaded');
    
    try {
        // Suppress ResizeObserver errors
        const originalError = console.error;
        let errorSuppressed = false;
        console.error = function(...args) {
            if (args[0] && typeof args[0] === 'string' && args[0].includes('ResizeObserver')) {
                if (!errorSuppressed) {
                    console.warn('[TextExtractor] ResizeObserver errors suppressed');
                    errorSuppressed = true;
                }
                return; // Suppress ResizeObserver errors
            }
            originalError.apply(console, args);
        };

        // Load Tesseract.js if not already loaded
        if (typeof Tesseract === 'undefined') {
            console.log('[TextExtractor] Loading Tesseract.js library...');
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/tesseract.js@4/dist/tesseract.min.js';
            script.async = true;
            script.defer = true;
            
            script.onload = () => {
                console.log('[TextExtractor] Tesseract.js loaded successfully');
                const extractor = new TextExtractor();
                window.textExtractor = extractor;
                extractor.suppressResizeObserverErrors();
                extractor.initialize();
            };
            
            script.onerror = () => {
                console.error('[TextExtractor] Failed to load Tesseract.js');
            };
            
            // Add preload link to header for faster loading
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = 'script';
            link.href = 'https://cdn.jsdelivr.net/npm/tesseract.js@4/dist/tesseract.min.js';
            link.crossOrigin = 'anonymous';
            if (document.head) {
                document.head.insertBefore(link, document.head.firstChild);
            }
            
            document.head.appendChild(script);
        } else {
            const extractor = new TextExtractor();
            window.textExtractor = extractor;
            extractor.suppressResizeObserverErrors();
            extractor.initialize();
        }
    } catch (error) {
        console.error('[TextExtractor] Initialization error:', error);
    }
})();
