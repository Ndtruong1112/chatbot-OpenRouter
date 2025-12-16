import gradio as gr
import time
import requests
from typing import List, Tuple
import openai #là 1 thư viện cần thiết để tương tác với OpenRouter
# Cấu hình
API_KEY = "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"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Models ưu tiên theo độ ổn định (từ các model có sẵn trong log)
PRIORITY_MODELS = [
    "deepseek/deepseek-chat-v3-0324:free",
    "qwen/qwen3-coder:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
    "mistralai/mistral-small-3.2-24b-instruct:free",
    "openai/gpt-oss-20b:free",
]

current_model = PRIORITY_MODELS[0] 

print(f"🔑 API Key: {API_KEY[:20]}...{API_KEY[-6:]}")
print(f"🤖 Starting model: {current_model}")

def make_api_call_with_retry(client, model: str, messages: List[dict], max_retries: int = 3):
    """
    Gọi API với retry và timeout handling
    """
    for attempt in range(max_retries):
        try:
            print(f"🔄 Attempt {attempt + 1}/{max_retries} with model: {model}")
            
            # Tăng timeout và giảm tham số để tránh timeout
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1000,      # Giảm token để response nhanh hơn
                temperature=1,     # Giảm creativity để nhanh hơn
                timeout=50,          # Tăng timeout lên 50s
                extra_headers={
                    "HTTP-Referer": "http://localhost:7862",
                    "X-Title": "Simple ChatBot"
                }
            )
            reply = response.choices[0].message.content
            print(f"✅ SUCCESS after {attempt + 1} attempts")
            return reply, model
            
        except openai.APITimeoutError as e:
            print(f"⏰ Timeout on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                print(f"💤 Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            continue
            
        except openai.APIStatusError as e:
            if e.status_code == 408:
                print(f"⏰ 408 Timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 3)  # 3s, 6s, 9s
                continue
            else:
                print(f"❌ API Status Error: {e.status_code} - {e}")
                break
                
        except Exception as e:
            print(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            continue
    
    return None, None

def chat_with_openrouter(message: str, history: List[Tuple[str, str]]):
    """
    Hàm chat với handling timeout và fallback models
    """
    global current_model
    
    print(f"\n📩 New message: {message}")
    
    try:
        client = openai.OpenAI(
            api_key=API_KEY,
            base_url=OPENROUTER_BASE_URL,
            timeout=60.0  # Timeout cho client
        )
        
        # Chuẩn bị messages - giữ ngắn gọn
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Keep responses concise and clear."}
        ]
        
        # Chỉ lấy 3 tin nhắn gần nhất để tránh context quá dài
        recent_history = history[-3:] if len(history) > 3 else history
        
        for user_msg, bot_msg in recent_history:
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if bot_msg:
                messages.append({"role": "assistant", "content": bot_msg})
        
        messages.append({"role": "user", "content": message})
        
        # Thử với model hiện tại trước
        reply, successful_model = make_api_call_with_retry(client, current_model, messages)
        
        if reply:
            if successful_model != current_model:
                current_model = successful_model
                print(f"🔄 Switched to model: {current_model}")
            return reply
        
        # Nếu model hiện tại fail, thử các model khác
        print("🔄 Trying fallback models...")
        for fallback_model in PRIORITY_MODELS:
            if fallback_model == current_model:
                continue  # Đã thử rồi
                
            print(f"🔄 Trying fallback: {fallback_model}")
            reply, successful_model = make_api_call_with_retry(client, fallback_model, messages, max_retries=2)
            
            if reply:
                current_model = fallback_model
                print(f"✅ Fallback successful! Switched to: {current_model}")
                return f"[Switched to {current_model}]\n\n{reply}"
        
        # Nếu tất cả đều fail
        return "❌ Tất cả models đều timeout! Có thể do:\n• OpenRouter quá tải\n• Kết nối mạng chậm\n• Rate limit\n\n🔄 Vui lòng thử lại sau vài phút."
        
    except Exception as e:
        error_msg = f"❌ Lỗi hệ thống: {str(e)}"
        print(f"🚨 System error: {e}")
        return error_msg

def get_model_status():
    """Kiểm tra trạng thái các models"""
    try:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{OPENROUTER_BASE_URL}/models", headers=headers, timeout=10)
        if response.status_code == 200:
            models_data = response.json()
            available_count = len([m for m in models_data.get('data', []) if 'google' in m.get('id', '')])
            return f"✅ {available_count} Google models available"
        else:
            return f"⚠️ Models API: {response.status_code}"
    except:
        return "❌ Cannot check models"

# Tạo interface
with gr.Blocks(title="ChatBot", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 OpenRouter ChatBot ")
    gr.Markdown(f"**Current Model:** `{current_model}`")
    
    # Status panel
    with gr.Accordion("📊 System Status", open=False):
        status_text = gr.Markdown(get_model_status())
        
        def refresh_status():
            return get_model_status()
        
        refresh_btn = gr.Button("🔄 Refresh Status")
        refresh_btn.click(refresh_status, outputs=status_text)
    
    # Main chat
    chatbot = gr.Chatbot(
        height=500,
        show_copy_button=True,
        avatar_images=("👤", "🤖")
    )
    
    msg = gr.Textbox(
        placeholder="Nhập tin nhắn ngắn gọn để tránh timeout...",
        show_label=False,
        max_lines=3
    )
    
    with gr.Row():
        send_btn = gr.Button("📤 Gửi", variant="primary")
        clear_btn = gr.Button("🗑️ Xóa")
        
    # Model selector
    model_dropdown = gr.Dropdown(
        choices=PRIORITY_MODELS,
        value=current_model,
        label="🤖 Chọn Model",
        interactive=True
    )
    
    def change_model(new_model):
        global current_model
        current_model = new_model
        return f"Đã chuyển sang: {new_model}"
    
    def respond(message, chat_history):
        if not message.strip():
            return chat_history, ""
        
        # Hiển thị typing indicator
        thinking_msg = "🤔 Đang suy nghĩ..."
        temp_history = chat_history + [(message, thinking_msg)]
        
        try:
            bot_response = chat_with_openrouter(message, chat_history)
            chat_history.append((message, bot_response))
            return chat_history, ""
        except Exception as e:
            error_response = f"❌ Lỗi: {str(e)}"
            chat_history.append((message, error_response))
            return chat_history, ""
    
    # Event handlers
    msg.submit(respond, [msg, chatbot], [chatbot, msg])
    send_btn.click(respond, [msg, chatbot], [chatbot, msg])
    clear_btn.click(lambda: [], outputs=chatbot)
    model_dropdown.change(change_model, [model_dropdown], None)
    
    # Examples
    gr.Examples(
        examples=[
            "lên cho a con beat số 2",
            "em ăn cơm chưa? ",
            "liệu python có phải là đỉnh xã hội trong thời đại AI không? ",
            "độ mixue có ngu không? ",
            "36 có phải là 1 quốc gia riêng không?"
        ],
        inputs=msg
    )

if __name__ == "__main__":
    print("🚀 Starting timeout-fixed chatbot...")
    try:
        demo.launch(
            inbrowser=True,
            share=False,
            server_name="127.0.0.1",
            server_port=7862,  # Đổi port tránh conflict
            show_error=True,
            debug=False  # Tắt debug để giảm overhead
        )
    except Exception as e:
        print(f"❌ Launch error: {e}")
        demo.launch(inbrowser=True, server_port=0)