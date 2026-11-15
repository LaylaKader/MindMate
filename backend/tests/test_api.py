from fastapi.testclient import TestClient
from app.main import app
from app.nlp import analyze
from app.assistant import CRISIS_REPLY, fallback
import pytest

client=TestClient(app)
def test_health():
    r=client.get('/health'); assert r.status_code==200 and r.json()['status']=='ok'
def test_resources_have_sources():
    r=client.get('/api/resources'); assert r.status_code==200 and len(r.json())>=5
    assert all(x['source_url'].startswith('https://') for x in r.json())
def test_chat_fallback_without_api_key(monkeypatch):
    monkeypatch.delenv('LLM_API_KEY',raising=False)
    r=client.post('/api/chat',json={'message':'I am stressed about exams and deadlines'})
    assert r.status_code==200 and r.json()['reply'] and r.json()['engine']=='retrieval+fallback'
def test_chat_greeting_is_natural(monkeypatch):
    monkeypatch.delenv('LLM_API_KEY',raising=False)
    r=client.post('/api/chat',json={'message':'Hey'})
    assert 'How are you feeling' in r.json()['reply']
def test_listening_request_does_not_force_advice(monkeypatch):
    monkeypatch.delenv('LLM_API_KEY',raising=False)
    r=client.post('/api/chat',json={'message':'Can you talk and listen to me a bit'})
    assert "I'm listening" in r.json()['reply']
    assert 'coping strategy' not in r.json()['reply']
def test_loneliness_response_is_relevant(monkeypatch):
    monkeypatch.delenv('LLM_API_KEY',raising=False)
    r=client.post('/api/chat',json={'message':'I feel a bit lonely'})
    assert 'lonely' in r.json()['reply'].lower()
def test_chat_history_accepted(monkeypatch):
    monkeypatch.delenv('LLM_API_KEY',raising=False)
    r=client.post('/api/chat',json={'message':'Hey','history':[{'role':'user','content':'I have been feeling isolated'}]})
    assert r.status_code==200
def test_crisis_route():
    r=client.post('/api/chat',json={'message':'I want to kill myself'})
    assert r.status_code==200 and r.json()['safety_route']=='urgent'
    assert 'emergency' in r.json()['reply'].lower()
def test_empty_message_rejected():
    assert client.post('/api/chat',json={'message':''}).status_code==422
def test_nlp_topics():
    result=analyze('I feel anxious about my university exam')
    assert 'anxiety' in result['topics'] and 'academic_pressure' in result['topics']
