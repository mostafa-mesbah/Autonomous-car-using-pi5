# import numpy as np
# import numpy as np
# import matplotlib.pyplot as plt
# import seaborn as sns
# import cv2
# class LaneTracker:
#     def __init__(self):
#         self.left_lane_history = []  # Store recent left lane positions
#         self.right_lane_history = []  # Store recent right lane positions
#         self.max_history = 10  # Keep last 10 frames
#         self.lane_width = None  # Estimated lane width
#         self.last_known_lanes = None  # Last detected lane positions
        
#     def detect_lane_slopes(self, binary):
#         """Detect left and right lane slopes using Hough Lines"""
#         h, w = binary.shape
        
#         # Convert binary to uint8 for HoughLines
#         binary_uint8 = (binary * 255).astype(np.uint8)
        
#         # Detect lines using Hough Transform
#         lines = cv2.HoughLinesP(binary_uint8, 1, np.pi/180, threshold=50, 
#                                minLineLength=30, maxLineGap=20)
        
#         left_lines = []
#         right_lines = []
        
#         if lines is not None:
#             for line in lines:
#                 x1, y1, x2, y2 = line[0]
                
#                 # Calculate slope and intercept
#                 if x2 - x1 != 0:  # Avoid division by zero
#                     slope = (y2 - y1) / (x2 - x1)
#                     intercept = y1 - slope * x1
                    
#                     # Filter by slope (vertical lines for lanes)
#                     if abs(slope) > 0.3:  # Reasonable lane slope threshold
#                         if slope < 0:  # Left lane (sloping right-down to left-up)
#                             left_lines.append((slope, intercept, x1, y1, x2, y2))
#                         else:  # Right lane (sloping left-down to right-up)
#                             right_lines.append((slope, intercept, x1, y1, x2, y2))
        
#         return left_lines, right_lines
    
#     def calculate_lane_positions(self, left_lines, right_lines, binary_shape):
#         """Calculate lane positions from detected lines"""
#         h, w = binary_shape
        
#         # Average the lines for each lane
#         left_x = None
#         right_x = None
        
#         if left_lines:
#             avg_slope = np.mean([line[0] for line in left_lines])
#             avg_intercept = np.mean([line[1] for line in left_lines])
#             # Calculate x position at bottom of image
#             left_x = int((h - avg_intercept) / avg_slope) if avg_slope != 0 else w//4
        
#         if right_lines:
#             avg_slope = np.mean([line[0] for line in right_lines])
#             avg_intercept = np.mean([line[1] for line in right_lines])
#             # Calculate x position at bottom of image
#             right_x = int((h - avg_intercept) / avg_slope) if avg_slope != 0 else 3*w//4
        
#         return left_x, right_x
    
#     def update_lane_history(self, left_x, right_x):
#         """Update lane history with new detections"""
#         if left_x is not None:
#             self.left_lane_history.append(left_x)
#             if len(self.left_lane_history) > self.max_history:
#                 self.left_lane_history.pop(0)
        
#         if right_x is not None:
#             self.right_lane_history.append(right_x)
#             if len(self.right_lane_history) > self.max_history:
#                 self.right_lane_history.pop(0)
        
#         # Update lane width estimate
#         if left_x is not None and right_x is not None:
#             self.lane_width = right_x - left_x
#             self.last_known_lanes = (left_x, right_x)
    
#     def predict_missing_lane(self, detected_lane_x, is_left=True):
#         """Predict position of missing lane based on history and lane width"""
#         if self.lane_width is None or self.last_known_lanes is None:
#             return None
        
#         if is_left:
#             # Predict left lane position based on right lane
#             predicted_left = detected_lane_x - self.lane_width
#             # Use history to smooth prediction
#             if self.left_lane_history:
#                 historical_avg = np.mean(self.left_lane_history)
#                 predicted_left = 0.7 * predicted_left + 0.3 * historical_avg
#             return max(0, int(predicted_left))
#         else:
#             # Predict right lane position based on left lane
#             predicted_right = detected_lane_x + self.lane_width
#             # Use history to smooth prediction
#             if self.right_lane_history:
#                 historical_avg = np.mean(self.right_lane_history)
#                 predicted_right = 0.7 * predicted_right + 0.3 * historical_avg
#             return min(255, int(predicted_right))

# # Initialize lane tracker
# lane_tracker = LaneTracker()

# def process_lane(frame, roi_start=350, threshold=25, base_speed=180, max_turn_speed=250, min_turn_speed=40):  
#     frame = cv2.flip(frame, -1)
#     frame = frame[roi_start:, :]
#     binary = dynamic_binary(frame, use_percentile=True, pct_low=0.1)  
    
#     # Detect lane slopes
#     left_lines, right_lines = lane_tracker.detect_lane_slopes(binary)
#     left_x, right_x = lane_tracker.calculate_lane_positions(left_lines, right_lines, binary.shape)
    
#     # Handle missing lanes
#     lanes_detected = 0
#     if left_x is not None:
#         lanes_detected += 1
#     if right_x is not None:
#         lanes_detected += 1
    
#     # If only one lane detected, predict the other
#     if lanes_detected == 1:
#         if left_x is None and right_x is not None:
#             left_x = lane_tracker.predict_missing_lane(right_x, is_left=True)
#         elif right_x is None and left_x is not None:
#             right_x = lane_tracker.predict_missing_lane(left_x, is_left=False)
    
#     # Update lane history
#     lane_tracker.update_lane_history(left_x, right_x)
    
#     # Calculate center and imbalance
#     if left_x is not None and right_x is not None:
#         lane_center = (left_x + right_x) // 2
#         car_position = binary.shape[1] // 2
#         offset = car_position - lane_center
        
#         # Normalize offset to percentage
#         max_offset = binary.shape[1] // 2
#         diff_share_pct = (offset / max_offset) * 100
#     else:
#         # Emergency handling - no lanes detected
#         diff_share_pct = 100  # Max turn in last known direction
    
#     # Enhanced decision logic for sharp turns
#     if abs(diff_share_pct) <= threshold:  
#         decision = 'straight'
#         left_speed = base_speed
#         right_speed = base_speed
#     else:
#         # Check for sharp turns (lane disappearance)
#         if lanes_detected < 2 and abs(diff_share_pct) > 50:
#             # Sharp turn detected - use maximum turn speed
#             if diff_share_pct > 0:  # Turn right sharply
#                 decision = 'right'
#                 left_speed = max_turn_speed
#                 right_speed = min_turn_speed
#             else:  # Turn left sharply
#                 decision = 'left'
#                 left_speed = min_turn_speed
#                 right_speed = max_turn_speed
#         else:
#             # Normal proportional turning
#             turn_intensity = min(abs(diff_share_pct) / 100.0, 1.0)
#             speed_difference = int(turn_intensity * (max_turn_speed - min_turn_speed))
            
#             if diff_share_pct > 0:  # Turn right
#                 decision = 'right'
#                 left_speed = min(base_speed + speed_difference, max_turn_speed)
#                 right_speed = max(base_speed - speed_difference, min_turn_speed)
#             else:  # Turn left
#                 decision = 'left'
#                 right_speed = min(base_speed + speed_difference, max_turn_speed)
#                 left_speed = max(base_speed - speed_difference, min_turn_speed)
    
#     # Ensure speeds are valid
#     left_speed = max(0, min(255, left_speed))
#     right_speed = max(0, min(255, right_speed))
    
#     # Draw lane visualization (optional)
#     draw_lane_debug(frame, binary, left_lines, right_lines, left_x, right_x, decision)
    
#     print(f"[LANE] Lanes: {lanes_detected}/2, Decision: {decision}, L: {left_speed}, R: {right_speed}, Offset: {diff_share_pct:.1f}%")
#     return decision, right_speed,left_speed

# def draw_lane_debug(frame, binary, left_lines, right_lines, left_x, right_x, decision):
#     """Draw lane detection debug information"""
#     debug_img = cv2.cvtColor((binary * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    
#     # Draw detected lines
#     for line in left_lines:
#         _, _, x1, y1, x2, y2 = line
#         cv2.line(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green for left lane
    
#     for line in right_lines:
#         _, _, x1, y1, x2, y2 = line
#         cv2.line(debug_img, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Red for right lane
    
#     # Draw lane positions
#     if left_x is not None:
#         cv2.line(debug_img, (left_x, 0), (left_x, debug_img.shape[0]), (255, 255, 0), 2)
#     if right_x is not None:
#         cv2.line(debug_img, (right_x, 0), (right_x, debug_img.shape[0]), (255, 255, 0), 2)
    
#     cv2.putText(debug_img, f"Decision: {decision}", (10, 30), 
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
#     cv2.imwrite("lane_debug.jpg", debug_img)

# def dynamic_binary(img_bgr, use_percentile=False, pct_low=0.5, pct_high=99.5, morph_kernel=5, open_iter=1, dilate_iter=2):
#     """
#     img_bgr: BGR image as read by cv2.imread
#     If use_percentile==False: threshold = (min_gray + max_gray) / 2
#     If use_percentile==True: threshold = (p_low + p_high) / 2 where p_low/p_high are percentiles.
#     Returns a uint8 binary image (0 or 255).
#     """
#     # to grayscale
#     gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

#     if use_percentile:
#         low = np.percentile(gray, pct_low)
#         high = np.percentile(gray, pct_high)
#     else:
#         low = int(gray.min())
#         high = int(gray.max())

#     thresh = (int(low) + int(high)) // 2

#     _, binary = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)

#     # morphological cleanup: open then dilate
#     kernel = np.ones((morph_kernel, morph_kernel), np.uint8)
#     if open_iter > 0:
#         binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=open_iter)
#     if dilate_iter > 0:
#         binary = cv2.dilate(binary, kernel, iterations=dilate_iter)

#     binary = np.round(binary / 255)

#     return binary  # , thresh, int(low), int(high)



import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import cv2
import seaborn as sns
from scipy import ndimage
from sklearn.decomposition import PCA
import math


def remove_red_lab(img, a_shift=-10):
    # img in RGB uint8
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB).astype(np.int16)
    lab[..., 1] = np.clip(lab[..., 1] + a_shift, 0, 255)  # negative moves toward green
    lab = lab.astype(np.uint8)
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)


def dynamic_binary(img_bgr, use_percentile=False, pct_low=0.5, pct_high=99.5, morph_kernel=5, open_iter=1, dilate_iter=2):
    """
    img_bgr: BGR image as read by cv2.imread
    If use_percentile==False: threshold = (min_gray + max_gray) / 2
    If use_percentile==True: threshold = (p_low + p_high) / 2 where p_low/p_high are percentiles.
    Returns a uint8 binary image (0 or 255).
    """
    # to grayscale
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.erode(gray, np.ones((3, 3), np.uint8), iterations=7)

    if use_percentile:
        low = np.percentile(gray, pct_low)
        high = np.percentile(gray, pct_high)
    else:
        low = int(gray.min())
        high = int(gray.max())

    thresh = (int(low) + int(high)) // 2

    _, binary = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)

    # morphological cleanup: open then dilate
    kernel = np.ones((morph_kernel, morph_kernel), np.uint8)
    if open_iter > 0:
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=open_iter)
    if dilate_iter > 0:
        binary = cv2.dilate(binary, kernel, iterations=dilate_iter)

    binary = np.round(binary / 255)

    return binary  # , thresh, int(low), int(high)


def lane_balance_metrics(bin01):
    """
    bin01: binary image with values 0/1 (not 0/255).
    Returns a dict with:
      - left_black, right_black (counts)
      - left_occupancy_pct, right_occupancy_pct (black / half_area * 100) or None if area unknown
      - left_share_pct, right_share_pct (share of total black)
      - diff_share_pct (left_share - right_share, percentage points)
      - signed_normalized ( (L-R) / (L+R) in [-1,1] )
    """
    h, w = bin01.shape[:2]
    mid = w // 2

    left = bin01[:, :mid]
    right = bin01[:, mid:]

    left_black = int((left == 0).sum())  # if black is 0; change to (left==1) if black==1
    right_black = int((right == 0).sum())

    total_black = left_black + right_black

    half_area = left.size  # = right.size (if w even)
    left_occupancy_pct = (left_black / half_area * 100) if half_area > 0 else None
    right_occupancy_pct = (right_black / half_area * 100) if half_area > 0 else None

    if total_black == 0:
        left_share_pct = right_share_pct = diff_share_pct = 0.0
        signed_normalized = 0.0
    else:
        left_share_pct = left_black / total_black * 100.0
        right_share_pct = right_black / total_black * 100.0
        diff_share_pct = left_share_pct - right_share_pct
        signed_normalized = (left_black - right_black) / total_black

    return diff_share_pct

def extract_lines(binary_image, min_blob_size=10, bridge_threshold=5):
    """
    Extract lines from a binary image containing black blobs (0s) on white background (1s).
    
    Parameters:
    -----------
    binary_image : numpy.ndarray
        Binary image with 0s (black blobs) and 1s (white background)
    min_blob_size : int
        Minimum number of pixels for a blob to be considered
    bridge_threshold : int
        Maximum distance in pixels for blobs to be considered connected.
        Larger values will merge nearby blobs into one line.
    
    Returns:
    --------
    lines : list of [[x1, y1], [x2, y2]]
        List of line segments, each defined by start and end points
    """
    # Invert image so blobs are 1s for labeling
    inverted = 1 - binary_image
    
    # Create structuring element for morphological operations
    # Use bridge_threshold to determine connectivity
    if bridge_threshold > 1:
        # Dilate slightly to connect nearby blobs
        struct = ndimage.generate_binary_structure(2, 2)
        struct = ndimage.iterate_structure(struct, bridge_threshold // 2)
        dilated = ndimage.binary_dilation(inverted, structure=struct)
    else:
        dilated = inverted
    
    # Label connected components
    labeled, num_features = ndimage.label(dilated)
    
    lines = []
    
    # Process each blob
    for label_id in range(1, num_features + 1):
        # Get coordinates of pixels in this blob
        coords = np.argwhere(labeled == label_id)
        
        if len(coords) < min_blob_size:
            continue
        
        # coords are in (row, col) format, convert to (x, y)
        points = coords[:, ::-1]  # Now (col, row) = (x, y)
        
        # Use PCA to find principal axis
        if len(points) > 1:
            pca = PCA(n_components=1)
            pca.fit(points)
            
            # Get the principal direction
            direction = pca.components_[0]
            center = points.mean(axis=0)
            
            # Project all points onto the principal axis
            projections = (points - center) @ direction
            
            # Find the two extreme points
            min_idx = projections.argmin()
            max_idx = projections.argmax()
            
            p1 = points[min_idx].tolist()
            p2 = points[max_idx].tolist()
            
            lines.append([p1, p2])
        else:
            # Single pixel, use it as both endpoints
            p = points[0].tolist()
            lines.append([p, p])
    
    return lines
    
def get_largest_line(lines):
    """
    Line Expected Shape: [[x1, y1], [x2, y2]]"""
    max_mag = -1
    max_line = None

    for line in lines:
        line_mag = np.linalg.norm([np.array(line[0]) - np.array(line[1])])
        if line_mag > max_mag:
            max_mag = line_mag
            max_line = line
    
    return max_line
    
def extract_relative_theta_from_bin(bin_img):
    lines = extract_lines(bin_img)
    if len(lines) == 0:
        return 0

    main_line = get_largest_line(lines)
    if main_line is None:
        return 0

    [x1, y1], [x2, y2] = main_line

    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        raise ValueError("Points A and B are identical (no line).")

    # angle between the direction vector and the vertical (0..180)
    # using atan2(dx, dy) gives the angle measured from the positive Y axis.
    angle_from_vertical = abs(math.degrees(math.atan2(dx, dy)))
    # For an unoriented infinite line we want the acute angle to vertical (0..90)
    angle_to_vertical = min(angle_from_vertical, 180.0 - angle_from_vertical)


    print(f"Angle To Vertical: {angle_to_vertical}")
    # Determine upward direction: pick the lower point (smaller y) as "start"
    if y1 == y2:
        # horizontal line: no upward direction
        print(f"Angle to vertical: {angle_to_vertical:.3f}°  (horizontal line)")
        print("No upward direction (horizontal).")
        return

    # identify lower and upper points
    if y1 < y2:
        lower_x, upper_x = x1, x2
    else:
        lower_x, upper_x = x2, x1

    dx_upward = upper_x - lower_x

    if dx_upward > 0:
        return angle_to_vertical, "left"
    elif dx_upward < 0:
        return angle_to_vertical, "right"
    # shouldn't run
    else:
        # dx_upward == 0 => perfectly vertical
        return angle_to_vertical, "straight"

def process_lane(frame):
    frame = cv2.flip(frame, -1)
    frame = frame[350:, :]
    cv2.imwrite("source_frame.jpg",frame)
    bin_img = dynamic_binary(frame, pct_low=0.1)
    cv2.imwrite("bin_frame.jpg",bin_img * 255)

    relative_theta, action = extract_relative_theta_from_bin(bin_img)
    diff = lane_balance_metrics(bin_img)

    if abs(relative_theta) <= 73:
        # Non sharp edge behavior
        if abs(diff) <= 25:
            print("straight")
            return "straight",180,180
        elif diff > 25:
            # left larger
            print("right")
            return "right",180,50
        elif diff <= -25:
            # right larger
            print("left")
            return "left",50,180
    else:
        print("SHARP TURN DETECTED")
        if action == 'left':
            print("left")
            return "left",80,250
        elif action == 'right':
            print("right")
            return "right",250,80
        else:
            print("straight")
            return "straight",180,180