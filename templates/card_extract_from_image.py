import cv2
import numpy as np

def extract_card_template(image_path, output_path):
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Cannot load image from {image_path}")
        return

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5,5), 0)

    # Canny edge detection (adjust values if needed)
    edges = cv2.Canny(blurred, 30, 120)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # DEBUG: Draw all contours to visualize
    debug_img = image.copy()
    cv2.drawContours(debug_img, contours, -1, (0,255,0), 2)
    cv2.imwrite('debug_contours.png', debug_img)

    card_contour = None
    max_area = 0
    # Find the largest approximate 4-point contour as the card
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 200:  # Lowered threshold for small cards, adjust as necessary
            continue
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        if len(approx) == 4 and area > max_area:
            max_area = area
            card_contour = approx

    if card_contour is None:
        print("Error: Card contour not found")
        return

    # Get bounding box and extract the card area
    x, y, w, h = cv2.boundingRect(card_contour)
    card_img = image[y:y+h, x:x+w]

    # Resize to standard template size
    card_template = cv2.resize(card_img, (64, 64))

    # Save the extracted template
    cv2.imwrite(output_path, card_template)
    print(f"Template saved to {output_path}")

# 用法範例：
result = extract_card_template('input_image.png', 'output_template.png')
print(result)
