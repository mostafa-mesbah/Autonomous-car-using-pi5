import cv2
import numpy as np
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
import math

# ==========================
# Image Preprocessing
# ==========================
def remove_red_lab(img, a_shift=-10):
    """
    Reduce red tones in an RGB image by adjusting LAB a-channel.
    """
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB).astype(np.int16)
    lab[..., 1] = np.clip(lab[..., 1] + a_shift, 0, 255)
    lab = lab.astype(np.uint8)
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

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

def preprocess_image(frame, resize_dim=(640, 480), crop_y=380, a_shift=-10):
    """
    Read, resize, crop, and optionally remove red from the image.
    """
    frame_resized = cv2.resize(frame,resize_dim)

    if frame is None:
        raise FileNotFoundError(f"Image not found: {image_path}")
    frame = cv2.resize(frame, resize_dim)
    frame_cropped = frame[crop_y:, :]
    cv2.imwrite("croped_frame.jpg",frame_cropped)
    frame_cropped = remove_red_lab(frame_cropped, a_shift)
    return frame_resized, frame_cropped

# ==========================
# Line Detection
# ==========================
def extract_longest_white_line(binary_img, min_size=30):
    """
    Finds the longest connected white line in a binary image.
    Returns endpoints, length, and all detected lines.
    """
    bin01 = (binary_img > 0).astype(np.uint8)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bin01, connectivity=8)
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
        all_lines.append(((int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), length))
        if length > max_length:
            max_length = length
            longest_line = ((int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])))
    return longest_line, max_length, all_lines

def dilate_binary(binary_img, kernel_size=(10, 10), iterations=3, invert=True):
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
def visualize_results(frame, gray, binary, binary_closed, longest_line):
    """
    Plot original, grayscale, binary, dilated, and longest line results.
    """
    vis = cv2.cvtColor(binary_closed, cv2.COLOR_GRAY2BGR)
    if longest_line:
        p1, p2 = longest_line
        cv2.line(vis, p1, p2, (0, 0, 255), 2)

    plt.figure(figsize=(16, 4))
    titles = ["Original", "Grayscale", "Binary", "Binary Closed", "Longest Line"]
    images = [cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), gray, binary, binary_closed, vis]
    cmaps = [None, 'gray', 'gray', 'gray', None]

    for i, (img, title, cmap) in enumerate(zip(images, titles, cmaps), 1):
        plt.subplot(1, 5, i)
        plt.title(title)
        plt.imshow(img, cmap=cmap)
        plt.axis('off')
    plt.show()


def classify_turn_with_direction(angle):
    """
    Classify the turn based on angle.
    Input:
        angle : float (0-360°)
    Output:
        direction : 'left' or 'right'
        level : 'sharp turn', 'low sharp turn', 'normal turn', 'no turn'
    """
    # Normalize angle to 0-360
    angle = angle % 360
    mission="f 100"
    angle_sym = angle
    if angle > 180:
        angle_sym = 360 - angle
    
    if 160 >=angle >= 25:
        direction = "straign"
        mission="f 0"
        mission="f 150"
    elif 170>=angle >160:
        mission="f 0"
        mission="t 50 150"
        direction = "left"
    elif 180>=angle >170:
        mission="f 0"
        mission="t 70 200"
        direction = "sharp left"
    elif 25>angle >=15:
        mission="f 0"
        mission="t 150 50"
        direction = "right"
    elif 15>angle >=0:
        mission="f 0"
        mission="t 210 70"
        direction = "sharp right"
    return mission,direction,angle

# ==========================
# Main Function Example
# ==========================
def visualize_results_cli(fliped_frame,frame_cropped,gray, binary,dilated,longest_line, save_debug=True):
    """
    CLI-friendly version: prints image stats, line info, and optionally saves images.
    """

    
    if longest_line:
        p1, p2 = longest_line
        length = np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
        
        # Overlay line for optional debug
        vis = cv2.cvtColor(dilated, cv2.COLOR_GRAY2BGR)
        cv2.line(vis, p1, p2, (0, 0, 255), 2)
    else:
        print("No line detected.")
        vis = cv2.cvtColor(dilated, cv2.COLOR_GRAY2BGR)

    # Optionally save images for offline viewing
    if save_debug:
        cv2.imwrite("frame.jpg", fliped_frame)
        cv2.imwrite("cropped.jpg", frame_cropped)
        cv2.imwrite("gray.jpg", gray)
        cv2.imwrite("binary.jpg", binary)
        cv2.imwrite("binary_closed.jpg", dilated)
        cv2.imwrite("vis.jpg", vis)
        

    return vis 
def process_lane(frame):
    fliped_frame = cv2.flip(frame, -1)
    #cv2.imwrite("first_frame.jpg",fliped_frame)
    frame_resized, frame_cropped = preprocess_image(fliped_frame)
    gray, binary, threshold = dynamic_binary(frame_cropped)
    dilated = dilate_binary(binary)
    longest_line, length, all_lines = extract_longest_white_line(dilated)
    #cv2.imwrite("last_frame.jpg",dilated)
    #visualize_results_cli(fliped_frame,frame_cropped,gray, binary,dilated,longest_line)
    if longest_line:
        angle = compute_line_angle(longest_line)
        #print(f"Angle of the line: {angle:.2f}°")
        return classify_turn_with_direction(angle)
    else:
        print("No valid lines detected.")
        return 's',"stop"

