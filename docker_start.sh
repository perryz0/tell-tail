#!/bin/bash

# Build and start the Docker containers
echo "Building and starting TellTail API server..."
docker-compose up --build -d

# Check if the container started successfully
if [ $? -eq 0 ]; then
    echo "TellTail API server is now running at http://localhost:5000"
    echo "To view logs: docker-compose logs -f"
    echo "To stop the server: docker-compose down"
else
    echo "Failed to start the TellTail API server. Please check the logs."
fi 