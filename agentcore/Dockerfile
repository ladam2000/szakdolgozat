FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY agent.py .

# Expose port
EXPOSE 8000

# Run with Strands agent
CMD ["python", "-m", "strands.serve", "agent:agent", "--host", "0.0.0.0", "--port", "8000"]
