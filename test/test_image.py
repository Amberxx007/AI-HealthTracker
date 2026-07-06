from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration

device = "cuda" if torch.cuda.is_available() else "cpu"

processor = BlipProcessor.from_pretrained(
    "Salesforce/blip-image-captioning-base"
)

model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base"
).to(device)

image = Image.open("test_image.jpg").convert("RGB")

inputs = processor(image, return_tensors="pt").to(device)

out = model.generate(**inputs, max_new_tokens=40)
caption = processor.decode(out[0], skip_special_tokens=True)

print("🖼 Image analysis:")
print(caption)
# Expected output: A descriptive caption of the image content.