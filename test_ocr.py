import sys; sys.path.insert(0, 'd:/ai-doctor-v3')
from services.ocr_engine import OCREngine
ocr = OCREngine()

# Test with Test_01.pdf (urine report)
with open('d:/ai-doctor-v3/test/Test_01.pdf', 'rb') as f:
    result = ocr.extract_from_image(f.read())
print(f'Test_01.pdf: {result["count"]} values')
for r in result['lab_results']:
    print(f'  {r["test_name"]}: {r["value"]} {r["unit"]} ({r["status"]})')

print()

# Test with Test_report.pdf (24-page)
with open('d:/ai-doctor-v3/test/Test_report.pdf', 'rb') as f:
    result2 = ocr.extract_from_image(f.read())
print(f'Test_report.pdf: {result2["count"]} values')
for r in result2['lab_results']:
    print(f'  {r["test_name"]}: {r["value"]} {r["unit"]} ({r["status"]})')
