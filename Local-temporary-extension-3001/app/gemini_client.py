"""
gemini_client.py — Khởi tạo kết nối Gemini API ẩn
Module xử lý logic gọi thư viện HTTP API ngầm của Google Gemini để tự động tạo ảnh dựa vào Cookie (bỏ qua UI Automation).
"""
import uuid
import asyncio
import re
from gemini_webapi import GeminiClient
from .gemini_config import load_gemini_config

async def generate_gemini_image(prompt: str, cookies_str: str, snlm0e: str, auth_bl: str = None) -> list[str]:
    """
    Called by the backend worker logic to generate an image directly from the server.
    Dynamically loads payload structure from gemini_settings.json.
    """
    cfg = load_gemini_config()
    
    # Cookie overrides from config
    cfg_cookies = cfg.get("cookies", {})
    secure_1psid = cfg_cookies.get("__Secure-1PSID", "").strip()
    secure_1psidts = cfg_cookies.get("__Secure-1PSIDTS", "").strip()
    
    # If config doesn't have custom ones, parse from cookies_str (extension fallback)
    if not secure_1psid or not secure_1psidts:
        cookie_dict = {}
        for c in cookies_str.split(';'):
            if '=' in c:
                k, v = c.strip().split('=', 1)
                cookie_dict[k] = v
        
        if not secure_1psid: secure_1psid = cookie_dict.get("__Secure-1PSID", "")
        if not secure_1psidts: secure_1psidts = cookie_dict.get("__Secure-1PSIDTS", "")
        
    if not secure_1psid or not secure_1psidts:
        print("Missing required cookies (__Secure-1PSID or __Secure-1PSIDTS) in cookies_str and config!")
        return []

    client = GeminiClient(
        secure_1psid=secure_1psid,
        secure_1psidts=secure_1psidts,
        # proxy="http://your-proxy:port" # Uncomment if proxy is needed from config
    )
    
    timeout_val = cfg.get("timeout", 120)
    try:
        await client.init(
            timeout=timeout_val,
            auto_close=False,
            auto_refresh=True,
            verbose=False
        )
    except Exception as e:
        print(f"Error initializing GeminiClient: {e}")
        return []

    request_uuid = str(uuid.uuid4()).upper()
    
    # Build model_header
    raw_header = cfg.get("model_header", {})
    model_header = {}
    for k, v in raw_header.items():
        if isinstance(v, str):
            model_header[k] = v.replace("{request_uuid}", request_uuid)
        else:
            model_header[k] = v

    # Build image_gen_fields (convert string keys to int for python dict compatibility)
    from typing import Any
    raw_gen_fields = cfg.get("image_gen_fields", {})
    image_gen_fields: dict[Any, Any] = {}
    for k, v in raw_gen_fields.items():
        val = v.replace("{request_uuid}", request_uuid) if isinstance(v, str) else v
        try:
            image_gen_fields[int(k)] = val
        except ValueError:
            image_gen_fields[k] = val
            
    model_dict = {
        "model_name": cfg.get("model_code", "gemini-image-gen"),
        "model_header": model_header,
        "image_gen_fields": image_gen_fields,
    }
    
    # Force gemini to use the drawing tool if the prompt is just a noun
    prompt_to_send = prompt
    lower_prompt = prompt.lower()
    if not any(kw in lower_prompt for kw in ["vẽ", "tạo", "gen", "draw", "create", "ảnh", "bức tranh"]):
        prompt_to_send = f"Vẽ một bức ảnh thật chi tiết và đẹp về: {prompt}"

    try:
        response = await client.generate_content(prompt_to_send, model=model_dict)
        urls = []
        images = getattr(response, "images", [])
        if not images:
            print(f"[-] Gemini responded but returned NO IMAGES for prompt: '{prompt}'")
            print(f"[-] Response Text: {getattr(response, 'text', str(response))}")
            
        import os
        import time
        import re
        os.makedirs(os.path.join("static", "images"), exist_ok=True)
        
        # Tạo chuỗi tên an toàn từ prompt
        safe_prompt = re.sub(r'[\\/*?:"<>|]', "", prompt)
        safe_prompt = safe_prompt.replace(' ', '_').replace('\n', '')[:40]
        if not safe_prompt:
            safe_prompt = "image"
            
        for i, img in enumerate(images):
            # Tuỳ thuộc vào cấu trúc object image tĩnh của gemini_webapi, nó có hàm save()
            if hasattr(img, "save"):
                timestamp_str = str(int(time.time()*100))
                # Gọi thẳng hàm save() để nó xử lý auth và tải ảnh bản gốc mượt nhất
                # Tạm lưu gốc bằng cách không cung cấp đuôi file (hàm save sẽ tự detect đuôi như .jpg)
                # Provide a default extension so fallback works properly
                temp_filename = f"tmp_{safe_prompt}_{timestamp_str}_{i}.jpg"
                saved_path = await img.save(path=os.path.join("static", "images"), filename=temp_filename)
                
                if saved_path:
                    # Dùng PIL để convert ra 2 định dạng
                    try:
                        from PIL import Image
                        with Image.open(saved_path) as pil_img:
                            # Chuyển sang RGB nếu cần lưu jpeg/webp tốt
                            if pil_img.mode in ("RGBA", "P"):
                                pil_img = pil_img.convert("RGB")
                            
                            img_dir = os.path.dirname(saved_path)
                            base_filename = f"{safe_prompt}_{timestamp_str}_{i}"
                            
                            png_path = os.path.join(img_dir, f"{base_filename}.png")
                            # webp_path = os.path.join(img_dir, f"{base_filename}.webp")
                            
                            # Lưu bản PNG
                            pil_img.save(png_path, format="PNG")
                            # pil_img.save(webp_path, format="WEBP", quality=95)
                            
                        # Đẩy cái png vào danh sách URLs trả về cho UI
                        # urls.append(f"/static/images/{base_filename}.webp")
                        urls.append(f"/static/images/{base_filename}.png")
                        
                        # Xoá file tmp gốc
                        try:
                            # if str(saved_path) != str(png_path) and str(saved_path) != str(webp_path):
                            if str(saved_path) != str(png_path):
                                os.remove(saved_path)
                        except:
                            pass
                            
                    except Exception as e:
                        print(f"Lỗi khi xử lý ảnh bằng PIL: {e}")
                        # Fallback về bản gốc
                        if os.path.exists(saved_path):
                            basename = os.path.basename(saved_path)
                            # Đảm bảo file có extension
                            if '.' not in basename:
                                new_path = f"{saved_path}.jpg"
                                os.rename(saved_path, new_path)
                                basename = f"{basename}.jpg"
                            urls.append(f"/static/images/{basename}")
                else:
                    img_url = getattr(img, "url", getattr(img, "image_url", str(img)))
                    urls.append(img_url)
            else:
                img_url = getattr(img, "url", getattr(img, "image_url", str(img)))
                if "=s1024-rj" in img_url:
                    img_url = img_url.replace("=s1024-rj", "=s2048-rj")
                elif "=s2048-rj" not in img_url and "googleusercontent" in img_url:
                    img_url += "=s2048-rj"
                    
                urls.append(img_url)
            
        return list(set(urls))
    except Exception as e:
        import traceback
        print(f"[!] Error generating gemini image content: {e}")
        traceback.print_exc()
        return []
    finally:
        await client.close()
