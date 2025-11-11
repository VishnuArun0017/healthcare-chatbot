from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import tempfile
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Health Assistant API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ChatRequest(BaseModel):
    text: str
    lang: str = "en"
    profile: dict = {}


class ChatResponse(BaseModel):
    answer: str
    route: str
    facts: list = []
    citations: list = []
    safety: dict = {}


@app.get("/health")
async def health_check():
    return {"ok": True}


@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    """Convert speech to text using OpenAI Whisper"""
    try:
        # Read the uploaded audio file
        audio_bytes = await file.read()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        # Transcribe using Whisper
        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return {"text": transcription.text}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT error: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint - currently returns stub response"""
    return ChatResponse(
        answer="Working on your query...",
        route="vector",
        facts=[],
        citations=[],
        safety={"red_flag": False, "matched": []}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)