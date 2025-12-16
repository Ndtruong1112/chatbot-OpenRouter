import gradio as gr
import requests
import time
from typing import List, Tuple

# 🔑 Nhập OpenRouter API key ở đây
API_KEY = "sk-..."  # ← Thay bằng key của bạn

# 🔗 Base URL của OpenRouter
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# 🔁 Danh sách các model có thật (từ OpenRouter)
PRIORITY_MODELS = [
    "mistralai/mistral-7b-instruct",
    "meta-llama/Meta-Llama-3-8B-Instruct",
    "meta-llama/Meta-Llama-3-70B-Instruct",
    "google/gemma-7b-it",
    "openchat/openchat-3.5-0106"
]

def make_api_call_with_retry(model: str, messages: List[dict], max_retries: int = 3) -> Tuple[str, str]:
    for attempt in range(max_retries):
        try:
            print(f"🔄 Attempt {attempt + 1}/{max_retries} with model: {model}")
            
            response = requests.post(
                url=f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                    "X-Title": "Simple Gradio Chatbot"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 1000,
                    "temperature": 1
                },
                timeout=50
            )
            
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
            print(f"✅ SUCCESS after {attempt + 1} attempts")
            return reply, model
            
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout on attempt {attempt + 1}")
            time.sleep(2 * (attempt + 1))
            continue
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            time.sleep(2)
            continue

    return None, None

def chat_with_openrouter(user_input, history):
    messages = []
    if history:
        for user, bot in history:
            messages.append({"role": "user", "content": user})
            messages.append({"role": "assistant", "content": bot})

    messages.append({"role": "user", "content": user_input})

    for current_model in PRIORITY_MODELS:
        reply, successful_model = make_api_call_with_retry(current_model, messages)
        if reply:
            print(f"✅ Model used: {successful_model}")
            return reply
        else:
            print(f"⚠️ Model {current_model} failed, trying next...")

    return "❌ Tất cả models đều timeout! Có thể do:\n• OpenRouter quá tải\n• Kết nối mạng chậm\n• Rate limit\n\n🔁 Vui lòng thử lại sau vài phút."

with gr.ChatInterface(chat_with_openrouter, title="💬 Chatbot dùng OpenRouter") as demo:
    demo.launch()
