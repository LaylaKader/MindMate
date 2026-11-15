from fastapi.testclient import TestClient
from app.main import app
from app.nlp import analyze
import pytest

client=TestClient(app)

def no_llm(monkeypatch):
    monkeypatch.delenv('LLM_API_KEY',raising=False)

def test_health():
    r=client.get('/health')
    assert r.status_code==200 and r.json()['status']=='ok'

def test_resources_have_sources():
    r=client.get('/api/resources')
    assert r.status_code==200 and len(r.json())>=5
    assert all(x['source_url'].startswith('https://') for x in r.json())

def test_chat_fallback_without_api_key(monkeypatch):
    no_llm(monkeypatch)
    r=client.post('/api/chat',json={'message':'I am stressed about exams and deadlines'})
    assert r.status_code==200 and r.json()['reply'] and r.json()['engine']=='retrieval+fallback'

def test_chat_greeting_has_personality(monkeypatch):
    no_llm(monkeypatch)
    r=client.post('/api/chat',json={'message':'Hey'})
    assert 'There you are' in r.json()['reply']

def test_listening_request_does_not_force_advice(monkeypatch):
    no_llm(monkeypatch)
    r=client.post('/api/chat',json={'message':'Can you talk and listen to me a bit'})
    reply=r.json()['reply']
    assert "I'm listening" in reply
    assert 'coping strategy' not in reply
    assert 'resource' not in reply.lower()

def test_loneliness_response_is_relevant(monkeypatch):
    no_llm(monkeypatch)
    r=client.post('/api/chat',json={'message':'I feel a bit lonely'})
    assert 'loneliness' in r.json()['reply'].lower() or 'lonely' in r.json()['reply'].lower()

def test_study_abroad_fear_gets_specific_response(monkeypatch):
    no_llm(monkeypatch)
    r=client.post('/api/chat',json={'message':"I feel like I won't be able to study abroad"})
    assert 'future' in r.json()['reply'].lower()
    assert 'study pressure' not in r.json()['reply'].lower()

def test_conversation_history_informs_followup(monkeypatch):
    no_llm(monkeypatch)
    r=client.post('/api/chat',json={
        'message':"I'm worried about funding",
        'history':[{'role':'user','content':"I don't think I'll be able to study abroad"}]
    })
    assert 'funding' in r.json()['reply'].lower()

def test_chat_history_accepted(monkeypatch):
    no_llm(monkeypatch)
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
