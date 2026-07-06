import requests, json
from PIL import Image
import io

API = "http://localhost:8000"

# Test report parse
img = Image.new("RGB", (600, 400), (255, 255, 255))
buf = io.BytesIO()
img.save(buf, format="JPEG")
buf.seek(0)
r = requests.post(f"{API}/api/report/parse", files={"image": ("r.jpg", buf, "image/jpeg")}, data={"patient_id": "test_02"})
d = r.json()
print(f"Report parse: {r.status_code}, count={d.get('count', 0)}")

# Test dashboard
r2 = requests.get(f"{API}/api/patient/test_full_01/dashboard")
d2 = r2.json()
print(f"Dashboard: {r2.status_code}, timeline={len(d2.get('timeline', []))}, labs={len(d2.get('recent_labs', []))}, images={len(d2.get('recent_images', []))}, bodymap={list(d2.get('body_map', {}).keys())}")

# Test patient update
r3 = requests.put(f"{API}/api/patient/test_full_01", json={"name": "Test User", "age": 30, "gender": "male"})
print(f"Patient update: {r3.status_code}, name={r3.json().get('name')}")

print("\nAll quick tests passed!")
