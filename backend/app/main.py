import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .assistant import respond

DATA=Path(__file__).with_name('knowledge.json')
RESOURCES=json.loads(DATA.read_text(encoding='utf-8'))
app=FastAPI(title='MindMate API',version='0.1.0',description='Non-clinical student wellbeing support prototype')
app.add_middleware(CORSMiddleware,allow_origins=['https://mindmate-nine-coral.vercel.app','https://mindmate-laylakader2k17-gmailcoms-projects.vercel.app','http://localhost:8080'],allow_credentials=False,allow_methods=['GET','POST'],allow_headers=['*'])
class ChatRequest(BaseModel):
    message: str = Field(min_length=1,max_length=2000)
@app.get('/health')
def health(): return {'status':'ok','service':'mindmate-api'}
@app.get('/api/resources')
def resources(): return RESOURCES
@app.post('/api/chat')
async def chat(body: ChatRequest): return await respond(body.message,RESOURCES)
