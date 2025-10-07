FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY runtime_agent_main.py .

# Expose port
EXPOSE 8000

# Run with OpenTelemetry instrumentation
CMD ["opentelemetry-instrument", "python", "runtime_agent_main.py"]
