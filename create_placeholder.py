from PIL import Image, ImageDraw, ImageFont
import os

# Create directory if it doesn't exist
image_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
os.makedirs(image_dir, exist_ok=True)

# Create a new image with a light gray background
width = 300
height = 200
color = (211, 211, 211)  # Light gray

image = Image.new('RGB', (width, height), color)
draw = ImageDraw.Draw(image)

# Add text
text = "Exercise"
text_color = (100, 100, 100)  # Dark gray

# Calculate text position (center)
text_bbox = draw.textbbox((0, 0), text)
text_width = text_bbox[2] - text_bbox[0]
text_height = text_bbox[3] - text_bbox[1]
text_x = (width - text_width) // 2
text_y = (height - text_height) // 2

# Draw the text
draw.text((text_x, text_y), text, fill=text_color)

# Save the image
image_path = os.path.join(image_dir, 'default-exercise.jpg')
image.save(image_path, 'JPEG')
print(f"Created placeholder image at: {image_path}")
