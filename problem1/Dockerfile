# Problem 1 - Part B: Dockerfile
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Prepare mount points for input/output
RUN mkdir -p /data/input /data/output

# Copy script into container
COPY fetch_and_process.py /app/

# Run script by default
ENTRYPOINT ["python", "/app/fetch_and_process.py"]

# Default args (can be overridden by run.sh)
CMD ["/data/input/urls.txt", "/data/output"]
