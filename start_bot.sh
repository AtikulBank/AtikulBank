#!/bin/bash
# XAUUSD God Bot - One-Command Runner
# Usage: ./start_bot.sh

echo "=========================================="
echo "  XAUUSD GOD BOT - Starting..."
echo "=========================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found"
    exit 1
fi

# Run the bot
python3 run_all.py

echo "=========================================="
echo "  Bot execution finished"
echo "=========================================="