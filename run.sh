sudo docker run --rm \
    -v "$(pwd)/app:/app" \
    -v "$(pwd)/app/logs:/app/logs" \
    -v "$(pwd)/app/graphs:/app/graphs" \
    my-trading-bot

