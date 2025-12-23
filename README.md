# Navigation Logs Directory

This directory contains the waypoint navigation log files generated during autonomous exploration missions.

## Log File Format

Log files are named with timestamps: `waypoint_log_YYYYMMDD_HHMMSS.txt`

## Log File Contents

Each log file contains:

1. **Header Information**
   - Start time
   - Mission parameters

2. **Waypoint Data** (for each waypoint)
   - Timestamp (seconds since epoch)
   - Waypoint name (Corner or Obstacle zone)
   - Target X coordinate (meters)
   - Target Y coordinate (meters)
   - Status (Goal Sent, Reached, Pause Complete, Failed, Timeout)
   - Actual robot position from odometry (when available)

3. **Summary Statistics**
   - End time
   - Total waypoints
   - Successfully reached waypoints
   - Failed waypoints
   - Success rate percentage
   - Total mission duration

## Waypoint Sequence

The robot navigates through the following sequence:

1. **Corner 1** (0.5, 0.5) - 2 second pause
2. **Obstacle 1 Zone** - Navigate through obstacle area
3. **Corner 2** (0.5, 4.5) - 2 second pause
4. **Obstacle 2 Zone** - Navigate through obstacle area
5. **Corner 3** (4.5, 4.5) - 2 second pause
6. **Obstacle 3 Zone** - Navigate through obstacle area
7. **Corner 4** (4.5, 0.5) - 2 second pause
8. **Obstacle 4 Zone** - Navigate through obstacle area
9. **Return to Corner 1** (0.5, 0.5) - Complete the circuit

## Viewing Logs

To view the most recent log:
```bash
cat $(ls -t ~/catkin_ws/src/turtlebot3_exploration/logs/waypoint_log_*.txt | head -1)
```

To view all logs:
```bash
ls -lh ~/catkin_ws/src/turtlebot3_exploration/logs/
```

## Analysis

Logs can be used for:
- Verifying successful waypoint navigation
- Analyzing navigation timing
- Debugging failed navigation attempts
- Performance evaluation
- Report generation
