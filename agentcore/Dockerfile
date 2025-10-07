FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY runtime_agent_main.py .

# Expose port
EXPOSE 8000

# Keep container running - AgentCore will invoke the agent
CMD ["opentelemetry-instrument", "python", "runtime_agent_main.py"]
