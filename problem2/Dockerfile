# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy main script into the container
COPY arxiv_processor.py /app/

# Create output directory for results
RUN mkdir -p /data/output

# Default entrypoint runs the processor
ENTRYPOINT ["python", "/app/arxiv_processor.py"]
