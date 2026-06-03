# TestAura AI

TestAura AI is an offline-first, enterprise-grade Requirement Intelligence and BDD Scenario Generation platform. It runs entirely on your local hardware (Apple Silicon or Windows/Linux), ensuring proprietary enterprise requirements are never sent to external third-party APIs.

It parses Software Requirement Specifications (DOCX/PDF), extracts actors, roles, and business rules, scores the requirements for clarity and testability, and uses an integrated Small Language Model (SLM) to automatically generate comprehensive Gherkin BDD test suites (Smoke Tests, Happy Paths, Negative Tests, Validations, and RBAC).

---

## 🏗 Architecture
- **Backend**: Python 3, Flask
- **Database**: SQLite (Local, offline-first)
- **Frontend**: HTMX, Tailwind CSS, Jinja2
- **AI Engine**: `llama-cpp-python` (Hardware Accelerated via Metal on Mac, or CUDA/OpenBLAS on Windows)
- **Models**: Qwen2-0.5B-Instruct (GGUF format)

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+
- `git`
- (Mac) Xcode Command Line Tools: `xcode-select --install`
- (Windows) C++ Build Tools (via Visual Studio Installer) for compiling `llama-cpp-python`.

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/TestAura-AI.git
cd TestAura-AI
```

### 2. Create a Virtual Environment
**Mac / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```
**Windows:**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. Install Dependencies
TestAura uses `llama-cpp-python` to run the AI engine locally. The installation command differs depending on your hardware.

**🍎 Mac (Apple Silicon / M1 / M2 / M3 / M4)**
To enable ultra-fast hardware acceleration using Apple's Metal GPU:
```bash
CMAKE_ARGS="-DGGML_METAL=on" pip install -r requirements.txt
```

**🪟 Windows (NVIDIA GPU)**
If you have an NVIDIA graphics card, you can offload processing to it via CUDA for massive speedups. (Requires CUDA toolkit installed):
```powershell
$env:CMAKE_ARGS="-DGGML_CUDA=on"
pip install -r requirements.txt
```

**💻 Windows / Linux (CPU Only)**
If you don't have a dedicated GPU, you can still run it perfectly fine on your CPU (it will just be slightly slower):
```powershell
pip install -r requirements.txt
```

### 4. Download the AI Model
Run the included script to download the Qwen-0.5B GGUF model into the `models/` directory:
```bash
python download_model.py
```

### 5. Initialize the Database
Set up the local SQLite database to store your requirements and generated scenarios:
```bash
python run.py --init-db
```

---

## 🎮 Running the Application

To start the TestAura AI server:
```bash
# On Mac/Linux
./run.sh

# Or manually on any OS:
python run.py
```

The application will be available at: **http://127.0.0.1:5001**

### Cross-Platform Note
The system is built to be seamlessly cross-platform. When you trigger AI Scenario Generation, the backend automatically detects if hardware acceleration is available. Because we specify `n_gpu_layers=-1`, the engine will attempt to offload 100% of the AI processing to your GPU (Metal on Mac, CUDA on Windows). If no GPU is found, it gracefully falls back to CPU processing without throwing errors.

---

## 🛠 Features
- **Document Parsing**: Upload DOCX/PDF files. TestAura parses hierarchical sections and calculates a Health Score based on requirement clarity.
- **Traceability**: Requirements are stored with strict ID linking.
- **Background Generation**: Select multiple requirements and instantly fire off background tasks to generate hundreds of scenarios without freezing the UI.
- **Coverage Analytics**: View percentage distribution charts for Happy Path, Negative Tests, Smoke Tests, Validations, and RBAC scenarios.
- **Export**: One-click copy/export of massively stitched `.feature` files for Jira, Xray, or Zephyr integration.
