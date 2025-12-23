#!/bin/bash
LOG_FILE=$(ls -t ~/catkin_ws/src/turtlebot3_exploration/logs/waypoint_log_*.txt 2>/dev/null | head -1)
if [ -f "$LOG_FILE" ]; then
    echo "=== Latest Log File: $LOG_FILE ==="
    cat "$LOG_FILE"
else
    echo "No log files found!"
fi
