from PIL import Image, ImageDraw, ImageFont
from typing import List
from config import HAZARD_CONFIG
from core.agents.state import DetectedHazard

def hex_to_rgb(hex_str: str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def annotate_image_with_hazards(image: Image.Image, hazards: List[DetectedHazard]) -> Image.Image:
    """
    Draws professional bounding boxes and class labels over the detected hazards.
    Handles normalized [0-1000] scale coordinates mapping to original dimensions.
    """
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    width, height = annotated.size

    for hazard in hazards:
        h_type = hazard.hazard_type.lower()
        cfg = HAZARD_CONFIG.get(h_type, HAZARD_CONFIG["pothole"])
        box_color = hex_to_rgb(cfg["color"])

        ymin, xmin, ymax, xmax = hazard.box_2d

        # Scale from 1000-base to pixel dimensions
        x1 = int((xmin / 1000.0) * width)
        y1 = int((ymin / 1000.0) * height)
        x2 = int((xmax / 1000.0) * width)
        y2 = int((ymax / 1000.0) * height)

        # Draw thick rectangular bounding box
        border_width = max(3, int(min(width, height) * 0.006))
        for i in range(border_width):
            draw.rectangle([x1 - i, y1 - i, x2 + i, y2 + i], outline=box_color)

        # Draw header badge
        label_text = f"{cfg['label']} ({int(hazard.confidence * 100)}%)"
        text_bbox = draw.textbbox((x1, y1), label_text)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]

        badge_y1 = max(0, y1 - text_h - 10)
        badge_y2 = badge_y1 + text_h + 8
        badge_x2 = x1 + text_w + 12

        draw.rectangle([x1, badge_y1, badge_x2, badge_y2], fill=box_color)
        draw.text((x1 + 6, badge_y1 + 4), label_text, fill=(255, 255, 255))

    return annotated