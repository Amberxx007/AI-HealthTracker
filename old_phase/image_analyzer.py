from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch

# Load model once (slow only first time)
processor = BlipProcessor.from_pretrained("Salesforce/blip2-flan-t5-xl")
model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip2-flan-t5-xl",
    torch_dtype=torch.float32
)

def analyze_medical_image(image_path: str):
    image = Image.open(image_path).convert("RGB")

    prompt = (
        "Describe the medical image. "
        "Mention visible abnormalities, inflammation, wounds, swelling, discoloration. "
        "Do not diagnose. Just describe."
    )

    inputs = processor(images=image, text=prompt, return_tensors="pt")

    output = model.generate(**inputs, max_new_tokens=200)

    description = processor.decode(output[0], skip_special_tokens=True)

    return {
        "image_analysis": description
    }
