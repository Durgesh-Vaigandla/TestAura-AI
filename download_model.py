import os
import urllib.request

def download_model():
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    # We use a very small model for MVP (Qwen2 0.5B, ~350MB)
    model_url = "https://huggingface.co/Qwen/Qwen2-0.5B-Instruct-GGUF/resolve/main/qwen2-0_5b-instruct-q4_k_m.gguf"
    model_path = os.path.join(models_dir, 'qwen2-0_5b-instruct-q4_k_m.gguf')
    
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
    
    if not os.path.exists(model_path):
        print(f"Downloading Qwen2-0.5B model to {model_path} (~350MB)...")
        urllib.request.urlretrieve(model_url, model_path)
        print("Download complete!")
    else:
        print("Model already exists.")

if __name__ == "__main__":
    download_model()
