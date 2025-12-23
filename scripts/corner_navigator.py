#!/usr/bin/env python3

import rospy
import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import String
import time
import math
import os
from datetime import datetime

class CornerNavigator:
    def __init__(self):
        rospy.init_node('corner_navigator', anonymous=False)
        
        # Action client for move_base
        self.client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
        rospy.loginfo("Waiting for move_base action server...")
        self.client.wait_for_server()
        rospy.loginfo("Connected to move_base server")
        
        # Define corner coordinates with intermediate obstacle waypoints
        # Format: (x, y, waypoint_name, pause_duration)
        self.waypoints = [
            # Start at Corner 1
            (0.5, 0.5, "Corner 1", 2.0),
            
            # Navigate through obstacle 1 to Corner 2
            (0.8, 1.5, "Waypoint - Obstacle 1 Zone", 0.5),
            (0.5, 4.5, "Corner 2", 2.0),
            
            # Navigate through obstacle 2 to Corner 3
            (1.8, 4.2, "Waypoint - Obstacle 2 Zone", 0.5),
            (4.5, 4.5, "Corner 3", 2.0),
            
            # Navigate through obstacle 3 to Corner 4
            (4.2, 3.5, "Waypoint - Obstacle 3 Zone", 0.5),
            (4.5, 0.5, "Corner 4", 2.0),
            
            # Navigate through obstacle 4 back toward Corner 1
            (3.5, 0.8, "Waypoint - Obstacle 4 Zone", 0.5),
            (0.5, 0.5, "Corner 1 (Return)", 2.0),
        ]
        
        # Subscribe to odometry for logging
        self.odom_sub = rospy.Subscriber('/odom', Odometry, self.odom_callback)
        self.current_odom = None
        
        # Get package path for log file
        try:
            import rospkg
            rospack = rospkg.RosPack()
            package_path = rospack.get_path('turtlebot3_exploration')
            log_dir = os.path.join(package_path, 'logs')
        except:
            # Fallback to home directory
            log_dir = os.path.expanduser('~/catkin_ws/src/turtlebot3_exploration/logs')
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = os.path.join(log_dir, 'waypoint_log_{}.txt'.format(timestamp))
        
        self.log_file = open(log_filename, 'w')
        rospy.loginfo("Log file created: {}".format(log_filename))
        
        # Write header
        self.log_file.write("=" * 80 + "\n")
        self.log_file.write("TurtleBot3 Autonomous Exploration - Waypoint Navigation Log\n")
        self.log_file.write("=" * 80 + "\n")
        self.log_file.write("Start Time: {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.log_file.write("=" * 80 + "\n\n")
        self.log_file.write("{:<12} | {:<30} | {:<8} | {:<8} | {:<15}\n".format(
            "Timestamp", "Waypoint Name", "X (m)", "Y (m)", "Status"
        ))
        self.log_file.write("-" * 80 + "\n")
        
        # Statistics
        self.waypoints_reached = 0
        self.waypoints_failed = 0
        self.start_time = None
        
        rospy.on_shutdown(self.shutdown_hook)
        
    def odom_callback(self, msg):
        """Store current odometry data"""
        self.current_odom = msg
        
    def create_goal(self, x, y, orientation_yaw=0.0):
        """Create a MoveBaseGoal with the given coordinates"""
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = "map"
        goal.target_pose.header.stamp = rospy.Time.now()
        
        # Set position
        goal.target_pose.pose.position.x = x
        goal.target_pose.pose.position.y = y
        goal.target_pose.pose.position.z = 0.0
        
        # Convert yaw to quaternion
        goal.target_pose.pose.orientation.x = 0.0
        goal.target_pose.pose.orientation.y = 0.0
        goal.target_pose.pose.orientation.z = math.sin(orientation_yaw / 2.0)
        goal.target_pose.pose.orientation.w = math.cos(orientation_yaw / 2.0)
        
        return goal
    
    def log_waypoint(self, waypoint_name, x, y, status):
        """Log waypoint information to file"""
        timestamp = rospy.Time.now().to_sec()
        
        # Also log odometry if available
        odom_info = ""
        if self.current_odom is not None:
            actual_x = self.current_odom.pose.pose.position.x
            actual_y = self.current_odom.pose.pose.position.y
            odom_info = " | Actual: ({:.2f}, {:.2f})".format(actual_x, actual_y)
        
        log_entry = "{:<12.2f} | {:<30} | {:<8.2f} | {:<8.2f} | {:<15}{}\n".format(
            timestamp, waypoint_name[:30], x, y, status, odom_info
        )
        
        self.log_file.write(log_entry)
        self.log_file.flush()
        rospy.loginfo(log_entry.strip())
        
    def navigate_to_waypoints(self):
        """Navigate to all waypoints sequentially"""
        rospy.loginfo("\n" + "="*80)
        rospy.loginfo("Starting autonomous navigation sequence...")
        rospy.loginfo("Total waypoints: {}".format(len(self.waypoints)))
        rospy.loginfo("="*80 + "\n")
        
        self.start_time = rospy.Time.now()
        
        for i, (x, y, waypoint_name, pause_duration) in enumerate(self.waypoints):
            rospy.loginfo("\n" + "-"*80)
            rospy.loginfo("[{}/{}] Navigating to: {} at ({:.2f}, {:.2f})".format(
                i+1, len(self.waypoints), waypoint_name, x, y
            ))
            rospy.loginfo("-"*80)
            
            # Create and send goal
            goal = self.create_goal(x, y)
            self.log_waypoint(waypoint_name, x, y, "Goal Sent")
            
            self.client.send_goal(goal)
            
            # Wait for result with timeout
            success = self.client.wait_for_result(rospy.Duration(60.0))
            
            if not success:
                rospy.logwarn("Timeout waiting for result at {}".format(waypoint_name))
                self.log_waypoint(waypoint_name, x, y, "Timeout")
                self.waypoints_failed += 1
                continue
            
            # Check result
            state = self.client.get_state()
            if state == actionlib.GoalStatus.SUCCEEDED:
                rospy.loginfo("SUCCESS: Reached {}!".format(waypoint_name))
                self.log_waypoint(waypoint_name, x, y, "Reached")
                self.waypoints_reached += 1
                
                # Pause at waypoint
                if pause_duration > 0:
                    rospy.loginfo("Pausing for {:.1f} seconds at {}".format(
                        pause_duration, waypoint_name
                    ))
                    rospy.sleep(pause_duration)
                    self.log_waypoint(waypoint_name, x, y, "Pause Complete")
                
            else:
                rospy.logwarn("FAILED to reach {}. State: {}".format(waypoint_name, state))
                self.log_waypoint(waypoint_name, x, y, "Failed")
                self.waypoints_failed += 1
                
        # Final summary
        total_time = (rospy.Time.now() - self.start_time).to_sec()
        
        rospy.loginfo("\n" + "="*80)
        rospy.loginfo("NAVIGATION SEQUENCE COMPLETE")
        rospy.loginfo("="*80)
        rospy.loginfo("Total waypoints: {}".format(len(self.waypoints)))
        rospy.loginfo("Successfully reached: {}".format(self.waypoints_reached))
        rospy.loginfo("Failed: {}".format(self.waypoints_failed))
        rospy.loginfo("Total time: {:.2f} seconds".format(total_time))
        rospy.loginfo("="*80 + "\n")
        
        # Write summary to log file
        self.log_file.write("\n" + "=" * 80 + "\n")
        self.log_file.write("NAVIGATION SUMMARY\n")
        self.log_file.write("=" * 80 + "\n")
        self.log_file.write("End Time: {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.log_file.write("Total Waypoints: {}\n".format(len(self.waypoints)))
        self.log_file.write("Successfully Reached: {}\n".format(self.waypoints_reached))
        self.log_file.write("Failed: {}\n".format(self.waypoints_failed))
        self.log_file.write("Success Rate: {:.1f}%\n".format(
            100.0 * self.waypoints_reached / len(self.waypoints) if len(self.waypoints) > 0 else 0
        ))
        self.log_file.write("Total Duration: {:.2f} seconds\n".format(total_time))
        self.log_file.write("=" * 80 + "\n")
        
    def shutdown_hook(self):
        """Clean shutdown"""
        rospy.loginfo("Shutting down corner navigator...")
        self.client.cancel_all_goals()
        
        if self.log_file and not self.log_file.closed:
            self.log_file.write("\nShutdown initiated at: {}\n".format(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            self.log_file.close()
            rospy.loginfo("Log file saved successfully")

def main():
    try:
        navigator = CornerNavigator()
        # Give SLAM and navigation stack time to initialize
        rospy.loginfo("Waiting 5 seconds for SLAM and navigation to initialize...")
        rospy.sleep(5.0)
        navigator.navigate_to_waypoints()
        
        # Keep node alive to allow for graceful shutdown
        rospy.loginfo("Navigation complete. Press Ctrl+C to exit.")
        rospy.spin()
        
    except rospy.ROSInterruptException:
        rospy.loginfo("Navigation interrupted by user")
    except Exception as e:
        rospy.logerr("Error during navigation: {}".format(str(e)))
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
