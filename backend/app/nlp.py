import re
from collections import Counter

TOPICS = {
    "academic_pressure": {"exam","assignment","deadline","grade","study","course","class","thesis","university","school","college","fail","semester","presentation"},
    "anxiety": {"anxious","anxiety","panic","nervous","worry","worried","scared","fear","overthink","racing"},
    "low_mood": {"sad","empty","hopeless","lonely","alone","cry","tired","worthless","unmotivated","down"},
    "burnout": {"burnout","exhausted","overwhelmed","drained","疲","can't","cannot","everything","too much"},
    "relationships": {"friend","relationship","partner","family","parent","roommate","breakup","ignored","argument"},
    "sleep": {"sleep","insomnia","awake","tired","nightmare","rest"},
}
CRISIS = re.compile(r"\b(kill myself|suicid(?:e|al)|end my life|want to die|hurt myself|self[- ]harm|can't keep myself safe|cannot keep myself safe|overdose|end it all)\b", re.I)
NEGATIVE = {"sad","scared","anxious","angry","lonely","hopeless","exhausted","overwhelmed","afraid","panic","hurt"}
POSITIVE = {"happy","calm","good","hopeful","excited","grateful","proud","better"}

def analyze(text: str) -> dict:
    words = re.findall(r"[a-z']+", text.lower())
    counts = {topic: len(set(words) & terms) for topic, terms in TOPICS.items()}
    topics = [k for k,v in sorted(counts.items(), key=lambda x:x[1], reverse=True) if v][:2]
    neg, pos = len(set(words)&NEGATIVE), len(set(words)&POSITIVE)
    sentiment = "negative_cues" if neg>pos else "positive_cues" if pos>neg else "unclear"
    return {"topics":topics,"sentiment_cues":sentiment,"crisis_flag":bool(CRISIS.search(text))}
