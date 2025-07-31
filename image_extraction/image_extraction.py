import os
import cv2
import numpy as np

def process_cards_in_folder(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            image_path = os.path.join(input_folder, filename)
            print(f"Processing {image_path}...")

            image = cv2.imread(image_path)
            if image is None:
                print(f"Error: Cannot load image from {image_path}")
                continue

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5,5), 0)
            edges = cv2.Canny(blurred, 30, 120)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            card_contour = None
            max_area = 0
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 200:
                    continue
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                if len(approx) == 4 and area > max_area:
                    max_area = area
                    card_contour = approx

            if card_contour is None:
                print(f"Error: Card contour not found in {filename}")
                continue

            x, y, w, h = cv2.boundingRect(card_contour)
            print(f"Original card size for {filename}: x={x}, y={y}, w={w}, h={h}")

            from math import gcd
            ratio_gcd = gcd(w, h)
            ratio_str = f"{w//ratio_gcd}/{h//ratio_gcd}"
            print(f"Width/Height ratio for {filename}: {ratio_str}")


            card_img = image[y:y+h, x:x+w]
            output_name = f"symbol_{os.path.splitext(filename)[0]}.png"
            output_path = os.path.join(output_folder, output_name)

            cv2.imwrite(output_path, card_img)
            print(f"Saved extracted card to {output_path}")

# 用法範例：
process_cards_in_folder('input_folder', 'output_folder')
