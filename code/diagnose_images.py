"""
Diagnostic script — check image formats and test base64 encoding.
Run: python diagnose_images.py
"""
import os
import base64
from pathlib import Path
from PIL import Image
import io

DATASET_DIR = Path(__file__).resolve().parent.parent / "dataset"

def check_image(path):
    full = DATASET_DIR / path
    if not full.exists():
        print(f"  NOT FOUND: {full}")
        return
    
    size_kb = full.stat().st_size / 1024
    
    # Check raw header bytes
    with open(full, "rb") as f:
        header = f.read(20)
    
    # Detect format from magic bytes
    if header[:2] == b'\xff\xd8':
        detected = "JPEG"
    elif header[:8] == b'\x89PNG\r\n\x1a\n':
        detected = "PNG"
    elif header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        detected = "WEBP"
    else:
        detected = f"UNKNOWN (bytes: {header[:8].hex()})"
    
    # Try opening with Pillow
    try:
        img = Image.open(full)
        pil_info = f"Pillow: {img.format} {img.mode} {img.size}"
    except Exception as e:
        pil_info = f"Pillow ERROR: {e}"
    
    # Try base64 encoding
    try:
        with open(full, "rb") as f:
            raw = f.read()
        b64 = base64.b64encode(raw).decode("utf-8")
        b64_len = len(b64)
        has_newlines = '\n' in b64 or '\r' in b64
        b64_info = f"Base64 OK ({b64_len} chars, newlines={has_newlines})"
    except Exception as e:
        b64_info = f"Base64 ERROR: {e}"
    
    print(f"  {path}")
    print(f"    Size: {size_kb:.1f} KB | Header: {detected}")
    print(f"    {pil_info}")
    print(f"    {b64_info}")
    print()

def main():
    # Check a few test images
    test_dir = DATASET_DIR / "images" / "test"
    sample_dir = DATASET_DIR / "images" / "sample"
    
    print("=== TEST IMAGES ===")
    for case_dir in sorted(test_dir.iterdir()):
        if case_dir.is_dir():
            for img_file in sorted(case_dir.iterdir()):
                if img_file.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'):
                    rel = img_file.relative_to(DATASET_DIR)
                    check_image(str(rel))
            break  # Just check first case for diagnostics
    
    print("\n=== SAMPLE IMAGES ===")
    for case_dir in sorted(sample_dir.iterdir()):
        if case_dir.is_dir():
            for img_file in sorted(case_dir.iterdir()):
                if img_file.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'):
                    rel = img_file.relative_to(DATASET_DIR)
                    check_image(str(rel))
            break  # Just check first case

    # Test a minimal Groq vision call
    print("\n=== TESTING GROQ VISION API ===")
    try:
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            print("  No GROQ_API_KEY set!")
            return
        
        client = Groq(api_key=api_key)
        
        # Use Pillow to create a small test image and encode it
        test_img = Image.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()
        test_img.save(buf, format="JPEG", quality=85)
        buf.seek(0)
        b64_str = base64.b64encode(buf.read()).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{b64_str}"
        
        print(f"  Test image base64 length: {len(b64_str)}")
        
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What color is this image? Reply in one word."},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            temperature=0.1,
            max_completion_tokens=50,
        )
        print(f"  ✓ API response: {response.choices[0].message.content}")
        
        # Now try with a real image, re-encoded via Pillow
        first_case = sorted(test_dir.iterdir())[1]  # skip .DS_Store
        first_img = sorted(first_case.iterdir())[0]
        
        img = Image.open(first_img)
        # Resize if needed
        max_dim = 1024
        if max(img.size) > max_dim:
            ratio = max_dim / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        
        # Convert to RGB if needed (handles RGBA, P, etc.)
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        buf.seek(0)
        b64_str = base64.b64encode(buf.read()).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{b64_str}"
        
        print(f"\n  Real image ({first_img.name}): base64 length={len(b64_str)}")
        
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe what you see in this image in one sentence."},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            temperature=0.1,
            max_completion_tokens=100,
        )
        print(f"  ✓ API response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
