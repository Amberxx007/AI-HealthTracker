"""Full end-to-end test of all API endpoints"""
import requests
import json
import time
from PIL import Image
import io
import numpy as np

API = "http://localhost:8000"

def test_chat_english():
    print("=" * 60)
    print("TEST 1: Text chat (English)")
    print("=" * 60)
    start = time.time()
    r = requests.post(f"{API}/api/chat", json={
        "patient_id": "test_full_01",
        "message": "I have a severe headache and feeling dizzy since yesterday",
        "language": "en"
    })
    elapsed = time.time() - start
    d = r.json()
    print(f"Status: {r.status_code} ({elapsed:.1f}s)")
    print(f"Triage level: {d.get('triage', {}).get('level', 'N/A')}")
    resp = d.get("response_text", "")
    print(f"Response ({len(resp)} chars): {resp[:300]}...")
    print(f"Session: {d.get('session_id', 'N/A')}")
    assert r.status_code == 200
    assert len(resp) > 50, f"Response too short: {resp}"
    assert "apologize" not in resp.lower(), f"Got fallback response: {resp[:100]}"
    print("PASS\n")
    return d.get("session_id")


def test_chat_hindi():
    print("=" * 60)
    print("TEST 2: Text chat (Hindi)")
    print("=" * 60)
    start = time.time()
    r = requests.post(f"{API}/api/chat", json={
        "patient_id": "test_full_01",
        "message": "mujhe sar mein bahut dard ho raha hai aur chakkar aa rahe hain",
        "language": "hi"
    })
    elapsed = time.time() - start
    d = r.json()
    print(f"Status: {r.status_code} ({elapsed:.1f}s)")
    print(f"Triage level: {d.get('triage', {}).get('level', 'N/A')}")
    resp = d.get("response_text", "")
    print(f"Response ({len(resp)} chars): {resp[:300]}...")
    assert r.status_code == 200
    assert len(resp) > 50
    assert "apologize" not in resp.lower(), f"Got fallback response: {resp[:100]}"
    print("PASS\n")


def test_streaming_chat():
    print("=" * 60)
    print("TEST 3: Streaming chat (SSE)")
    print("=" * 60)
    start = time.time()
    r = requests.post(f"{API}/api/chat/stream", json={
        "patient_id": "test_full_01",
        "message": "I have a skin rash on my left arm that is red and itchy",
        "language": "en"
    }, stream=True)
    elapsed_first = None
    full_text = ""
    triage_info = None
    chunks = 0

    for line in r.iter_lines():
        if not line:
            continue
        decoded = line.decode("utf-8")
        if not decoded.startswith("data: "):
            continue
        data = decoded[6:]
        if data.strip() == "[DONE]":
            break
        try:
            p = json.loads(data)
            if p["type"] == "triage":
                triage_info = p
            elif p["type"] == "chunk":
                chunks += 1
                full_text += p["content"]
                if elapsed_first is None:
                    elapsed_first = time.time() - start
            elif p["type"] == "done":
                pass
        except json.JSONDecodeError:
            pass

    elapsed = time.time() - start
    print(f"Status: {r.status_code}")
    print(f"First token: {elapsed_first:.1f}s, Total: {elapsed:.1f}s")
    print(f"Chunks received: {chunks}")
    print(f"Triage: {triage_info}")
    print(f"Response ({len(full_text)} chars): {full_text[:300]}...")
    assert r.status_code == 200
    assert chunks > 5, f"Too few chunks: {chunks}"
    assert len(full_text) > 50
    print("PASS\n")


def test_image_analysis():
    print("=" * 60)
    print("TEST 4: Image analysis (non-streaming)")
    print("=" * 60)
    # Create a reddish patch image simulating a rash
    img = Image.new("RGB", (300, 300), color=(220, 80, 80))
    # Add some variation
    pixels = img.load()
    for x in range(100, 200):
        for y in range(100, 200):
            pixels[x, y] = (255, 50, 50)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    start = time.time()
    r = requests.post(f"{API}/api/image/analyze", files={
        "image": ("rash_test.jpg", buf, "image/jpeg")
    }, data={
        "patient_id": "test_full_01",
        "body_region": "left_arm",
        "image_type": "photo",
        "description": "Red rash on my arm"
    })
    elapsed = time.time() - start
    d = r.json()
    print(f"Status: {r.status_code} ({elapsed:.1f}s)")
    print(f"Vision analysis: {d.get('analysis', 'N/A')[:200]}")
    print(f"Interpretation ({len(d.get('interpretation', ''))} chars): {d.get('interpretation', '')[:300]}...")
    assert r.status_code == 200
    # The analysis should NOT be echoing the prompt
    analysis = d.get("analysis", "").lower()
    assert "do not diagnose" not in analysis, f"BLIP echoing prompt: {analysis}"
    assert "apologize" not in d.get("interpretation", "").lower(), "LLM timed out"
    print("PASS\n")


def test_image_stream():
    print("=" * 60)
    print("TEST 5: Image analysis (streaming)")
    print("=" * 60)
    img = Image.new("RGB", (300, 300), color=(200, 150, 100))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    start = time.time()
    r = requests.post(f"{API}/api/image/analyze/stream", files={
        "image": ("wound_test.jpg", buf, "image/jpeg")
    }, data={
        "patient_id": "test_full_01",
        "body_region": "right_arm",
        "image_type": "photo"
    }, stream=True)

    vision_desc = None
    full_text = ""
    chunks = 0
    for line in r.iter_lines():
        if not line:
            continue
        decoded = line.decode("utf-8")
        if not decoded.startswith("data: "):
            continue
        data = decoded[6:]
        if data.strip() == "[DONE]":
            break
        try:
            p = json.loads(data)
            if p["type"] == "vision":
                vision_desc = p.get("description")
            elif p["type"] == "chunk":
                chunks += 1
                full_text += p["content"]
            elif p["type"] == "error":
                print(f"ERROR: {p.get('content')}")
        except json.JSONDecodeError:
            pass

    elapsed = time.time() - start
    print(f"Status: {r.status_code} ({elapsed:.1f}s)")
    print(f"Vision desc: {vision_desc}")
    print(f"Chunks: {chunks}")
    print(f"Response ({len(full_text)} chars): {full_text[:300]}...")
    assert r.status_code == 200
    assert chunks > 0, "No streaming chunks received"
    print("PASS\n")


def test_report_ocr():
    print("=" * 60)
    print("TEST 6: Lab report OCR parsing")
    print("=" * 60)
    # Create a test image with lab values text
    img = Image.new("RGB", (600, 400), color=(255, 255, 255))
    # We can't easily add text to an image without pillow-draw, but the OCR
    # should still process the image even if it finds no lab values
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    start = time.time()
    r = requests.post(f"{API}/api/report/parse", files={
        "image": ("report_test.jpg", buf, "image/jpeg")
    }, data={
        "patient_id": "test_full_01"
    })
    elapsed = time.time() - start
    d = r.json()
    print(f"Status: {r.status_code} ({elapsed:.1f}s)")
    print(f"Raw text: {d.get('raw_text', 'N/A')[:200]}")
    print(f"Lab results: {d.get('lab_results', [])}")
    print(f"Count: {d.get('count', 0)}")
    assert r.status_code == 200
    print("PASS\n")


def test_dashboard():
    print("=" * 60)
    print("TEST 7: Patient dashboard")
    print("=" * 60)
    r = requests.get(f"{API}/api/patient/test_full_01/dashboard")
    d = r.json()
    print(f"Status: {r.status_code}")
    print(f"Patient: {d.get('patient', {}).get('patient_id', 'N/A')}")
    print(f"Timeline events: {len(d.get('timeline', []))}")
    print(f"Body map regions: {list(d.get('body_map', {}).keys())}")
    print(f"Lab results: {len(d.get('recent_labs', []))}")
    print(f"Images: {len(d.get('recent_images', []))}")
    print(f"Sessions: {len(d.get('sessions', []))}")
    assert r.status_code == 200
    print("PASS\n")


def test_patient_update():
    print("=" * 60)
    print("TEST 8: Patient profile update")
    print("=" * 60)
    r = requests.put(f"{API}/api/patient/test_full_01", json={
        "name": "Test User",
        "age": 30,
        "gender": "male",
        "blood_group": "O+",
        "allergies": "penicillin",
        "chronic_conditions": "none"
    })
    d = r.json()
    print(f"Status: {r.status_code}")
    print(f"Patient: {d}")
    assert r.status_code == 200
    assert d.get("name") == "Test User"
    print("PASS\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("    FULL API TEST SUITE")
    print("=" * 60 + "\n")

    # Quick health check first
    try:
        r = requests.get(f"{API}/api/health", timeout=5)
        print(f"Server health: {r.json()}\n")
    except Exception as e:
        print(f"Server not reachable: {e}")
        exit(1)

    passed = 0
    failed = 0
    tests = [
        test_chat_english,
        test_chat_hindi,
        test_streaming_chat,
        test_image_analysis,
        test_image_stream,
        test_report_ocr,
        test_dashboard,
        test_patient_update,
    ]

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"FAIL: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)}")
    print("=" * 60)
