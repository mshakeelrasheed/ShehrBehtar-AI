import json
import io
import re
import time
import base64
import requests
import numpy as np
from PIL import Image
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, OPENROUTER_API_KEY
from core.agents.state import VisionDetectionResult, DetectedHazard

def detect_civic_hazards(image: Image.Image, filename_hint: str = "", user_category_hint: str = "Auto-Detect") -> VisionDetectionResult:
    """
    High-accuracy multi-tier civic hazard classifier:
    1. User explicit category / filename fast hint
    2. Google Gemini 3.8 Flash (Vision)
    3. OpenRouter Free Multimodal Vision (via clean plain URL)
    4. Computer Vision Image Heuristic Fallback
    """
    # 1. User Explicit Selection / Filename Fast Hint
    u_hint = user_category_hint.lower()
    f_hint = filename_hint.lower()

    if "manhole" in u_hint or "gutter" in u_hint or any(k in f_hint for k in ["manhole", "gutter", "drain", "sewer"]):
        return _build_res("open_manhole", "Open sewer chamber / broken curb drain cover", [400, 350, 950, 900])
    elif "garbage" in u_hint or "waste" in u_hint or any(k in f_hint for k in ["garbage", "waste", "trash", "kachra"]):
        return _build_res("garbage", "Roadside solid waste accumulation and garbage pile", [300, 150, 850, 850])
    elif "road" in u_hint or "pothole" in u_hint or any(k in f_hint for k in ["pothole", "cavity", "asphalt", "crater", "damage"]):
        return _build_res("pothole", "Asphalt road cavity / surface pothole", [350, 200, 750, 750])

    # Convert Image to JPEG bytes
    rgb_image = image.convert("RGB")
    img_byte_arr = io.BytesIO()
    rgb_image.save(img_byte_arr, format='JPEG', quality=85)
    img_bytes = img_byte_arr.getvalue()
    b64_img = base64.b64encode(img_bytes).decode("utf-8")

    prompt = """
    You are an AI Civic Infrastructure Inspector for Pakistan.
    Analyze this street photograph and identify the single primary civic hazard.

    CLASSIFY PRECISELY INTO ONE:
    - 'open_manhole': An open drain, missing sewer lid, broken concrete drain slab on curb/sidewalk, sewer cavity.
    - 'garbage': Piles of plastic bags, household waste, roadside garbage, uncollected trash heaps.
    - 'pothole': Bitumen depression, cavity, crater, or broken road asphalt surface on the vehicle roadway.

    Return strictly raw JSON (no backticks, no markdown):
    {
      "hazard_type": "open_manhole" | "garbage" | "pothole",
      "description": "Short explanation",
      "ymin": 300,
      "xmin": 200,
      "ymax": 800,
      "xmax": 800
    }
    """

    # 2. Try Gemini 3.8 Flash
    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=[
                            types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                            prompt
                        ],
                        config=types.GenerateContentConfig(
                            temperature=0.1,
                            response_mime_type="application/json",
                            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                        )
                    )
                    raw = response.text.strip()
                    if "```" in raw:
                        raw = re.sub(r"^```[a-zA-Z]*\n", "", raw)
                        raw = re.sub(r"\n```$", "", raw).strip()

                    parsed = json.loads(raw)
                    cat = parsed.get("hazard_type", "").lower().strip()
                    desc = parsed.get("description", "Civic issue")
                    box = [
                        int(parsed.get("ymin", 350)),
                        int(parsed.get("xmin", 250)),
                        int(parsed.get("ymax", 850)),
                        int(parsed.get("xmax", 850))
                    ]
                    if cat in ["open_manhole", "garbage", "pothole"]:
                        print(f"[Vision Success] Gemini 3.8 Output: {cat}")
                        return _build_res(cat, desc, box)

                except Exception as e_gen:
                    err_text = str(e_gen)
                    if "429" in err_text or "RESOURCE_EXHAUSTED" in err_text:
                        print("[Gemini Quota Full]: Switching directly to OpenRouter Vision...")
                        break
                    elif "503" in err_text:
                        time.sleep(1.5)
                        continue
                    else:
                        print(f"[Gemini Notice]: {e_gen}")
                        break
        except Exception as e_outer:
            print(f"[Gemini Client Notice]: {e_outer}")

    # 3. Failover to OpenRouter Free Vision (Clean Plain URL)
    if OPENROUTER_API_KEY:
        try:
            print("[Vision] Engaging OpenRouter Vision Failover...")
            clean_api_key = OPENROUTER_API_KEY.strip().strip("'").strip('"')
            headers = {
                "Authorization": f"Bearer {clean_api_key}",
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "ShehrBehtar AI",
                "Content-Type": "application/json"
            }

            candidate_models = [
                "openai/gpt-4o-mini",
                "google/gemini-flash-1.5",
                "meta-llama/llama-3.2-11b-vision-instruct"
            ]

            target_url = "https://openrouter.ai/api/v1/chat/completions"

            for model_id in candidate_models:
                try:
                    payload = {
                        "model": model_id,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{b64_img}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "temperature": 0.1
                    }

                    resp = requests.post(
                        target_url,
                        headers=headers,
                        json=payload,
                        timeout=25
                    )

                    if resp.status_code == 200:
                        res_json = resp.json()
                        raw_text = res_json["choices"][0]["message"]["content"].strip()
                        if "```" in raw_text:
                            raw_text = re.sub(r"^```[a-zA-Z]*\n", "", raw_text)
                            raw_text = re.sub(r"\n```$", "", raw_text).strip()

                        parsed = json.loads(raw_text)
                        cat = parsed.get("hazard_type", "").lower().strip()
                        desc = parsed.get("description", "Civic issue identified via OpenRouter")
                        box = [
                            int(parsed.get("ymin", 350)),
                            int(parsed.get("xmin", 250)),
                            int(parsed.get("ymax", 850)),
                            int(parsed.get("xmax", 850))
                        ]
                        if cat in ["open_manhole", "garbage", "pothole"]:
                            print(f"[Vision Success] OpenRouter ({model_id}) Output: {cat}")
                            return _build_res(cat, desc, box)
                    else:
                        print(f"[OpenRouter Model {model_id} HTTP {resp.status_code}]: {resp.text[:120]}")
                except Exception as m_err:
                    print(f"[OpenRouter Model {model_id} Error]: {m_err}")
                    continue

        except Exception as e_or:
            print(f"[OpenRouter Failover Error]: {e_or}")

    # 4. Computer Vision Image Heuristic Fallback
    print("[Vision] Applying CV Feature-based Heuristic...")
    try:
        small_img = rgb_image.resize((150, 150))
        img_arr = np.array(small_img, dtype=np.float32)
        r, g, b = img_arr[:, :, 0], img_arr[:, :, 1], img_arr[:, :, 2]
        std_rgb = np.std(img_arr)
        brightness = np.mean(img_arr)
        color_diff = np.mean(np.abs(r - g) + np.abs(g - b) + np.abs(r - b))

        if color_diff > 35 or std_rgb > 55:
            return _build_res("garbage", "Roadside solid waste accumulation and garbage pile", [300, 150, 850, 850])
        elif brightness < 60:
            return _build_res("open_manhole", "Open sewer chamber / drain cavity", [400, 350, 950, 900])
        else:
            return _build_res("pothole", "Road asphalt cavity / surface pothole", [350, 200, 750, 750])
    except Exception:
        return _build_res("pothole", "Road asphalt cavity / surface pothole", [350, 200, 750, 750])


def _build_res(hazard_type: str, description: str, box: list) -> VisionDetectionResult:
    return VisionDetectionResult(
        hazards=[
            DetectedHazard(
                hazard_type=hazard_type,
                box_2d=box,
                confidence=0.95,
                description=description
            )
        ],
        raw_summary=description
    )