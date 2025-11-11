from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import tempfile
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from .safety import detect_red_flags, extract_symptoms
from .router import is_graph_intent, extract_city
from .rag.retriever import retrieve
from .models import ChatRequest, ChatResponse, Profile

from .graph import fallback as graph_fallback
from .graph.cypher import (
    get_red_flags as neo4j_get_red_flags,
    get_contraindications as neo4j_get_contraindications,
    get_providers_in_city as neo4j_get_providers_in_city,
    get_safe_actions_for_metabolic_conditions as neo4j_get_safe_actions,
)
from .graph.client import neo4j_client

load_dotenv()

app = FastAPI(title="Health Assistant API")


@app.on_event("shutdown")
async def _shutdown() -> None:
    if neo4j_client.driver:
        neo4j_client.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

_neo4j_available: Optional[bool] = None


def ensure_neo4j() -> bool:
    global _neo4j_available
    if _neo4j_available is None:
        try:
            _neo4j_available = neo4j_client.connect()
        except Exception:
            _neo4j_available = False
    return bool(_neo4j_available)


def graph_get_red_flags(symptoms: List[str]) -> List[Dict[str, Any]]:
    if ensure_neo4j():
        try:
            return neo4j_get_red_flags(symptoms)
        except Exception:
            pass
    return graph_fallback.get_red_flags(symptoms)


def graph_get_contraindications(user_conditions: List[str]) -> List[Dict[str, Any]]:
    if ensure_neo4j():
        try:
            return neo4j_get_contraindications(user_conditions)
        except Exception:
            pass
    return graph_fallback.get_contraindications(user_conditions)


def graph_get_providers(city: str) -> List[Dict[str, Any]]:
    if ensure_neo4j():
        try:
            return neo4j_get_providers_in_city(city)
        except Exception:
            pass
    return graph_fallback.get_providers_in_city(city)


def graph_get_safe_actions(user_conditions: List[str]) -> List[Dict[str, Any]]:
    if not user_conditions:
        return []
    
    if ensure_neo4j():
        try:
            return neo4j_get_safe_actions()
        except Exception:
            pass
    return graph_fallback.get_safe_actions(user_conditions)


def generate_answer(context: str, query: str, lang: str = "en") -> str:
    """Generate answer using OpenAI or fallback"""
    if not client:
        return "I'm here to help with health questions. Please note: I cannot provide medical diagnosis. For emergencies, call 108 or visit the nearest hospital."
    
    system_prompt = """You are a helpful health assistant. Provide clear, accurate health information based on the context provided.

IMPORTANT GUIDELINES:
- You are NOT a doctor and cannot diagnose
- Provide general health information only
- Always include a disclaimer about seeking professional medical care
- Be empathetic and supportive
- Keep answers concise (3-4 short paragraphs)
- Structure answers as:
  1. What it could mean (non-diagnostic)
  2. Safe self-care steps
  3. When to see a doctor
  4. Brief disclaimer

For Hindi responses, use simple, clear Hindi."""

    user_prompt = f"""Context from medical knowledge base:
{context}

User question: {query}

Language: {"Hindi" if lang == "hi" else "English"}

Provide a helpful, non-diagnostic response."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI error: {e}")
        return "I'm experiencing technical difficulties. For health emergencies, please call 108 or visit your nearest hospital."


@app.get("/health")
async def health_check():
    return {
        "ok": True,
        "openai_configured": client is not None,
        "services": {
            "rag": True,
            "graph": ensure_neo4j(),
            "graph_fallback": True,
            "safety": True
        }
    }


@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    """Convert speech to text using OpenAI Whisper"""
    if not client:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured")
    
    try:
        audio_bytes = await file.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        os.unlink(tmp_path)
        
        return {"text": transcription.text}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT error: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint with routing, safety detection, and RAG
    """
    text = request.text
    lang = request.lang
    profile: Profile = request.profile
    
    # Step 1: Safety detection
    safety_result = detect_red_flags(text, lang)
    
    # Step 2: Determine routing
    use_graph = is_graph_intent(text)
    
    facts = []
    citations = []
    answer = ""
    
    # Step 3: If red flags detected, always include graph red-flag query
    if safety_result["red_flag"]:
        symptoms = extract_symptoms(text)
        red_flag_results = graph_get_red_flags(symptoms)
        
        if red_flag_results:
            facts.append({
                "type": "red_flags",
                "data": red_flag_results
            })
    
    # Step 4: Execute appropriate query path
    if use_graph:
        # Graph-based query
        route = "graph"
        
        # Check for contraindications if user has conditions
        user_conditions = []
        if profile.diabetes:
            user_conditions.append("Diabetes")
        if profile.hypertension:
            user_conditions.append("Hypertension")

        condition_keywords = {
            "diabetes": "Diabetes",
            "hypertension": "Hypertension",
        }
        text_lower = text.lower()
        for keyword, label in condition_keywords.items():
            if keyword in text_lower and label not in user_conditions:
                user_conditions.append(label)
        
        if user_conditions:
            contras = graph_get_contraindications(user_conditions)
            if contras:
                facts.append({
                    "type": "contraindications",
                    "data": contras
                })
            
            safe_actions = graph_get_safe_actions(user_conditions)
            if safe_actions:
                facts.append({
                    "type": "safe_actions",
                    "data": safe_actions
                })
        
        # Check for provider query
        city = profile.city or extract_city(text)
        if city:
            providers = graph_get_providers(city)
            if providers:
                facts.append({
                    "type": "providers",
                    "data": providers
                })
        
        # Also get RAG context for LLM answer
        rag_results = retrieve(text, k=3)
        context = "\n\n".join([r["chunk"] for r in rag_results])
        citations = [
            {"source": r["source"], "id": r["id"], "topic": r.get("topic")}
            for r in rag_results
        ]
        
        # Generate answer that references the facts
        if facts:
            fact_summary = "\n\nRelevant facts from database:\n"
            for fact_group in facts:
                if fact_group["type"] == "red_flags":
                    fact_summary += "⚠️ Red flag conditions detected\n"
                elif fact_group["type"] == "contraindications":
                    fact_summary += f"⛔ Things to avoid: {', '.join([c['avoid'] for c in fact_group['data']])}\n"
                elif fact_group["type"] == "providers":
                    fact_summary += f"🏥 {len(fact_group['data'])} healthcare providers found\n"
            
            context = context + fact_summary
        
        answer = generate_answer(context, text, lang)
        
    else:
        # Vector RAG query
        route = "vector"
        
        # Retrieve relevant chunks
        rag_results = retrieve(text, k=4)
        
        if not rag_results:
            answer = "I don't have specific information about that. For health concerns, please consult a healthcare professional."
        else:
            context = "\n\n".join([r["chunk"] for r in rag_results])
            citations = [
                {"source": r["source"], "id": r["id"], "topic": r.get("topic")}
                for r in rag_results
            ]
            
            # Check profile for personalization
            personalized_conditions = []
            if profile.diabetes:
                personalized_conditions.append("diabetes")
            if profile.hypertension:
                personalized_conditions.append("hypertension")
            if personalized_conditions:
                context += (
                    "\n\nNote: User has "
                    + " and ".join(personalized_conditions)
                    + ". Provide relevant precautions."
                )
            
            answer = generate_answer(context, text, lang)
    
    # Add disclaimer if not emergency
    if not safety_result["red_flag"]:
        disclaimer = "\n\n⚠️ This is general information only, not medical advice. Consult a healthcare professional for proper diagnosis and treatment."
        if lang == "hi":
            disclaimer = "\n\n⚠️ यह केवल सामान्य जानकारी है, चिकित्सा सलाह नहीं। उचित निदान और उपचार के लिए स्वास्थ्य पेशेवर से परामर्श करें।"
        answer += disclaimer
    
    return ChatResponse(
        answer=answer,
        route=route,
        facts=facts,
        citations=citations,
        safety=safety_result
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)