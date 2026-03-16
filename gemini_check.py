"""
Jalankan: py check_gemini.py
Untuk cek model Gemini mana yang bisa dipakai dengan API key kamu
"""
import urllib.request, json

API_KEY = "AIzaSyC7G16-4iEeruUKJBJQW_zood1q3PYkjes"

print("=== CEK MODEL TERSEDIA ===")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
try:
    with urllib.request.urlopen(url, timeout=10) as r:
        data = json.loads(r.read())
    models = data.get('models', [])
    print(f"Total models: {len(models)}\n")
    print("Model yang support generateContent:")
    for m in models:
        name      = m.get('name', '')
        supported = m.get('supportedGenerationMethods', [])
        if 'generateContent' in supported:
            print(f"  ✓ {name}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== TEST GENERATE ===")
# Coba model-model umum
models_to_try = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-pro",
]
for model in models_to_try:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
    body = json.dumps({"contents": [{"parts": [{"text": "Say hi"}]}]}).encode()
    req  = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print(f"  ✓ WORKS: {model}")
            break
    except urllib.error.HTTPError as e:
        print(f"  ✗ {e.code}: {model}")
    except Exception as e:
        print(f"  ✗ ERR: {model} — {e}")