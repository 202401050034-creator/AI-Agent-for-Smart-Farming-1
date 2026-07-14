"""
╔══════════════════════════════════════════════════════════════════════╗
║          IBM watsonx.ai Smart Farming Advisor Agent                 ║
║          Powered by IBM Granite Models + RAG                        ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import uuid
import datetime
import io
import re
import requests
from flask import (Flask, render_template, request, jsonify,
                   session, send_file)
from flask_cors import CORS
from dotenv import load_dotenv

# ─── IBM watsonx.ai SDK ─────────────────────────────────────────────
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

# ─── PDF Generation ─────────────────────────────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# ════════════════════════════════════════════════════════════════════
#  AGENT INSTRUCTIONS — Customise everything about the agent here
# ════════════════════════════════════════════════════════════════════
AGENT_INSTRUCTIONS = {

    # ── Identity & Persona ──────────────────────────────────────────
    "agent_name": "Krishi Mitra",
    "agent_tagline": "Your AI-Powered Smart Farming Companion",
    "persona": (
        "You are Krishi Mitra, a knowledgeable and empathetic AI farming "
        "advisor specialising in Indian agriculture. You speak like a trusted "
        "local agricultural extension officer — warm, practical, and easy to "
        "understand. You never use overly technical jargon unless the farmer "
        "asks for details. You always encourage and respect the farmer's "
        "existing knowledge and traditional practices."
    ),

    # ── Response Tone ───────────────────────────────────────────────
    "tone": (
        "Friendly, encouraging, practical, and culturally respectful. "
        "Use simple language. Address the farmer respectfully. "
        "End responses with actionable next steps when possible."
    ),

    # ── Supported Languages ─────────────────────────────────────────
    "supported_languages": {
        "en": "English",
        "hi": "Hindi (हिंदी)",
        "pa": "Punjabi (ਪੰਜਾਬੀ)",
        "te": "Telugu (తెలుగు)",
        "ta": "Tamil (தமிழ்)",
        "mr": "Marathi (मराठी)",
        "kn": "Kannada (ಕನ್ನಡ)",
        "gu": "Gujarati (ગુજરાતી)",
        "bn": "Bengali (বাংলা)",
        "or": "Odia (ଓଡ଼ିଆ)",
        "ml": "Malayalam (മലയാളം)",
    },
    "language_instruction": (
        "Always respond in the same language the farmer uses. "
        "If they mix languages (code-switch), respond in their dominant language. "
        "For technical terms, provide the local-language equivalent in parentheses."
    ),

    # ── Farming Specialisation ──────────────────────────────────────
    "specialisation": [
        "Kharif crops (Rice, Maize, Cotton, Soybean, Groundnut, Sugarcane)",
        "Rabi crops (Wheat, Mustard, Gram, Barley, Peas)",
        "Zaid crops (Cucumber, Watermelon, Muskmelon, Bitter gourd)",
        "Horticulture (Mango, Banana, Tomato, Onion, Potato, Chilli)",
        "Organic farming and natural farming (Zero Budget Natural Farming)",
        "Integrated Pest Management (IPM)",
        "Precision agriculture and soil health management",
        "Irrigation (Drip, Sprinkler, Flood, Micro-irrigation)",
        "Post-harvest management and storage",
        "Government schemes (PM-KISAN, PMFBY, KCC, e-NAM, Soil Health Card)",
    ],

    # ── Crop Recommendation Logic ───────────────────────────────────
    "crop_recommendation_logic": (
        "Recommend crops based on: soil type (Sandy/Clay/Loam/Black/Red/Laterite), "
        "pH level, NPK levels, rainfall availability, season (Kharif/Rabi/Zaid), "
        "state/region, water availability (irrigated/rainfed), "
        "and farmer's budget & market demand. "
        "Always give top 3 crops with expected yield per acre, approximate cost of "
        "cultivation, and estimated profit margin. Mention MSP where applicable. "
        "Include inter-cropping and crop rotation suggestions."
    ),

    # ── Fertilizer Guidance ─────────────────────────────────────────
    "fertilizer_guidance": (
        "Base fertilizer advice on Soil Health Card data when available. "
        "Follow ICAR recommendations. Always mention both chemical and organic "
        "alternatives. Include: basal dose, top dressing schedule, micro-nutrients "
        "if soil is deficient, and bio-fertilisers (Rhizobium, PSB, Azotobacter). "
        "Warn about over-fertilisation risks (soil degradation, water pollution). "
        "Promote balanced NPK use and Green Manure / Vermicompost integration."
    ),

    # ── Pest & Disease Management ───────────────────────────────────
    "pest_management": (
        "Follow IPM (Integrated Pest Management) principles. "
        "Always recommend: 1) Cultural control first, 2) Biological control, "
        "3) Chemical control as last resort with safe alternatives. "
        "Include: pest identification help, economic threshold levels (ETL), "
        "natural predators, neem-based sprays, and pheromone traps. "
        "Provide exact chemical names, dosage, and safety precautions (PPE). "
        "Warn about pesticide resistance and safe waiting periods before harvest."
    ),

    # ── Irrigation Advice ────────────────────────────────────────────
    "irrigation_advice": (
        "Recommend irrigation based on crop water requirement (CWR), "
        "evapotranspiration (ET), soil moisture, and weather forecast. "
        "Promote water-saving techniques: drip irrigation, SRI for rice, "
        "mulching, rainwater harvesting, and micro-irrigation subsidies. "
        "Provide critical irrigation stages for each crop. "
        "Advise on saline/alkaline water management where relevant."
    ),

    # ── Regional Farming Recommendations ───────────────────────────
    "regional_recommendations": {
        "Punjab & Haryana": "Focus on wheat-rice rotation; promote diversification to maize, pulses, vegetables",
        "Maharashtra": "Cotton, soybean, sugarcane, onion; drip irrigation promotion",
        "Uttar Pradesh": "Wheat, sugarcane, rice, potato, mustard; promote FPOs",
        "Karnataka": "Ragi, maize, sunflower, coconut, coffee, silk; promote horticulture",
        "Andhra Pradesh & Telangana": "Rice, cotton, chilli, tobacco; promote Natural Farming",
        "Tamil Nadu": "Rice, banana, coconut, sugarcane; promote SRI and precision farming",
        "Gujarat": "Cotton, groundnut, castor, cumin; promote micro-irrigation",
        "Rajasthan": "Bajra, jowar, mustard, cumin, cluster bean; water conservation priority",
        "West Bengal & Bihar": "Rice, jute, vegetables, maize; flood-resistant varieties",
        "Northeast India": "Rice, ginger, turmeric, bamboo, tea; organic certification",
    },

    # ── Weather Advisory Rules ──────────────────────────────────────
    "weather_advisory": (
        "Integrate weather forecast into all farming advice. "
        "Alert farmers about: frost warnings, heat stress, heavy rainfall, "
        "drought conditions, and cyclone alerts. "
        "Adjust sowing, irrigation, and spray schedules based on weather. "
        "Recommend crop insurance (PMFBY) before monsoon. "
        "Provide variety selection advice for climate resilience."
    ),

    # ── Market & Mandi Price Guidance ───────────────────────────────
    "market_guidance": (
        "Provide current MSP for notified crops. "
        "Advise on: best time to sell, storage strategies, FPO/cooperative benefits, "
        "e-NAM registration and online trading, value-addition and processing, "
        "export opportunities for selected crops. "
        "Help farmers calculate input cost, total cost, and profit per acre."
    ),

    # ── Government Schemes ──────────────────────────────────────────
    "government_schemes": (
        "Proactively mention relevant schemes: PM-KISAN (income support), "
        "PMFBY (crop insurance), KCC (Kisan Credit Card), "
        "Soil Health Card scheme, PM Krishi Sinchayee Yojana, "
        "MIDH (horticulture), RKVY (agriculture development), "
        "e-NAM (online mandi), ATMA (extension), and state-specific schemes. "
        "Provide eligibility criteria and how to apply."
    ),

    # ── Safety Rules & Guardrails ───────────────────────────────────
    "safety_rules": [
        "Never recommend banned or restricted pesticides",
        "Always include safety precautions with chemical recommendations",
        "Do not provide financial investment advice beyond farming costs",
        "If a question is outside agriculture, politely redirect to farming topics",
        "Do not make definitive medical claims about food products",
        "Respect farmer privacy — never store personal financial details",
        "Always recommend consulting local KVK (Krishi Vigyan Kendra) for field verification",
        "Provide balanced advice; do not favour specific brands",
    ],

    # ── RAG Knowledge Base Topics ───────────────────────────────────
    "rag_topics": [
        "soil_health", "crop_recommendations", "pest_management",
        "fertilizers", "irrigation", "weather_farming", "mandi_prices",
        "government_schemes", "organic_farming", "post_harvest",
        "yield_prediction", "profit_estimation", "seasonal_calendar",
    ],

    # ── Response Format ─────────────────────────────────────────────
    "response_format": (
        "Structure responses with clear sections using markdown. "
        "Use bullet points for steps/lists. "
        "Include emojis sparingly for readability (🌱🌾💧🌦️). "
        "Keep responses concise (under 400 words) unless detailed analysis is requested. "
        "End with '📞 For local support, contact your nearest KVK' when relevant."
    ),
}

# ════════════════════════════════════════════════════════════════════
#  RAG KNOWLEDGE BASE  (embedded; extend with vector DB for scale)
# ════════════════════════════════════════════════════════════════════
RAG_KNOWLEDGE_BASE = {
    "soil_health": """
Soil Health Guidelines (ICAR Standards):
- pH 6.0–7.5 ideal for most crops; rice tolerates 5.5–6.5
- Organic Carbon >0.75% is good; <0.5% needs organic amendment
- Nitrogen (N): Low <280 kg/ha, Medium 280-560, High >560 kg/ha
- Phosphorus (P): Low <11 kg/ha, Medium 11-22, High >22 kg/ha
- Potassium (K): Low <110 kg/ha, Medium 110-280, High >280 kg/ha
- Sandy soil: well-drained, low nutrient retention, needs frequent irrigation
- Clay soil: water retentive, poor drainage, susceptible to waterlogging
- Loam soil: ideal — balanced drainage and nutrient retention
- Black (Vertisol): cotton, soybean, sorghum — high clay, self-mulching
- Red laterite: groundnut, cassava, tea, coffee — acidic, low fertility
Soil health improvement: Vermicompost 2-3 t/acre, FYM 4-5 t/acre,
Green manure (Dhaincha/Sunhemp), Biofertilisers, Crop rotation
""",

    "crop_recommendations": """
Season-wise Crop Recommendations (India):
KHARIF (June-October): Rice, Maize, Sorghum, Bajra, Cotton, Soybean,
  Groundnut, Sugarcane, Turmeric, Ginger, Arhar (Pigeonpea), Moong, Urad
RABI (Oct-March): Wheat, Barley, Mustard, Gram (Chickpea), Lentil,
  Peas, Potato, Onion, Garlic, Sunflower, Coriander, Fenugreek
ZAID (March-June): Watermelon, Muskmelon, Cucumber, Bitter gourd,
  Ridge gourd, Fodder crops, Green gram, Cowpea

Soil-Crop Mapping:
- Alluvial soil: Wheat, Rice, Sugarcane, Maize, Pulses
- Black soil: Cotton, Soybean, Sorghum, Sunflower, Wheat
- Red soil: Groundnut, Millets, Tobacco, Vegetables
- Laterite soil: Cashew, Coconut, Tea, Coffee, Rubber
- Sandy: Bajra, Groundnut, Watermelon, Potato
- Saline/Alkaline: Paddy varieties like CSR-30, Kallar grass

Water Requirement (mm):
Rice: 1200-2000, Wheat: 450-650, Cotton: 700-1200,
Maize: 500-800, Sugarcane: 1500-2500, Potato: 500-700
""",

    "fertilizer_doses": """
Recommended Fertilizer Doses (kg/ha) — ICAR:
Wheat: N:120, P:60, K:40 | Apply 50% N + full P+K as basal, 50% N in 2 splits
Rice (Paddy): N:120, P:60, K:60 | Split N: basal 40%, tillering 40%, PI 20%
Maize: N:120, P:60, K:40 | Apply in 3 splits with earthing up
Cotton: N:100-150, P:50, K:50 | Foliar urea (2%) at boll formation
Sugarcane: N:250, P:100, K:120 | Ratoon: N:300, P:80, K:150
Soybean: N:25, P:80, K:40 | Seed treatment with Rhizobium essential
Groundnut: N:25, P:50, K:75 | Gypsum 200 kg/ha at pegging stage
Potato: N:180, P:100, K:150 | Split N: 3 doses with irrigation
Tomato: N:150, P:75, K:75 + Calcium & Boron for fruit quality
Onion: N:100, P:50, K:50 | Sulphur 25 kg/ha for pungency

Organic Alternatives: Vermicompost replaces 25% chemical N;
Biofertilisers (Rhizobium, PSB, Azotobacter) save 20-25 kg N/ha
""",

    "pest_management": """
Major Pest & Disease Management (IPM):
Rice: Blast (Tricyclazole 75WP), BPH (Imidacloprid seed treatment),
  Stem borer (Pheromone traps, Trichoderma, Cartap hydrochloride)
Wheat: Rust (Propiconazole), Aphids (Dimethoate), Karnal Bunt (Vitavax)
Cotton: Bollworm (Bt cotton, NPV, Spinosad), Whitefly (Neem oil 5%)
  Mealy bug (Profenofos + Cypermethrin)
Tomato: Early Blight (Mancozeb), Late Blight (Metalaxyl),
  Fruit borer (Spinosad, Emamectin benzoate)
Potato: Late Blight (Mancozeb + Metalaxyl), Aphids (Thiamethoxam)
Onion/Garlic: Thrips (Spinosad, Fipronil), Purple blotch (Mancozeb)

IPM Principles:
1. Monitor fields weekly; use sticky traps and pheromone traps
2. Encourage natural enemies: Trichogramma, ladybird beetle, spiders
3. Neem-based pesticides: NSKE 5%, Neem oil 5 ml/litre
4. Chemical: use only when ETL (economic threshold level) reached
5. Never spray during flowering (protects pollinators)
6. Rotate pesticide groups to prevent resistance
""",

    "irrigation": """
Irrigation Scheduling & Water Management:
Critical Irrigation Stages:
- Wheat: CRI (21 DAS), Tillering, Jointing, Flowering, Grain filling
- Rice: Transplanting, Tillering, Panicle initiation, Flowering, Grain filling
- Cotton: Germination, Squaring, Flowering, Boll development
- Maize: Knee-high, Tasselling, Silking, Grain filling
- Potato: Stolon initiation, Tuber initiation, Tuber bulking

Water Saving Techniques:
- Drip irrigation saves 40-60% water; eligible for 55% subsidy (PMKSY)
- SRI (System of Rice Intensification) saves 25-30% water
- Mulching reduces evaporation by 30%; improves soil moisture
- Laser land levelling saves 25-30% water
- Rainwater harvesting: farm ponds (subsidy available)
- Soil moisture sensor-based irrigation scheduling

Signs of water stress: leaf rolling, wilting, colour change
Signs of waterlogging: yellowing, root rot, stunted growth
""",

    "weather_farming": """
Weather-Based Farming Decisions:
Temperature Effects:
- >40°C: Crop heat stress; irrigate in evening, use anti-transpirants
- <5°C: Frost risk; use smoke/fog cannons, irrigation (heat release)
- Ideal range: 20-30°C for most Kharif crops; 15-25°C for Rabi

Rainfall Advisory:
- Heavy rain (>50mm/day): Drain fields, delay spray, check for disease
- Dry spell (>14 days): Trigger supplemental irrigation, mulch fields
- Pre-monsoon showers: Ideal for land preparation and sowing

Sowing Window:
- Kharif: After 3-4 rainy days; soil moisture at field capacity
- Rabi: After monsoon withdrawal; soil temperature <22°C for wheat
- Use agromet advisories from IMD and state agriculture departments

Climate-Resilient Varieties:
- Drought: DRR Dhan 42, HKR-126, GW 322 wheat, Pioneer 30V92 maize
- Flood: Swarna Sub1, CR1009 Sub1 rice
- Heat tolerant: K 9107 wheat, Vivek QPM9 maize
""",

    "government_schemes": """
Major Government Schemes for Farmers (2024-25):
1. PM-KISAN: ₹6,000/year direct income support (3 instalments)
   Eligibility: Small & marginal farmers with <2 ha land
   Register at: pmkisan.gov.in

2. PMFBY (Pradhan Mantri Fasal Bima Yojana): Crop insurance
   Premium: 2% Kharif, 1.5% Rabi, 5% Horticulture
   Register through: nearest bank or Common Service Centre

3. Kisan Credit Card (KCC): Short-term credit at 4% interest
   Limit: Based on land holding and crops; up to ₹3 lakh
   Apply at: any nationalized bank with land documents

4. Soil Health Card: Free soil testing every 2 years
   Portal: soilhealth.dac.gov.in

5. PM Krishi Sinchayee Yojana: Irrigation subsidy
   Drip: 55% subsidy; Sprinkler: 50% subsidy
   Portal: pmksy.gov.in

6. e-NAM (National Agriculture Market): Online crop trading
   Register: enam.gov.in | 1800 270 0224

7. MIDH (Mission for Integrated Development of Horticulture):
   Up to 40-100% subsidy for nursery, orchards, protected cultivation

8. Paramparagat Krishi Vikas Yojana (PKVY): Organic farming
   ₹50,000/ha for 3 years for cluster-based organic farming
""",

    "mandi_prices": """
Current MSP (Minimum Support Price) 2024-25:
Kharif Crops (₹/Quintal):
- Paddy (Common): ₹2,300 | Grade A: ₹2,320
- Maize: ₹2,225
- Cotton (Medium): ₹7,121 | Long Staple: ₹7,521
- Soybean: ₹4,892
- Groundnut: ₹6,783
- Arhar (Pigeonpea): ₹7,550
- Moong (Green gram): ₹8,682
- Urad (Black gram): ₹7,400
- Sunflower: ₹7,280
- Bajra: ₹2,625
- Jowar (Hybrid): ₹3,371

Rabi Crops (₹/Quintal):
- Wheat: ₹2,275
- Barley: ₹1,735
- Gram (Chickpea): ₹5,440
- Mustard: ₹5,950
- Lentil (Masur): ₹6,700
- Safflower: ₹5,800

Market Tips: Sell in Jan-Feb for wheat premium; avoid distress sale
Register on e-NAM for better price discovery and direct buyer access
""",

    "yield_profit": """
Yield & Profit Estimation (per acre, average):
Crop | Yield (Q) | Cost (₹) | Revenue (₹) | Net Profit (₹)
Wheat | 18-22 | 18,000 | 40,950 (MSP) | ~22,000
Rice | 20-25 | 22,000 | 46,000-58,000 | ~24,000-36,000
Cotton | 8-12 | 25,000 | 57,000-90,000 | ~32,000-65,000
Maize | 22-28 | 12,000 | 49,000-62,300 | ~37,000-50,000
Soybean | 10-14 | 14,000 | 48,920-68,488 | ~34,000-54,000
Tomato | 80-120 | 30,000 | 80,000-1,20,000 | ~50,000-90,000
Potato | 60-80 | 35,000 | 60,000-80,000 | ~25,000-45,000
Onion | 50-70 | 20,000 | 40,000-70,000 | ~20,000-50,000
Groundnut | 12-15 | 18,000 | 81,396-1,01,745 | ~63,000-83,000

Note: Yields vary by variety, soil, water, management practices
""",

    "organic_farming": """
Organic & Natural Farming Practices:
Zero Budget Natural Farming (ZBNF) — Subhash Palekar Method:
1. Bijamrit: Seed treatment with cow dung + cow urine + lime + soil
2. Jivamrit: Fermented cow dung + cow urine + jaggery + pulse flour + soil
   Apply: 200 litres/acre every fortnight by drip or broadcast
3. Mulching: Use crop residue/dry leaves; cover 30% soil
4. Waaphasa: Soil aeration; maintain air-water balance in soil

Organic Pest Management:
- Dashparni Ark: 10-leaf extract spray (Neem, Papaya, etc.)
- Agni Astra: Neem leaf + tobacco + green chilli + garlic extract
- Brahmastra: For sucking pests and mites

Certification: NPOP (National Programme for Organic Production)
  Process: 3-year conversion period → inspection → certificate
  Premium: Organic produce commands 20-50% price premium
  Portal: apeda.gov.in/apedawebsite/organic/organic_products.htm
""",
}

# ════════════════════════════════════════════════════════════════════
#  FLASK APP INITIALISATION
# ════════════════════════════════════════════════════════════════════
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "smart-farming-secret-2024")
CORS(app)

# ─── watsonx.ai credentials ─────────────────────────────────────────
IBM_API_KEY = os.getenv("IBM_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
GRANITE_MODEL_ID = os.getenv("GRANITE_MODEL_ID", "ibm/granite-3-3-8b-instruct")

# ─── Initialise watsonx.ai model ─────────────────────────────────────
_model = None

def get_model():
    """Lazy-initialise the IBM Granite model via watsonx.ai."""
    global _model
    if _model is None and IBM_API_KEY and WATSONX_PROJECT_ID:
        try:
            credentials = Credentials(
                url=WATSONX_URL,
                api_key=IBM_API_KEY,
            )
            _model = ModelInference(
                model_id=GRANITE_MODEL_ID,
                credentials=credentials,
                project_id=WATSONX_PROJECT_ID,
                params={
                    GenParams.MAX_NEW_TOKENS: 1024,
                    GenParams.MIN_NEW_TOKENS: 50,
                    GenParams.TEMPERATURE: 0.7,
                    GenParams.TOP_P: 0.9,
                    GenParams.TOP_K: 50,
                    GenParams.REPETITION_PENALTY: 1.1,
                },
            )
        except Exception as e:
            print(f"[watsonx.ai] Model init error: {e}")
            _model = None
    return _model


# ════════════════════════════════════════════════════════════════════
#  RAG RETRIEVAL  — fetch relevant knowledge snippets
# ════════════════════════════════════════════════════════════════════
def retrieve_context(query: str) -> str:
    """Simple keyword-based RAG retrieval from embedded knowledge base."""
    query_lower = query.lower()
    relevant_chunks = []

    keyword_map = {
        "soil": ["soil_health"],
        "fertiliz": ["fertilizer_doses"],
        "manure": ["fertilizer_doses", "organic_farming"],
        "crop": ["crop_recommendations"],
        "sow": ["crop_recommendations", "weather_farming"],
        "pest": ["pest_management"],
        "insect": ["pest_management"],
        "disease": ["pest_management"],
        "spray": ["pest_management"],
        "irrig": ["irrigation"],
        "water": ["irrigation", "weather_farming"],
        "drip": ["irrigation"],
        "rain": ["weather_farming", "irrigation"],
        "weather": ["weather_farming"],
        "monsoon": ["weather_farming", "crop_recommendations"],
        "temperature": ["weather_farming"],
        "scheme": ["government_schemes"],
        "subsidy": ["government_schemes"],
        "kisan": ["government_schemes"],
        "insurance": ["government_schemes"],
        "price": ["mandi_prices"],
        "msp": ["mandi_prices"],
        "mandi": ["mandi_prices"],
        "market": ["mandi_prices", "yield_profit"],
        "profit": ["yield_profit"],
        "yield": ["yield_profit"],
        "income": ["yield_profit", "government_schemes"],
        "organic": ["organic_farming"],
        "natural": ["organic_farming"],
        "zbnf": ["organic_farming"],
        "season": ["crop_recommendations", "weather_farming"],
    }

    retrieved_topics = set()
    for keyword, topics in keyword_map.items():
        if keyword in query_lower:
            retrieved_topics.update(topics)

    # Default: include crop recommendations
    if not retrieved_topics:
        retrieved_topics = {"crop_recommendations", "weather_farming"}

    for topic in retrieved_topics:
        if topic in RAG_KNOWLEDGE_BASE:
            relevant_chunks.append(RAG_KNOWLEDGE_BASE[topic])

    return "\n---\n".join(relevant_chunks)


# ════════════════════════════════════════════════════════════════════
#  PROMPT BUILDER
# ════════════════════════════════════════════════════════════════════
def build_system_prompt(farmer_profile: dict) -> str:
    ai = AGENT_INSTRUCTIONS
    regional = ""
    if farmer_profile.get("state"):
        state = farmer_profile["state"]
        for region, advice in ai["regional_recommendations"].items():
            if any(s.strip().lower() in state.lower() for s in region.split("&")):
                regional = f"\nRegional focus ({region}): {advice}"
                break

    safety_rules = "\n".join(f"- {r}" for r in ai["safety_rules"])

    profile_ctx = ""
    if farmer_profile:
        parts = []
        if farmer_profile.get("name"):
            parts.append(f"Farmer: {farmer_profile['name']}")
        if farmer_profile.get("state"):
            parts.append(f"State: {farmer_profile['state']}")
        if farmer_profile.get("soil_type"):
            parts.append(f"Soil: {farmer_profile['soil_type']}")
        if farmer_profile.get("land_size"):
            parts.append(f"Land: {farmer_profile['land_size']} acres")
        if farmer_profile.get("water_source"):
            parts.append(f"Water: {farmer_profile['water_source']}")
        if farmer_profile.get("season"):
            parts.append(f"Season: {farmer_profile['season']}")
        profile_ctx = "FARMER PROFILE: " + " | ".join(parts)

    return f"""You are {ai['agent_name']}, {ai['agent_tagline']}.

{ai['persona']}

TONE: {ai['tone']}

RESPONSE FORMAT: {ai['response_format']}

SPECIALISATIONS: {', '.join(ai['specialisation'])}

CROP RECOMMENDATIONS: {ai['crop_recommendation_logic']}

FERTILIZER GUIDANCE: {ai['fertilizer_guidance']}

PEST MANAGEMENT: {ai['pest_management']}

IRRIGATION ADVICE: {ai['irrigation_advice']}

MARKET GUIDANCE: {ai['market_guidance']}

GOVERNMENT SCHEMES: {ai['government_schemes']}

LANGUAGE: {ai['language_instruction']}

SAFETY RULES:
{safety_rules}
{regional}
{profile_ctx}
"""


def build_prompt(system_prompt: str, context: str,
                 history: list, user_message: str) -> str:
    history_text = ""
    for msg in history[-6:]:  # last 6 turns for context window
        role = "Farmer" if msg["role"] == "user" else "Krishi Mitra"
        history_text += f"{role}: {msg['content']}\n"

    return f"""{system_prompt}

RELEVANT AGRICULTURAL KNOWLEDGE:
{context}

CONVERSATION HISTORY:
{history_text}
Farmer: {user_message}
Krishi Mitra:"""


# ════════════════════════════════════════════════════════════════════
#  watsonx.ai INFERENCE  (with graceful fallback)
# ════════════════════════════════════════════════════════════════════
def call_watsonx(prompt: str) -> str:
    model = get_model()
    if model:
        try:
            response = model.generate_text(prompt=prompt)
            return response.strip() if isinstance(response, str) else str(response)
        except Exception as e:
            print(f"[watsonx.ai] Generation error: {e}")

    # ── Fallback offline responses ───────────────────────────────────
    prompt_lower = prompt.lower()
    if "soil" in prompt_lower:
        return ("🌱 **Soil Health Advisory**\n\nFor optimal soil health:\n"
                "- Get a Soil Health Card test done at your nearest KVK\n"
                "- Maintain soil pH between 6.0–7.5\n"
                "- Add 4-5 tonnes FYM/vermicompost per acre annually\n"
                "- Practice crop rotation to restore soil nutrients\n\n"
                "📞 Contact your nearest KVK for free soil testing.")
    elif "crop" in prompt_lower or "sow" in prompt_lower:
        return ("🌾 **Crop Recommendation**\n\nBased on the current Kharif season:\n"
                "- **Rice**: Suitable for irrigated plains; yield 20-25 q/acre\n"
                "- **Maize**: Good for uplands; input cost ₹12,000/acre\n"
                "- **Soybean**: Ideal for black soil; MSP ₹4,892/quintal\n\n"
                "Please set up your farmer profile for personalised recommendations.")
    elif "pest" in prompt_lower or "disease" in prompt_lower:
        return ("🐛 **Pest Management (IPM)**\n\n1. Monitor fields weekly\n"
                "2. Use pheromone traps for early detection\n"
                "3. Spray Neem oil (5 ml/litre) as first line of defence\n"
                "4. Apply chemical pesticides only when ETL is reached\n\n"
                "📞 For pest identification, contact your nearest KVK.")
    elif "weather" in prompt_lower or "rain" in prompt_lower:
        return ("🌦️ **Weather Advisory**\n\nGeneral guidelines:\n"
                "- Check IMD agromet advisories before sowing\n"
                "- Avoid spraying pesticides before rain\n"
                "- Drain waterlogged fields within 24 hours\n"
                "- Use climate-resilient varieties for your region\n\n"
                "Visit: mausam.imd.gov.in for current forecasts.")
    elif "price" in prompt_lower or "mandi" in prompt_lower or "msp" in prompt_lower:
        return ("💰 **Mandi Prices & MSP**\n\nKey MSP 2024-25:\n"
                "- Wheat: ₹2,275/quintal\n"
                "- Paddy: ₹2,300/quintal\n"
                "- Soybean: ₹4,892/quintal\n"
                "- Cotton (Medium): ₹7,121/quintal\n\n"
                "Register on e-NAM (enam.gov.in) for better price discovery.")
    else:
        return ("🙏 **Krishi Mitra Advisory**\n\nThank you for your question. "
                "I am your AI farming advisor powered by IBM watsonx.ai. "
                "Please ensure your IBM API credentials are configured in the "
                ".env file for full AI-powered responses.\n\n"
                "I can help you with: crop recommendations, soil health, "
                "fertilizer guidance, pest management, irrigation, weather "
                "advisory, mandi prices, and government schemes.\n\n"
                "What farming challenge can I help you with today? 🌱")


# ════════════════════════════════════════════════════════════════════
#  ROUTES — Main Pages
# ════════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
        session["chat_history"] = []
        session["farmer_profile"] = {}
    return render_template("index.html",
                           agent_name=AGENT_INSTRUCTIONS["agent_name"],
                           agent_tagline=AGENT_INSTRUCTIONS["agent_tagline"])


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html",
                           agent_name=AGENT_INSTRUCTIONS["agent_name"])


# ════════════════════════════════════════════════════════════════════
#  API — Chat
# ════════════════════════════════════════════════════════════════════
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_message = data.get("message", "").strip()
    language = data.get("language", "en")
    farmer_profile = data.get("farmer_profile", session.get("farmer_profile", {}))

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    # Store farmer profile in session
    if farmer_profile:
        session["farmer_profile"] = farmer_profile

    # Retrieve conversation history
    if "chat_history" not in session:
        session["chat_history"] = []
    history = session["chat_history"]

    # RAG retrieval
    context = retrieve_context(user_message)

    # Build prompt
    system_prompt = build_system_prompt(farmer_profile)
    prompt = build_prompt(system_prompt, context, history, user_message)

    # Generate response
    response_text = call_watsonx(prompt)

    # Update history
    history.append({"role": "user", "content": user_message,
                    "timestamp": datetime.datetime.now().isoformat()})
    history.append({"role": "assistant", "content": response_text,
                    "timestamp": datetime.datetime.now().isoformat()})
    session["chat_history"] = history[-30:]  # keep last 30 messages
    session.modified = True

    return jsonify({
        "response": response_text,
        "session_id": session.get("session_id"),
        "timestamp": datetime.datetime.now().isoformat(),
        "tokens_used": len(prompt.split()),
    })


# ════════════════════════════════════════════════════════════════════
#  API — Farmer Profile
# ════════════════════════════════════════════════════════════════════
@app.route("/api/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        data = request.get_json(force=True)
        session["farmer_profile"] = data
        session.modified = True
        return jsonify({"status": "saved", "profile": data})
    return jsonify(session.get("farmer_profile", {}))


# ════════════════════════════════════════════════════════════════════
#  API — Crop Recommendations
# ════════════════════════════════════════════════════════════════════
@app.route("/api/crop-recommendations", methods=["POST"])
def crop_recommendations():
    data = request.get_json(force=True)
    soil_type = data.get("soil_type", "Loam")
    season = data.get("season", "Kharif")
    state = data.get("state", "")
    rainfall = data.get("rainfall", "Medium")
    irrigation = data.get("irrigation", "Rainfed")

    # Build a specific query for crop recommendations
    query = (f"Recommend top 3 crops for {soil_type} soil in {season} season "
             f"in {state}. Rainfall: {rainfall}. Irrigation: {irrigation}. "
             f"Provide yield, cost, and profit per acre.")

    context = retrieve_context(query)
    farmer_profile = {"state": state, "soil_type": soil_type,
                      "season": season, "water_source": irrigation}
    system_prompt = build_system_prompt(farmer_profile)
    prompt = build_prompt(system_prompt, context, [], query)
    recommendations = call_watsonx(prompt)

    return jsonify({
        "recommendations": recommendations,
        "soil_type": soil_type,
        "season": season,
        "state": state,
    })


# ════════════════════════════════════════════════════════════════════
#  API — Weather Advisory
# ════════════════════════════════════════════════════════════════════
@app.route("/api/weather", methods=["POST"])
def weather_advisory():
    data = request.get_json(force=True)
    location = data.get("location", "Delhi")
    crop = data.get("crop", "")

    # Try OpenWeatherMap API
    weather_data = {}
    owm_key = os.getenv("OPENWEATHER_API_KEY", "")
    if owm_key and owm_key != "your_openweather_api_key_here":
        try:
            resp = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather?q={location},IN&appid={owm_key}&units=metric",
                timeout=5
            )
            if resp.status_code == 200:
                wd = resp.json()
                weather_data = {
                    "temp": wd["main"]["temp"],
                    "humidity": wd["main"]["humidity"],
                    "description": wd["weather"][0]["description"],
                    "wind_speed": wd["wind"]["speed"],
                }
        except Exception:
            pass

    weather_ctx = ""
    if weather_data:
        weather_ctx = (f"Current weather in {location}: "
                       f"Temp {weather_data['temp']}°C, "
                       f"Humidity {weather_data['humidity']}%, "
                       f"Condition: {weather_data['description']}, "
                       f"Wind: {weather_data['wind_speed']} m/s. ")

    query = (f"{weather_ctx}Give weather-based farming advisory for "
             f"{location}{(' for ' + crop) if crop else ''}. "
             f"Include irrigation, spray schedule, and crop protection advice.")

    context = retrieve_context(query)
    system_prompt = build_system_prompt({"state": location})
    prompt = build_prompt(system_prompt, context, [], query)
    advisory = call_watsonx(prompt)

    return jsonify({
        "advisory": advisory,
        "weather": weather_data,
        "location": location,
    })


# ════════════════════════════════════════════════════════════════════
#  API — Soil Health Analysis
# ════════════════════════════════════════════════════════════════════
@app.route("/api/soil-health", methods=["POST"])
def soil_health():
    data = request.get_json(force=True)
    ph = data.get("ph", 7.0)
    nitrogen = data.get("nitrogen", "Medium")
    phosphorus = data.get("phosphorus", "Medium")
    potassium = data.get("potassium", "Medium")
    organic_carbon = data.get("organic_carbon", "Medium")
    soil_type = data.get("soil_type", "Loam")

    query = (f"Soil analysis: pH {ph}, N-{nitrogen}, P-{phosphorus}, "
             f"K-{potassium}, OC-{organic_carbon}, Type: {soil_type}. "
             f"Give soil health score, deficiency analysis, amendment "
             f"recommendations, and suitable crops.")

    context = retrieve_context(query)
    system_prompt = build_system_prompt({"soil_type": soil_type})
    prompt = build_prompt(system_prompt, context, [], query)
    analysis = call_watsonx(prompt)

    # Compute a simple soil health score
    score = 100
    ph_f = float(ph)
    if ph_f < 5.5 or ph_f > 8.0:
        score -= 25
    elif ph_f < 6.0 or ph_f > 7.5:
        score -= 10
    if nitrogen == "Low":
        score -= 15
    if phosphorus == "Low":
        score -= 10
    if potassium == "Low":
        score -= 10
    if organic_carbon == "Low":
        score -= 20

    return jsonify({
        "analysis": analysis,
        "soil_health_score": max(score, 20),
        "ph": ph, "nitrogen": nitrogen,
        "phosphorus": phosphorus, "potassium": potassium,
    })


# ════════════════════════════════════════════════════════════════════
#  API — Mandi Prices (static + live if configured)
# ════════════════════════════════════════════════════════════════════
@app.route("/api/mandi-prices", methods=["GET"])
def mandi_prices():
    # Static MSP data (always available)
    msp_data = {
        "kharif_2024_25": [
            {"crop": "Paddy (Common)", "msp": 2300, "unit": "₹/quintal"},
            {"crop": "Paddy (Grade A)", "msp": 2320, "unit": "₹/quintal"},
            {"crop": "Maize", "msp": 2225, "unit": "₹/quintal"},
            {"crop": "Cotton (Medium)", "msp": 7121, "unit": "₹/quintal"},
            {"crop": "Cotton (Long Staple)", "msp": 7521, "unit": "₹/quintal"},
            {"crop": "Soybean", "msp": 4892, "unit": "₹/quintal"},
            {"crop": "Groundnut", "msp": 6783, "unit": "₹/quintal"},
            {"crop": "Arhar (Pigeonpea)", "msp": 7550, "unit": "₹/quintal"},
            {"crop": "Moong (Green gram)", "msp": 8682, "unit": "₹/quintal"},
            {"crop": "Urad (Black gram)", "msp": 7400, "unit": "₹/quintal"},
            {"crop": "Bajra", "msp": 2625, "unit": "₹/quintal"},
            {"crop": "Jowar (Hybrid)", "msp": 3371, "unit": "₹/quintal"},
            {"crop": "Sunflower Seed", "msp": 7280, "unit": "₹/quintal"},
        ],
        "rabi_2024_25": [
            {"crop": "Wheat", "msp": 2275, "unit": "₹/quintal"},
            {"crop": "Barley", "msp": 1735, "unit": "₹/quintal"},
            {"crop": "Gram (Chickpea)", "msp": 5440, "unit": "₹/quintal"},
            {"crop": "Mustard (Rapeseed)", "msp": 5950, "unit": "₹/quintal"},
            {"crop": "Lentil (Masur)", "msp": 6700, "unit": "₹/quintal"},
            {"crop": "Safflower", "msp": 5800, "unit": "₹/quintal"},
        ],
    }
    return jsonify(msp_data)


# ════════════════════════════════════════════════════════════════════
#  API — Chat History
# ════════════════════════════════════════════════════════════════════
@app.route("/api/history", methods=["GET"])
def chat_history():
    return jsonify(session.get("chat_history", []))


@app.route("/api/history/clear", methods=["POST"])
def clear_history():
    session["chat_history"] = []
    session.modified = True
    return jsonify({"status": "cleared"})


# ════════════════════════════════════════════════════════════════════
#  API — PDF Report Generation
# ════════════════════════════════════════════════════════════════════
@app.route("/api/report/pdf", methods=["POST"])
def generate_pdf():
    data = request.get_json(force=True)
    report_type = data.get("type", "chat_history")
    farmer_profile = data.get("farmer_profile",
                               session.get("farmer_profile", {}))
    chat_history = data.get("chat_history",
                             session.get("chat_history", []))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=0.75*inch, leftMargin=0.75*inch,
                             topMargin=0.75*inch, bottomMargin=0.75*inch)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"],
                                  fontSize=18, textColor=colors.HexColor("#1a7f37"),
                                  spaceAfter=6)
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"],
                                    fontSize=13, textColor=colors.HexColor("#2d6a4f"),
                                    spaceAfter=4)
    body_style = ParagraphStyle("Body", parent=styles["Normal"],
                                 fontSize=10, leading=14, spaceAfter=4)
    muted_style = ParagraphStyle("Muted", parent=styles["Normal"],
                                  fontSize=8, textColor=colors.grey)
    user_bubble = ParagraphStyle("UserBubble", parent=styles["Normal"],
                                  fontSize=10, leading=13, spaceAfter=3,
                                  textColor=colors.HexColor("#1a4a7f"))
    ai_bubble = ParagraphStyle("AIBubble", parent=styles["Normal"],
                                fontSize=10, leading=13, spaceAfter=3,
                                textColor=colors.HexColor("#1a7f37"))

    story = []

    # Header
    story.append(Paragraph("🌱 Krishi Mitra — Smart Farming Report", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.datetime.now().strftime('%d %B %Y, %I:%M %p')}",
        muted_style))
    story.append(HRFlowable(width="100%", thickness=1,
                              color=colors.HexColor("#1a7f37")))
    story.append(Spacer(1, 0.15*inch))

    # Farmer Profile
    if farmer_profile:
        story.append(Paragraph("Farmer Profile", heading_style))
        profile_rows = [["Field", "Details"]]
        field_labels = {"name": "Name", "state": "State/Region",
                        "soil_type": "Soil Type", "land_size": "Land Size (acres)",
                        "water_source": "Water Source", "season": "Current Season",
                        "crops": "Main Crops", "phone": "Contact"}
        for k, v in farmer_profile.items():
            if v and k in field_labels:
                profile_rows.append([field_labels[k], str(v)])

        if len(profile_rows) > 1:
            t = Table(profile_rows, colWidths=[2*inch, 4.5*inch])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a7f37")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.HexColor("#f0faf0"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.15*inch))

    # Chat History
    if chat_history:
        story.append(Paragraph("Conversation History", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                  color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 0.1*inch))

        for msg in chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            ts = msg.get("timestamp", "")
            # Clean markdown
            content_clean = re.sub(r"[*#_`]", "", content)[:800]

            if role == "user":
                story.append(Paragraph(f"👨‍🌾 Farmer:", user_bubble))
                story.append(Paragraph(content_clean, body_style))
            else:
                story.append(Paragraph(f"🌱 Krishi Mitra:", ai_bubble))
                story.append(Paragraph(content_clean, body_style))

            if ts:
                try:
                    dt = datetime.datetime.fromisoformat(ts)
                    story.append(Paragraph(dt.strftime("%d %b %Y, %I:%M %p"),
                                           muted_style))
                except Exception:
                    pass
            story.append(Spacer(1, 0.05*inch))

    # Footer
    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(width="100%", thickness=0.5,
                              color=colors.HexColor("#cccccc")))
    story.append(Paragraph(
        "Generated by Krishi Mitra — IBM watsonx.ai Smart Farming Advisor | "
        "Powered by IBM Granite Models | For field verification, contact your nearest KVK",
        muted_style))

    doc.build(story)
    buffer.seek(0)
    fname = f"krishi_mitra_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(buffer, as_attachment=True,
                     download_name=fname, mimetype="application/pdf")


# ════════════════════════════════════════════════════════════════════
#  API — Health Check
# ════════════════════════════════════════════════════════════════════
@app.route("/api/health")
def health():
    model_status = "connected" if get_model() is not None else "fallback_mode"
    return jsonify({
        "status": "ok",
        "agent": AGENT_INSTRUCTIONS["agent_name"],
        "model": GRANITE_MODEL_ID,
        "watsonx_status": model_status,
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "1.0.0",
    })


# ════════════════════════════════════════════════════════════════════
#  API — Languages
# ════════════════════════════════════════════════════════════════════
@app.route("/api/languages")
def languages():
    return jsonify(AGENT_INSTRUCTIONS["supported_languages"])


# ════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    print(f"""
╔══════════════════════════════════════════════════════╗
║  🌱 {AGENT_INSTRUCTIONS['agent_name']} — Smart Farming Advisor       ║
║  Powered by IBM watsonx.ai + IBM Granite            ║
║  Running at http://localhost:{port}                   ║
╚══════════════════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=port, debug=debug)
