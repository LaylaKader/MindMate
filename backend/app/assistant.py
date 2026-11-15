import os
import httpx
from .nlp import analyze

CRISIS_REPLY = ("I'm really sorry things feel this heavy. I'm glad you said something. I can't assess your safety or provide crisis care, and I don't want you to be alone with this. If you may act on these thoughts or cannot stay safe, contact your local emergency number or go to the nearest emergency department now. Please tell a trusted person and ask them to stay with you. If you can do so safely, move away from anything you might use to hurt yourself. This chat is not monitored and cannot contact help for you.")

def retrieve(message: str, resources: list[dict], limit: int=3):
    tokens=set(__import__('re').findall(r"[a-z']+", message.lower()))
    scored=[]
    for item in resources:
        words=set(__import__('re').findall(r"[a-z']+", (item['title']+' '+item['topic']+' '+item['summary']).lower()))
        score=len(tokens & words)
        if item['topic'] in analyze(message)['topics']: score+=2
        if score: scored.append((score,item))
    return [x[1] for x in sorted(scored,key=lambda x:x[0],reverse=True)[:limit]]

def fallback(message: str, analysis: dict, resources: list[dict]) -> str:
    topic=analysis['topics'][0] if analysis['topics'] else None
    opening="That sounds like a lot to carry. Thanks for trusting me with a little of it."
    if topic=='academic_pressure': opening="Study pressure can feel relentless, especially when several deadlines pile up."
    elif topic=='anxiety': opening="That sounds unsettling. We don't have to solve the whole thing in one go."
    elif topic=='low_mood': opening="I'm sorry this has been feeling so lonely or heavy. You deserve support with it."
    elif topic=='burnout': opening="It sounds as though you've been running on very little space to recover."
    elif topic=='relationships': opening="Relationships can bring up complicated feelings. It makes sense to want space to untangle them."
    elif topic=='sleep': opening="When rest is difficult, everything else can feel harder too."
    follow="What feels like the hardest part right now?"
    if topic=='academic_pressure': follow="Would it help to pick just one task for the next 15 minutes, or would you rather talk about the pressure first?"
    elif topic=='anxiety': follow="If it feels okay, name one thing you know for sure right now, separate from what your worry is predicting."
    elif topic=='low_mood': follow="Is there one person you feel relatively safe contacting today, even with a short message?"
    elif topic=='burnout': follow="Could one demand be paused, made smaller, or shared with someone?"
    elif topic=='sleep': follow="Would a low-pressure wind-down for tonight be more useful than trying to force sleep?"
    suffix=""
    if resources: suffix="\n\nA small idea from the resource library: "+resources[0]['summary']
    return opening+"\n\n"+follow+suffix+"\n\nI'm an AI support tool, not a counsellor. If this keeps affecting your daily life, a trusted person or qualified professional can offer support beyond this chat."

async def llm_reply(message: str, resources: list[dict]):
    key=os.getenv('LLM_API_KEY'); base=os.getenv('LLM_BASE_URL','https://api.openai.com/v1').rstrip('/'); model=os.getenv('LLM_MODEL','gpt-4o-mini')
    if not key: return None
    context='\\n'.join(f"- {r['title']}: {r['summary']} (source: {r['source_url']})" for r in resources)
    system=("You are MindMate, a warm, non-clinical student wellbeing support companion for people of all student ages. Validate feelings without claiming certainty. Ask at most one gentle question. Offer one small, optional, low-risk coping step. Never diagnose, prescribe, make promises, encourage dependency, or discourage human support. Do not act as therapist. Do not infer age or location. For crisis content, tell the user to contact local emergency services/nearest emergency department and a trusted person immediately; do not imply you can monitor or dispatch help. Avoid collecting identifying details. If relevant, use only this educational reference context, not as medical advice:\\n"+context)
    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}'},json={'model':model,'temperature':0.5,'max_tokens':350,'messages':[{'role':'system','content':system},{'role':'user','content':message}]})
        r.raise_for_status(); return r.json()['choices'][0]['message']['content'].strip()

async def respond(message: str, resources: list[dict]):
    analysis=analyze(message)
    if analysis['crisis_flag']: return {'reply':CRISIS_REPLY,'resources':[],'safety_route':'urgent','nlp':analysis,'engine':'safety'}
    matches=retrieve(message,resources)
    try: reply=await llm_reply(message,matches)
    except Exception: reply=None
    engine='llm+retrieval' if reply else 'retrieval+fallback'
    return {'reply':reply or fallback(message,analysis,matches),'resources':matches,'safety_route':'standard','nlp':analysis,'engine':engine}
