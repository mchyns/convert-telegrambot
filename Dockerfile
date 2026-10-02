FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install LibreOffice headless, system fonts, and required packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-nogui \
    libreoffice-writer \
    fonts-dejavu-core \
    fonts-liberation \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app/ ./app/

# Create temporary directory
RUN mkdir -p /tmp/docpdf

# Expose Render PORT (default 10000 or dynamic $PORT)
EXPOSE 10000

CMD ["python", "-m", "app.main"]
