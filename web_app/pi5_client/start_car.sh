#!/bin/bash
# Start Car Client - Runs both simulator and sync script

echo "🚗 Starting Car Client..."

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "Installing tmux..."
    sudo apt-get update && sudo apt-get install -y tmux
fi

# Kill existing session if it exists
tmux kill-session -t car_client 2>/dev/null

# Create new tmux session
tmux new-session -d -s car_client

# Window 0: Car Simulator
tmux rename-window -t car_client:0 'Simulator'
tmux send-keys -t car_client:0 'cd ~/pi5_client && python3 car_simulator.py' C-m

# Window 1: Sync Script
tmux new-window -t car_client:1 -n 'Sync'
tmux send-keys -t car_client:1 'cd ~/pi5_client && sleep 2 && python3 sync_to_server.py' C-m

echo ""
echo "✅ Car client started in tmux session 'car_client'"
echo ""
echo "Commands:"
echo "  tmux attach -t car_client     # View output"
echo "  tmux kill-session -t car_client  # Stop everything"
echo ""
echo "Inside tmux:"
echo "  Ctrl+B then 0  # Switch to simulator window"
echo "  Ctrl+B then 1  # Switch to sync window"
echo "  Ctrl+B then D  # Detach (keep running in background)"
echo ""
