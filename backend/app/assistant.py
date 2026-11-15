import os
import re
import httpx
from .nlp import analyze

CRISIS_REPLY = ("I'm really sorry things feel this heavy. I can't assess your safety or provide crisis care. If you may act on these thoughts or cannot stay safe, contact local emergency services or go to the nearest emergency department now. Please tell a trusted person and ask them to stay with you. This chat is not monitored and cannot contact help for you.")

def retrieve(message: str, resources: list[dict], limit: int=2):
    tokens=set(re.findall(r"[a-z']+", message.lower()))
    scored=[]
    for item in resources:
        text=(item.get('title','')+' '+item.get('topic','')+' '+item.get('summary','')).lower()
        score=len(tokens & set(re.findall(r"[a-z']+", text)))
        if score: scored.append((score,item))
    return [x[1] for x in sorted(scored,key=lambda x:x[0],reverse=True)[:limit]]

def fallback(message: str, analysis: dict, resources: list[dict], history: list[dict]) -> str:
    text=message.strip().lower()
    previous_user=next((m.get("content","").lower() for m in reversed(history) if m.get("role")=="user"), "")
    previous_assistant=next((m.get("content","").lower() for m in reversed(history) if m.get("role")=="assistant"), "")
    if re.fullmatch(r"(hi|hey|hello|hiya|heyy|good morning|good evening|good afternoon)[!. ]*", text):
        return "Hey. There you are. 🙂 What's the state of things today—quiet, chaotic, or somewhere annoyingly in between?"
    if any(p in text for p in ("can you listen","just listen","talk and listen","can we talk","stay with me","hear me out","i just want to talk")):
        return "I can do that. No fixing, no unsolicited life lecture. I'm listening—start wherever you like, even if the story comes out a little messy."
    if any(p in text for p in ("thank you","thanks","that helps")):
        return "Anytime. And for the record, you don't have to turn every feeling into a lesson or a plan. We can just let it be what it is."
    if any(p in text for p in ("study abroad","abroad","overseas","international student")) and any(p in text for p in ("won't","will not","can't","cannot","never","not be able","give up","impossible")):
        return "That one sounds like it really matters to you. And I hear the fear underneath it—not just worrying about an application, but wondering whether the future you've been working toward might slip away. That's a heavy thought to sit with. What happened today that made it feel so out of reach?"
    if "study abroad" in previous_user or "abroad" in previous_user:
        if any(p in text for p in ("money","funding","scholarship","tuition","cost","financial")):
            return "So the money side is making the whole dream feel fragile. That's a real obstacle, not a silly worry. Tell me what part is pressing on you most—the funding itself, or the fear that you won't find a university willing to support you?"
        if any(p in text for p in ("professor","supervisor","reply","email","university","application","admission","deadline","cgpa","ielts","rejected")):
            return "Ah. So this isn't an abstract fear; something in the application process has brought it right to the surface. Tell me what happened. I'll stay with the actual problem instead of throwing a motivational poster at you."
    if any(p in text for p in ("i feel lonely","i'm lonely","im lonely","i feel alone","nobody","no one")):
        return "Loneliness has a way of making a room feel much bigger than it is. I'm here with you in this conversation. Is it that you miss a particular person, or more that you don't feel properly understood by the people around you?"
    if previous_assistant and any(p in text for p in ("same thing","as i said","i told you","that's what i mean")):
        return "You're right—let me not make you repeat yourself. Keep going from where you left off. I'm following."
    topic=analysis['topics'][0] if analysis['topics'] else None
    if topic=='academic_pressure':
        return "It sounds like this matters a lot to you, which can make every setback feel like a verdict on your future. I don't think one difficult moment gets to decide the whole story. What part is frightening you most right now?"
    if topic=='anxiety':
        return "Your mind sounds like it's running several steps ahead of you. We don't have to chase every thought at once. What is the one thought that keeps coming back?"
    if topic=='low_mood':
        return "That sounds lonely, and I'm not going to pretend a quick tip fixes it. You can tell me more. What does the loneliness feel like for you tonight?"
    if topic=='burnout':
        return "You've been running on a low battery for a while, haven't you? I'm not going to tell you to simply be more productive. What's been draining you the most?"
    if topic=='relationships':
        return "That sounds complicated in the way people things usually are. I'm not going to pick a side without understanding it. What happened?"
    if topic=='sleep':
        return "Being tired and unable to rest is a particularly unfair combination. Is it your thoughts keeping you awake, or does sleep just refuse to show up?"
    return "I'm here. You don't need to make this sound neat or reasonable before you tell me. What's on your mind?"

async def llm_reply(message: str, resources: list[dict], history: list[dict]):
    key=os.getenv('LLM_API_KEY')
    if not key: return None
    base=os.getenv('LLM_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.getenv('LLM_MODEL','gpt-4o-mini')
    context="\n".join(f"- {r['title']}: {r['summary']} (source: {r['source_url']})" for r in resources)
    system=("You are MindMate, a conversational student wellbeing companion. Your personality is calm, self-assured, perceptive, gently protective, a little witty and occasionally dry—but never arrogant, possessive, flirtatious, theatrical, or patronising. Think composed confidence and understated warmth, not a therapist's script. Speak like a real person: use contractions, varied sentence length, natural reactions, and occasional light humour when the moment allows. Do not overuse emojis. Avoid canned openings such as 'That sounds like a lot to carry', 'I'm glad you reached out', or 'Thanks for trusting me'. Never begin every reply by restating the user's emotion. Respond to specific details and emotional meaning. Remember and refer naturally to earlier turns. If they ask you to listen, listen: no advice, exercises, resources, or follow-up interrogation; invite them to continue simply. Ask at most one question, and sometimes ask none. Don't turn every message into a question. Don't append resources or coping tips unless clearly relevant or requested. If someone fears they cannot study abroad, engage with that dream and the concrete fear rather than generic study-stress advice. Validate without promising outcomes. Never diagnose, prescribe, claim to be human, encourage emotional dependency, or discourage real-world support. You are AI support, not therapy. For crisis content, advise immediate contact with local emergency services or nearest emergency department and a trusted person; never imply you can monitor or dispatch help.\nEDUCATIONAL CONTEXT (use only when directly relevant):\n"+context)
    messages=[{'role':'system','content':system}]
    for item in history[-8:]:
        if item.get('role') in ('user','assistant') and isinstance(item.get('content'),str):
            messages.append({'role':item['role'],'content':item['content'][:2000]})
    messages.append({'role':'user','content':message})
    async with httpx.AsyncClient(timeout=25) as client:
        r=await client.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}'},json={'model':model,'temperature':0.85,'max_tokens':260,'messages':messages})
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content'].strip()

async def respond(message: str, resources: list[dict], history: list[dict] | None=None):
    history=history or []
    analysis=analyze(message)
    if analysis['crisis_flag']:
        return {'reply':CRISIS_REPLY,'resources':[],'safety_route':'urgent','nlp':analysis,'engine':'safety'}
    matches=retrieve(message,resources)
    try: reply=await llm_reply(message,matches,history)
    except Exception: reply=None
    engine='llm+retrieval' if reply else 'retrieval+fallback'
    if not reply: reply=fallback(message,analysis,matches,history)
    return {'reply':reply,'resources':matches,'safety_route':'standard','nlp':analysis,'engine':engine}
