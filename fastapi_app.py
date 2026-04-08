from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import asyncio
from datetime import datetime, timedelta
import json
import re
from nltk_nlp import detect_intent, get_general_response

app = FastAPI(
    title="DEO Chatbot API",
    description="High-performance academic chatbot",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for better validation
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    intent: str
    confidence: float
    entities: Dict[str, Any] = {}
    timestamp: datetime

class StudentQuery(BaseModel):
    roll_number: str
    include_details: bool = True

class SectionQuery(BaseModel):
    section: str
    batch: Optional[str] = None
    semester: Optional[str] = None

# In-memory cache (free alternative to Redis)
cache = {}
CACHE_TTL = 300  # 5 minutes

def get_cache_key(key: str) -> Any:
    """Get value from cache"""
    if key in cache:
        data, timestamp = cache[key]
        if datetime.now().timestamp() - timestamp < CACHE_TTL:
            return data
        else:
            del cache[key]
    return None

def set_cache_key(key: str, value: Any) -> None:
    """Set value in cache"""
    cache[key] = (value, datetime.now().timestamp())

# Enhanced NLP processing
async def process_message(message: str, user_id: str = None) -> Dict:
    """Process user message with enhanced NLP"""
    # Check cache first
    cache_key = f"msg_{hash(message)}"
    cached_result = get_cache_key(cache_key)
    if cached_result:
        return cached_result
    
    # Process with NLP
    intent, sem, batch, roll, section, subject, qualifier = detect_intent(message)
    
    # Extract entities
    entities = {}
    if roll:
        entities['roll_number'] = roll
    if section:
        entities['section'] = section
    if subject:
        entities['subject'] = subject
    if sem:
        entities['semester'] = sem
    if batch:
        entities['batch'] = batch
    if qualifier:
        entities['qualifier'] = qualifier
    
    # Generate response
    if intent == 'general':
        response = get_general_response(message)
    else:
        response = f"Processing {intent} request with entities: {list(entities.keys())}"
    
    result = {
        'response': response,
        'intent': intent,
        'confidence': 0.85,  # Will be calculated from model
        'entities': entities,
        'timestamp': datetime.now()
    }
    
    # Cache the result
    set_cache_key(cache_key, result)
    
    return result

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "DEO Chatbot API v2.0",
        "status": "running",
        "features": [
            "FastAPI backend",
            "Enhanced NLP",
            "In-memory caching",
            "Automatic validation"
        ]
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        result = await process_message(request.message, request.user_id)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )

@app.post("/analyze-intent")
async def analyze_intent(request: ChatRequest):
    """Analyze intent only"""
    try:
        intent, sem, batch, roll, section, subject, qualifier = detect_intent(request.message)
        return {
            "intent": intent,
            "entities": {
                "semester": sem,
                "batch": batch,
                "roll_number": roll,
                "section": section,
                "subject": subject,
                "qualifier": qualifier
            },
            "confidence": 0.85
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing intent: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "cache_size": len(cache),
        "version": "2.0.0"
    }

@app.get("/stats")
async def get_stats():
    """Get API statistics"""
    return {
        "cache_entries": len(cache),
        "uptime": "running",
        "performance": "high",
        "features": {
            "async_processing": True,
            "caching": True,
            "validation": True,
            "auto_docs": True
        }
    }

# Automatic documentation at /docs
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
