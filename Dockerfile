FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=web.server
ENV FLASK_ENV=production

# Create directories for session storage
RUN mkdir -p /app/flask_session

# Expose port
EXPOSE 5000

# Command to run the application
CMD ["python", "-m", "web.server"] 