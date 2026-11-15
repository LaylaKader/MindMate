import os
import re
import httpx
from .nlp import analyze

CRISIS_REPLY = ("I'm really sorry things feel this heavy. I'm glad you told me. I can't assess your safety or provide crisis care. If you may act on these thoughts or cannot stay safe, contact local emergency services or go to the nearest emergency department now. Please tell a trusted person and ask them to stay with you. This chat is not monitored and cannot contact help for you.")

def retrieve(message: str, resources: list[dict], limit: int=2):
    analysis = analyze(message)
    tokens=set(re.findall(r"[a-z']+", message.lower()))
    topic_terms = {
      "low_mood":{"lonely","alone","isolated","left out","sad","empty","miss","nobody","friendless"},
      "anxiety":{"anxious","anxiety","panic","nervous","worry","worried","scared","fear","overthink"},
      "academic_pressure":{"exam","assignment","deadline","grade","study","course","class","thesis","university","school","college","fail","semester"},
      "burnout":{"burnout","exhausted","overwhelmed","drained","tired","too much"},
      "sleep":{"sleep","insomnia","awake","nightmare","rest"},
      "relationships":{"friend","relationship","partner","family","parent","roommate","breakup","ignored","argument"}
    }
    scored=[]
    for item in resources:
        text=(item.get('title','')+' '+item.get('topic','')+' '+item.get('summary','')).lower()
        words=set(re.findall(r"[a-z']+", text))
        score=len(tokens & words)
        for topic in analysis['topics']:
            if topic in topic_terms and any(term in message.lower() for term in topic_terms[topic]):
                if topic in item.get('topic','') or (topic=='low_mood' and item.get('id')=='support'):
                    score+=3
        if score: scored.append((score,item))
    return [x[1] for x in sorted(scored,key=lambda x:x[0],reverse=True)[:limit]]

def fallback(message: str, analysis: dict, resources: list[dict], history: list[dict]) -> str:
    text=message.strip().lower()
    if re.fullmatch(r"(hi|hey|hello|hiya|heyy|good morning|good evening|good afternoon)[!. ]*", text):
        return "Hey 💛 I'm here. We can talk about something difficult, something ordinary, or absolutely nothing important. How are you feeling right now?"
    if any(p in text for p in ("can you listen","just listen","talk and listen","can we talk","stay with me","hear me out")):
        return "Of course. I'm listening. You don't have to organise your thoughts or find the right words. Tell me whatever is on your mind, at your own pace. I won't rush to give advice."
    if any(p in text for p in ("thank you","thanks","that helps")):
        return "You're welcome. I'm glad you told me. We can stay with this for a bit, or shift to something lighter—whatever feels right."
    topic=analysis['topics'][0] if analysis['topics'] else None
    if topic=='academic_pressure':
        opening="Study pressure can feel relentless, especially when several deadlines pile up."
        follow="What's weighing on you most: the amount of work, fear of the result, or something else?"
    elif topic=='anxiety':
        opening="That sounds unsettling. I'm glad you shared it with me."
        follow="Would you like to tell me what happened just before this feeling showed up?"
    elif topic=='low_mood':
        opening="Feeling lonely can really hurt, especially when it seems like everyone else has someone. I'm here to listen."
        follow="Has something happened recently that made the loneliness stronger, or has it been building for a while?"
    elif topic=='burnout':
        opening="It sounds like you've been carrying a lot without enough time to recover."
        follow="What has been taking the most out of you lately?"
    elif topic=='relationships':
        opening="It can be hard when relationships leave you with a lot of feelings to untangle."
        follow="What happened? I'm listening, and I won't jump straight into advice."
    elif topic=='sleep':
        opening="When sleep is difficult, the whole day can feel heavier."
        follow="Is it hard to fall asleep, stay asleep, or switch your thoughts off?"
    else:
        opening="I'm glad you reached out. I'm listening, and you can take your time."
        follow="What has been happening for you lately?"
    answer=opening+"\n\n"+follow
    if resources:
        answer += "\n\nIf you'd like an idea to try, here's one related resource: "+resources[0]['title']+". "+resources[0]['summary']
    return answer

async def llm_reply(message: str, resources: list[dict], history: list[dict]):
    key=os.getenv('LLM_API_KEY')
    if not key: return None
    base=os.getenv('LLM_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.getenv('LLM_MODEL','gpt-4o-mini')
    context="\n".join(f"- {r['title']}: {r['summary']} (source: {r['source_url']})" for r in resources)
    system=("You are MindMate, a warm, attentive, non-clinical student wellbeing companion for school, college and university students. Your primary job is to listen and respond to what the person actually said, not to force generic advice. Reflect one specific detail from their message. If they ask you to listen, do not give advice; invite them to continue gently. For greetings, greet naturally. Ask at most one gentle open question. Do not repeat the same opening or question from earlier turns. Avoid generic coping tips unless clearly relevant or requested. Validate feelings without claiming certainty. Never diagnose, prescribe, promise confidentiality, encourage dependency, or discourage human support. Do not infer age or location. For crisis content, tell them to contact local emergency services/nearest emergency department and a trusted person immediately; never imply you can monitor or dispatch help. Use the optional educational context only when relevant; don't force it into every reply.\nEDUCATIONAL CONTEXT:\n"+context)
    messages=[{'role':'system','content':system}]
    for item in history[-8:]:
        if item.get('role') in ('user','assistant') and isinstance(item.get('content'),str):
            messages.append({'role':item['role'],'content':item['content'][:2000]})
    messages.append({'role':'user','content':message})
    async with httpx.AsyncClient(timeout=25) as client:
        r=await client.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}'},json={'model':model,'temperature':0.7,'max_tokens':300,'messages':messages})
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
