#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
def main(args=None):
    rclpy.init(args=args)
    node = Node("camera_driver_node")
    node.get_logger().info("hi the camera has started")
    rclpy.shutdown()
if __name__ == "__main__":
    main()