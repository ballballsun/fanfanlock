from PIL import Image
import numpy as np

# Load image and convert to numpy array
image = Image.open('image.png')
image_np = np.array(image)

# If image has alpha channel, remove it
if image_np.shape[2] == 4:
    image_np = image_np[:,:,:3]

def find_rects_by_color(img, target_color, tolerance=30):
    """Find bounding boxes of rectangular regions close to the target_color."""
    from scipy.ndimage import label, find_objects
    
    mask = ((img >= np.array(target_color) - tolerance) & 
            (img <= np.array(target_color) + tolerance)).all(axis=-1)
    # Label connected components
    labeled, num_features = label(mask)
    slices = find_objects(labeled)
    rects = []
    for slc in slices:
        y1, y2 = slc[0].start, slc[0].stop
        x1, x2 = slc[1].start, slc[1].stop
        rects.append((x1, y1, x2 - x1, y2 - y1))
    return rects

# Finding rectangular regions by color analysis
rect_colors = [
    [195, 165, 115], # yellowish background
    [170, 130, 125], # pinkish background
    [105, 155, 145], # greenish background
    [195, 90, 80],   # red background
    [65, 45, 35],    # dark background
    [40, 60, 135]    # blue background
]

all_rects = []
for color in rect_colors:
    rects = find_rects_by_color(image_np, color, tolerance=20)
    all_rects.extend(rects)

# Count sizes for all rectangles
sizes = [(w, h) for _, _, w, h in all_rects]

# Count occurrences
from collections import Counter
size_counts = Counter(sizes)

# Tolerance for similar sizes
tolerance = 3

def are_similar(size1, size2, tol):
    return abs(size1[0] - size2[0]) <= tol and abs(size1[1] - size2[1]) <= tol

# Group similar sizes
group_counts = {}
unique_sizes = list(size_counts.keys())
for base_size in unique_sizes:
    group_count = sum(count for size, count in size_counts.items() 
                     if are_similar(size, base_size, tolerance))
    group_counts[base_size] = group_count

max_group_count = max(group_counts.values())
most_common_groups = [size for size, count in group_counts.items() 
                     if count == max_group_count]

# Count rectangles in the most common size group
count_rects = 0
for size in sizes:
    if any(are_similar(size, group, tolerance) for group in most_common_groups):
        count_rects += 1

print(f"Number of rectangles with highest occurrence size: {count_rects}")
print(f"Most common size(s): {most_common_groups}")
print(f"Occurrence count: {max_group_count}")
