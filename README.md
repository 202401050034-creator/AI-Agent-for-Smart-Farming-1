# 🌱 Krishi Mitra — AI Smart Farming Advisor Agent

> **Powered by IBM watsonx.ai + IBM Granite Models**  
> Personalised farming guidance for Indian farmers in 11 regional languages

![IBM watsonx.ai](https://img.shields.io/badge/IBM-watsonx.ai-0f62fe?style=flat-square&logo=ibm)
![IBM Granite](https://img.shields.io/badge/IBM-Granite%20AI-00b4d8?style=flat-square&logo=ibm)
![Python Flask](https://img.shields.io/badge/Flask-3.0-green?style=flat-square&logo=flask)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple?style=flat-square&logo=bootstrap)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **IBM Granite AI** | Powered by `ibm/granite-3-3-8b-instruct` via watsonx.ai |
| 📚 **RAG System** | Embedded agricultural knowledge base with ICAR/FAO data |
| 🌾 **Crop Advisor** | Season/soil/region-based crop recommendations |
| 🌍 **Soil Health** | NPK analysis, pH scoring, amendment advice |
| 🌦️ **Weather Advisory** | OpenWeather API + farming action plans |
| 💰 **Mandi Prices** | Live MSP 2024-25 dashboard with search |
| 📋 **Govt Schemes** | PM-KISAN, PMFBY, KCC, e-NAM, PMKSY guide |
| 👨‍🌾 **Farmer Profile** | Personalised region/soil/crop context |
| 📄 **PDF Reports** | Download full chat + farm advisory as PDF |
| 🎤 **Voice Input** | Web Speech API in regional languages |
| 🌙 **Dark Mode** | Full dark/light theme toggle |
| 📱 **Mobile Ready** | Responsive Bootstrap 5 design |
| 🌐 **11 Languages** | English, Hindi, Punjabi, Telugu, Tamil + more |
| 🔧 **AGENT_INSTRUCTIONS** | Fully customisable agent behaviour in `app.py` |

---

## 🏗️ Project Structure

```
smart-farming-agent/
│
├── app.py                  ← Flask backend + watsonx.ai + RAG + AGENT_INSTRUCTIONS
├── requirements.txt        ← Python dependencies
├── .env.example            ← Environment variable template
├── .env                    ← Your credentials (git-ignored)
│
├── templates/
│   ├── index.html          ← Main chat + advisor UI
│   └── dashboard.html      ← Farmer dashboard
│
├── static/
│   ├── css/
│   │   └── style.css       ← Custom CSS (dark mode, animations)
│   └── js/
│       ├── app.js          ← Chat, voice, PDF, profile, weather JS
│       └── dashboard.js    ← MSP chart + dashboard logic
│
└── README.md
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.9+ installed
- IBM Cloud account with watsonx.ai access
- (Optional) OpenWeather API key for live weather

### 2. Clone / Download

```bash
git clone https://github.com/yourname/krishi-mitra.git
cd krishi-mitra
```

### 3. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

```bash
# Copy the template
cp .env.example .env
```

Edit `.env` with your credentials:

```env
IBM_API_KEY=your_ibm_cloud_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-3-3-8b-instruct
SECRET_KEY=change-this-to-a-random-string
OPENWEATHER_API_KEY=your_openweather_api_key_here  # optional
```

### 6. Run the Application

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## 🔑 Getting IBM watsonx.ai Credentials

### Step 1 — IBM Cloud API Key
1. Go to [IBM Cloud Console](https://cloud.ibm.com)
2. Click **Manage → Access (IAM) → API Keys**
3. Click **Create an IBM Cloud API Key**
4. Copy and paste into your `.env` file as `IBM_API_KEY`

### Step 2 — watsonx.ai Project ID
1. Go to [IBM watsonx.ai](https://dataplatform.cloud.ibm.com/wx/home)
2. Create a new project or open existing
3. Go to **Manage → General → Project ID**
4. Copy and paste into your `.env` as `WATSONX_PROJECT_ID`

### Step 3 — Model ID
Default: `ibm/granite-3-3-8b-instruct`  
Other options:
- `ibm/granite-3-8b-instruct`
- `ibm/granite-13b-instruct-v2`
- `ibm/granite-3-2-8b-instruct`

---

## 🔧 Customising AGENT_INSTRUCTIONS

The `AGENT_INSTRUCTIONS` dictionary at the top of `app.py` lets you customise everything:

```python
AGENT_INSTRUCTIONS = {
    # Identity
    "agent_name": "Krishi Mitra",          # Change the agent's name
    "persona": "...",                       # Describe the agent's character

    # Tone
    "tone": "Friendly, practical...",       # How it communicates

    # Specialisation
    "specialisation": [...],                # Focus crop types / topics

    # Crop Logic
    "crop_recommendation_logic": "...",     # How to recommend crops

    # Safety
    "safety_rules": [...],                  # What the agent must NOT do

    # Languages
    "supported_languages": {...},           # Add/remove language support

    # Regional Advice
    "regional_recommendations": {
        "Punjab & Haryana": "...",          # State-specific farming tips
    },

    # Guidance rules for each topic...
    "fertilizer_guidance": "...",
    "pest_management": "...",
    "irrigation_advice": "...",
    "market_guidance": "...",
}
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main chat interface |
| `GET` | `/dashboard` | Farmer dashboard |
| `POST` | `/api/chat` | Send message, get AI response |
| `POST` | `/api/crop-recommendations` | Get crop suggestions |
| `POST` | `/api/weather` | Weather-based advisory |
| `POST` | `/api/soil-health` | Soil analysis + score |
| `GET` | `/api/mandi-prices` | MSP 2024-25 data |
| `GET/POST` | `/api/profile` | Farmer profile |
| `GET` | `/api/history` | Chat history |
| `POST` | `/api/history/clear` | Clear session history |
| `POST` | `/api/report/pdf` | Generate PDF report |
| `GET` | `/api/health` | Health check + model status |
| `GET` | `/api/languages` | Supported languages list |

### Chat API Example

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What crops should I grow in black soil this Kharif season?",
    "language": "en",
    "farmer_profile": {
      "state": "Maharashtra",
      "soil_type": "Black",
      "land_size": "5",
      "water_source": "Rainfed"
    }
  }'
```

---

## 📦 Production Deployment

### Option A — Gunicorn (Linux/macOS)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Option B — Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
```

```bash
docker build -t krishi-mitra .
docker run -p 5000:5000 --env-file .env krishi-mitra
```

### Option C — IBM Code Engine / Cloud Run

```bash
# Build and push
docker build -t us.icr.io/YOUR_NAMESPACE/krishi-mitra .
docker push us.icr.io/YOUR_NAMESPACE/krishi-mitra

# Deploy on IBM Code Engine
ibmcloud ce application create \
  --name krishi-mitra \
  --image us.icr.io/YOUR_NAMESPACE/krishi-mitra \
  --env-from-secret krishi-mitra-secrets \
  --port 5000
```

### Option D — Heroku

```bash
# Procfile
echo "web: gunicorn app:app" > Procfile

heroku create krishi-mitra-app
heroku config:set IBM_API_KEY=xxx WATSONX_PROJECT_ID=xxx SECRET_KEY=xxx
git push heroku main
```

---

## 🔒 Security Checklist

- [ ] Change `SECRET_KEY` in `.env` (use `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] Never commit `.env` to git (already in `.gitignore`)
- [ ] Use HTTPS in production (Let's Encrypt / Cloud Load Balancer)
- [ ] Set `FLASK_DEBUG=False` in production
- [ ] Consider rate limiting for `/api/chat` in production

---

## 🌱 RAG Knowledge Base

The embedded knowledge base in `app.py` covers:

- **Soil health** — ICAR pH/NPK standards, soil types, amendments
- **Crop recommendations** — Season-wise, soil-wise, region-wise
- **Fertilizer doses** — ICAR-recommended NPK for 15+ crops
- **Pest management** — IPM protocols, ETL levels, bio-alternatives
- **Irrigation** — Critical stages, water-saving tech, SRI
- **Weather farming** — Temperature effects, sowing windows, climate varieties
- **Government schemes** — PM-KISAN, PMFBY, KCC, e-NAM, PMKSY
- **Mandi prices** — MSP 2024-25 for all notified crops
- **Yield & profit** — Per-acre estimates for 10+ crops
- **Organic farming** — ZBNF, Jeevamrit, Bijamrit, organic certification

> **To extend the RAG:** Add new entries to the `RAG_KNOWLEDGE_BASE` dict in `app.py`.  
> **For production scale:** Replace with a vector database (Chroma, Milvus, Watson Discovery).

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/add-pest-database`)
3. Commit your changes (`git commit -m 'Add detailed pest database'`)
4. Push to the branch (`git push origin feature/add-pest-database`)
5. Open a Pull Request

---

## 📄 License

MIT License — Free to use, modify, and distribute.

---

## 🙏 Credits

- **IBM watsonx.ai** — Foundation model infrastructure
- **IBM Granite** — Open-source AI models
- **ICAR** — Agricultural research and recommendations
- **CACP** — MSP data source
- **IMD** — Weather data framework
- **Bootstrap** — UI framework

---

<p align="center">
  Made with ❤️ for Indian Farmers 🇮🇳 | Powered by IBM watsonx.ai
</p>
