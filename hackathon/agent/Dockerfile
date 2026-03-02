# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — AI Multi-Tab Browser Agent
# ─────────────────────────────────────────────────────────────────────────────
# Build:   docker build -t ai-browser-agent .
# Run:     docker run --rm -e GEMINI_API_KEY=your_key ai-browser-agent \
#              --task "Compare RTX 4060 prices on Amazon and Flipkart" \
#              --headless --no-preview
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# System dependencies for Chromium / Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg ca-certificates \
    libglib2.0-0 libnss3 libnspr4 libdbus-1-3 \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2 \
    fonts-liberation libpango-1.0-0 libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY agent/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright + Chromium browser binaries
RUN playwright install chromium --with-deps

# Copy agent source
COPY agent/ ./

# Environment defaults (override via docker run -e)
ENV GEMINI_API_KEY="AIzaSyC_Q1cIU0ba4iMCU1RnBGtbszv0XCfIWuw"
ENV HEADLESS="true"
ENV PREVIEW_WS_PORT="8765"
ENV PREVIEW_INTERVAL="1.5"

# Expose preview WebSocket port
EXPOSE 8765

# Default command
ENTRYPOINT ["python", "main.py"]
CMD ["--task", "Compare RTX 4060 laptop prices on Amazon and Flipkart", "--headless", "--no-preview"]
