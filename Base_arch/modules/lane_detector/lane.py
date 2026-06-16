import cv2
import numpy as np
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
import math
# ==========================
# Image Preprocessing
# ==========================

pid_integral = 0
pid_prev_error = 0
def dynamic_binary(img_bgr, use_percentile=True, pct_low=0.5, pct_high=99.5):
    """
    Convert an image to grayscale and compute a dynamic binary threshold.
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    if use_percentile:
        low = np.percentile(gray, pct_low)
        high = np.percentile(gray, pct_high)
    else:
        low = gray.min()
        high = gray.max()
    threshold = (low + high) / 2
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    return gray, binary, threshold
def preprocess_image(
    frame,
    resize_dim=(320, 240),
    crop_y=170,
    crop_left=20,
    crop_right=20,
    a_shift=-10
):
    """
    Crop top, left, and right parts of the image
    and remove red using LAB color space.
    """
    if frame is None:
        raise ValueError("Frame is None")
    # Crop:
    # crop_y pixels from top
    # crop_left pixels from left
    # crop_right pixels from right
    frame_cropped = frame[crop_y:, crop_left:-crop_right]
    return frame_cropped
# ==========================
# Line Detection
# ==========================
def extract_longest_white_line(binary_img, min_size=20):
    """
    Finds the longest connected white line in a binary image.
    Returns endpoints, length, and all detected lines.
    """
    bin01 = (binary_img > 0).astype(np.uint8)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        bin01, connectivity=8)
    all_lines = []
    longest_line = None
    max_length = 0
    for label_id in range(1, num_labels):
        mask = (labels == label_id)
        coords = np.column_stack(np.where(mask))  # (y, x)
        if len(coords) < min_size:
            continue
        points = coords[:, ::-1]  # convert to (x, y)
        pca = PCA(n_components=1)
        pca.fit(points)
        direction = pca.components_[0]
        center = points.mean(axis=0)
        projections = (points - center) @ direction
        p1 = center + projections.min() * direction
        p2 = center + projections.max() * direction
        length = np.linalg.norm(p2 - p1)
        all_lines.append(
            ((int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), length))
        if length > max_length:
            max_length = length
            longest_line = ((int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])))
    return longest_line, max_length, all_lines

def extract_left_right_lines(binary_img, min_size=20):
    h, w = binary_img.shape[:2]
    mid = w // 2

    # Split image
    left_img = binary_img[:, :mid]
    right_img = binary_img[:, mid:]

    # Find longest line in each half
    left_line, left_len, _ = extract_longest_white_line(
        left_img,
        min_size=min_size
    )

    right_line, right_len, _ = extract_longest_white_line(
        right_img,
        min_size=min_size
    )

    # Convert right coordinates back to full image coordinates
    if right_line is not None:
        (x1, y1), (x2, y2) = right_line

        right_line = (
            (x1 + mid, y1),
            (x2 + mid, y2)
        )

    return left_line, left_len, right_line, right_len

def dilate_binary(binary_img, kernel_size=(1, 1), iterations=1, invert=True):
    """
    Dilate a binary image to close gaps.
    """
    if invert:
        binary_img = cv2.bitwise_not(binary_img)
    kernel = np.ones(kernel_size, np.uint8)
    dilated = cv2.dilate(binary_img, kernel, iterations=iterations)
    return dilated
def compute_line_angle(line):
    """
    Compute the angle (degrees) of a line given endpoints.
    """
    (x1, y1), (x2, y2) = line
    if y1 > y2:
        x1, y1, x2, y2 = x2, y2, x1, y1
    dx = x2 - x1
    dy = y2 - y1
    angle_rad = math.atan2(dy, dx)
    angle_deg = 180 - math.degrees(angle_rad)
    return angle_deg
# ==========================
# Visualization
# ==========================

def classify_turn_with_direction(left_angle, left_length, right_angle, right_length):
    """
    Advanced dual-lane steering logic.
    - Calculates ideal steering for Left and Right lanes independently.
    - If a lane is missing or too short, it defaults to a 'search' turn.
    - Final servo command is the average of both lane decisions + PID trim.
    """
    # ── System Constants ──────────────────────────────────────────────────────
    SERVO_CENTER = 104
    SERVO_MIN    = 70     # Max right
    SERVO_MAX    = 130    # Max left
    MIN_LENGTH   = 50     # Noise threshold

    TARGET_LEFT  = 35
    TARGET_RIGHT = 140

    LANE_LEFT_MIN,  LANE_LEFT_MAX  = 3,   40
    LANE_RIGHT_MIN, LANE_RIGHT_MAX = 140, 175

    global pid_integral, pid_prev_error
    Kp, Ki, Kd = 1.5, 0.0, 0.0

    # ── 1. LEFT LANE ──────────────────────────────────────────────────────────
    left_valid = (left_angle  is not None and
                  left_length is not None and
                  left_length >= MIN_LENGTH)

    if not left_valid:
        steer_left = SERVO_MAX       # steer left to find the lane
        dir_left   = "search_left"
        ang_left   = 0
    else:
        ang_left = max(LANE_LEFT_MIN, min(LANE_LEFT_MAX, left_angle % 360))

        if abs(ang_left - TARGET_LEFT) <= 3:
            steer_left = SERVO_CENTER
            dir_left   = "straight"
        else:
            # ang_left < TARGET_LEFT → too shallow → steer right (decrease servo)
            denom      = TARGET_LEFT - LANE_LEFT_MIN        # 35 - 3 = 32 (never 0)
            ratio      = (TARGET_LEFT - ang_left) / denom
            steer_left = int(SERVO_CENTER - ratio * (SERVO_CENTER - SERVO_MIN))
            dir_left   = "right"

    mission_left = f"t {steer_left}"

    # ── 2. RIGHT LANE ─────────────────────────────────────────────────────────
    right_valid = (right_angle  is not None and
                   right_length is not None and
                   right_length >= MIN_LENGTH)

    if not right_valid:
        steer_right = SERVO_MIN      # steer right to find the lane
        dir_right   = "search_right"
        ang_right   = 0
    else:
        ang_right = max(LANE_RIGHT_MIN, min(LANE_RIGHT_MAX, right_angle % 360))

        if abs(ang_right - TARGET_RIGHT) <= 3:
            steer_right = SERVO_CENTER
            dir_right   = "straight"
        else:
            # ang_right > TARGET_RIGHT → drifting right → steer left (increase servo)
            denom       = LANE_RIGHT_MAX - TARGET_RIGHT     # 175 - 140 = 35 (never 0)
            ratio       = (ang_right - TARGET_RIGHT) / denom
            steer_right = int(SERVO_CENTER + ratio * (SERVO_MAX - SERVO_CENTER))
            dir_right   = "left"

    mission_right = f"t {steer_right}"

    # ── 3. FINAL DECISION ─────────────────────────────────────────────────────
    if not left_valid and not right_valid:
        final_steer = SERVO_CENTER
        final_dir   = "lost_straight"
    else:
        final_steer = int((steer_left + steer_right) / 2)

        if   final_steer > SERVO_CENTER + 3: final_dir = "left"
        elif final_steer < SERVO_CENTER - 3: final_dir = "right"
        else:                                final_dir = "straight"

    # ── 4. PID TRIM ───────────────────────────────────────────────────────────
    errors = []
    if left_valid:  errors.append(TARGET_LEFT  - ang_left)
    if right_valid: errors.append(ang_right    - TARGET_RIGHT)

    if errors:
        error          = sum(errors) / len(errors)
        pid_integral   = max(-100, min(100, pid_integral + error))
        derivative     = error - pid_prev_error
        pid_output     = Kp * error + Ki * pid_integral + Kd * derivative
        pid_prev_error = error
    else:
        pid_output = pid_integral = pid_prev_error = 0

    if   final_dir == "right": final_steer -= abs(int(pid_output))
    elif final_dir == "left":  final_steer += abs(int(pid_output))
    else:                      final_steer += int(pid_output)

    final_steer   = max(SERVO_MIN, min(SERVO_MAX, final_steer))
    final_mission = f"t {final_steer}"

    return (
        mission_left,  dir_left,  ang_left,
        mission_right, dir_right, ang_right,
        final_mission, final_dir, final_steer,
    )
# ==========================
# Main Function Example
# ==========================
def process_lane(frame, return_debug=False):
    frame_cropped = preprocess_image(frame)
    gray, binary, threshold = dynamic_binary(frame_cropped)
    dilated = dilate_binary(binary)
    left_line, left_length, right_line, right_length = extract_left_right_lines(dilated)

    angle_left = None
    angle_right = None

    if left_length < 90:
        left_line = None
        angle_left = None
    else:
        angle_left = compute_line_angle(left_line)
    if right_length < 90:
        right_line = None
        angle_right = None
    else:
        angle_right = compute_line_angle(right_line)

    mission_from_left, direction_from_left, angle_left, mission_from_right, direction_from_right, angle_right, final_mission, final_dir, final_steer = classify_turn_with_direction(
        angle_left,
        left_length,
        angle_right,
        right_length,
    )
    if return_debug:
        # Create visualization with line drawn on dilated image
        vis = cv2.cvtColor(dilated, cv2.COLOR_GRAY2BGR)
        if left_line:
            cv2.line(vis,left_line[0],left_line[1],(0,255,0),2)
        if right_line:
            cv2.line(vis,right_line[0],right_line[1],(0,0,255),2)            
        debug_info = {
            'original': frame,
            'cropped': frame_cropped,
            'gray': gray,
            'binary': binary,
            'dilated': dilated,
            'visualization': vis,
            'left_line': left_line,
            'right_line': right_line,
            'right_angle': angle_right,
            'left_angle': angle_left
            ,'left_length':left_length
            ,'right_length':right_length
        }
        print(f"Left Line: {left_line}, Angle: {angle_left:.2f}°, Mission: {mission_from_left}, Direction: {direction_from_left}, Length: {left_length}")
        print(f"Right Line: {right_line}, Angle: {angle_right:.2f}°, Mission: {mission_from_right}, Direction: {direction_from_right}, Length: {right_length}")
        print(f"Final Mission: {final_mission}, Final Direction: {final_dir}, Final Steer: {final_steer}")
        return (
            mission_from_left,
            direction_from_left,
            angle_left,
            left_length,
            mission_from_right,
            direction_from_right,
            angle_right,
            right_length,
            final_mission,
            final_dir,
            final_steer,
            debug_info,
        )
    else:
        print("No valid lines detected.")
        if return_debug:
            vis = cv2.cvtColor(dilated, cv2.COLOR_GRAY2BGR)
            debug_info = {
                'original': frame,
                'cropped': frame_cropped,
                'gray': gray,
                'binary': binary,
                'dilated': dilated,
                'visualization': vis,
                'left_line': None,
                'right_line': None,
                'right_angle': 0,
                'left_angle': 0,
                'final_mission': final_mission,
                'final_direction': final_dir,
                'final_steer': final_steer,
            }
            return 's', "stop", 0, left_length, 's', "stop", 0, 0, final_mission, final_dir, final_steer, debug_info
        return 's', "stop", 0, left_length, 's', "stop", 0, 0, final_mission, final_dir, final_steer, None