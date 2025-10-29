#!/usr/bin/env python
# coding: utf-8

# In[48]:


import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import cv2

# In[118]:


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
    # return {
    #     "left_black": left_black,
    #     "right_black": right_black,
    #     "left_occupancy_pct": left_occupancy_pct,
    #     "right_occupancy_pct": right_occupancy_pct,
    #     "left_share_pct": left_share_pct,
    #     "right_share_pct": right_share_pct,
    #     "diff_share_pct": diff_share_pct,
    #     "signed_normalized": signed_normalized,
    # }

# In[125]:
  
def process_lane(frame, roi_start=350, threshold=25, base_speed=180, max_turn_speed=250, min_turn_speed=40):  
    """  
    Process a frame for lane detection and return steering decision with wheel speeds.  
      
    Args:  
        frame: BGR frame from camera  
        roi_start: Row to start ROI (crops top portion), e.g., 300  
        threshold: Decision threshold for turning  
        base_speed: Base speed when going straight (both wheels)  
        max_turn_speed: Maximum speed for turning wheel  
        min_turn_speed: Minimum speed for turning wheel  
          
    Returns:  
        decision: 'straight', 'left', or 'right'  
        left_speed: PWM speed for left wheel (0-255)  
        right_speed: PWM speed for right wheel (0-255)  
        diff_share_pct: The balance metric value  
    """  
    # Apply binary threshold  
    frame = cv2.flip(frame, -1)
    frame = frame[roi_start:, :]
    cv2.imwrite("cropped_real.jpg", frame)
    binary = dynamic_binary(frame, use_percentile=True, pct_low=0.1)  
      
    # Crop to region of interest if specified  
    if roi_start:  
        cv2.imwrite("cropped_binary.jpg", (binary * 255).astype(np.uint8))
      
    # Get lane balance metric  
    diff_share_pct = lane_balance_metrics(binary)  
      
    # Calculate wheel speeds based on lane imbalance
    if abs(diff_share_pct) <= threshold:  
        decision = 'straight'
        # Both wheels same speed when going straight
        left_speed = base_speed
        right_speed = base_speed
    elif diff_share_pct > threshold:  
        # Left side has more black lane, turn RIGHT
        decision = 'right'
        # Calculate turn intensity (0.0 to 1.0) based on how much black is on left
        turn_intensity = min(abs(diff_share_pct) / 100.0, 1.0)
        
        # For right turn: left wheel faster, right wheel slower
        # More black on left = sharper turn = bigger speed difference
        speed_difference = int(turn_intensity * (max_turn_speed - min_turn_speed))
        
        left_speed = min(base_speed + speed_difference, max_turn_speed)
        right_speed = max(base_speed - speed_difference, min_turn_speed)
    else:  
        # Right side has more black lane, turn LEFT
        decision = 'left'
        # Calculate turn intensity (0.0 to 1.0) based on how much black is on right
        turn_intensity = min(abs(diff_share_pct) / 100.0, 1.0)
        
        # For left turn: right wheel faster, left wheel slower
        # More black on right = sharper turn = bigger speed difference
        speed_difference = int(turn_intensity * (max_turn_speed - min_turn_speed))
        
        right_speed = min(base_speed + speed_difference, max_turn_speed)
        left_speed = max(base_speed - speed_difference, min_turn_speed)
    
    # Ensure speeds are within valid range
    left_speed = max(0, min(255, left_speed))
    right_speed = max(0, min(255, right_speed))
      
    print(f"[LANE] Decision: {decision}, L: {left_speed}, R: {right_speed}, Imbalance: {diff_share_pct:.1f}%")
    return decision, right_speed ,left_speed