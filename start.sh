#!/bin/bash

# Start the FastAPI server
echo "Starting FastAPI server..."
uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8000} &
P1=$!

# Start the Discord bot
echo "Starting Discord bot..."
API_URL="http://localhost:${PORT:-8000}/api/v1/bot" python discord/bot.py &
P2=$!

# Wait for both processes to finish
# If either fails, the script will exit
wait -n $P1 $P2

# Exit with the status of the first process that failed
exit $?
