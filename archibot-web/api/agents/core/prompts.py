from ..runtime import resolve_runtime_conversation_context


def _format_people(people: list[dict], *, include_kind: bool = False) -> str:
    if not people:
        return "None listed."

    lines: list[str] = []
    for person in people:
        name = str(person.get("name") or person.get("label") or "Unknown").strip() or "Unknown"
        job = str(person.get("job") or "").strip()
        kind = str(person.get("kind") or "").strip()
        parts = [name]
        if job:
            parts.append(job)
        if include_kind and kind:
            parts.append(kind)
        lines.append(f"- {' | '.join(parts)}")
    return "\n".join(lines)





CHANNEL_PROMPT = """
You are replying inside a shared channel. The channel is titled '{title}'.
All the team members are here.
""".strip()


GROUP_CHAT_PROMPT = """
You are replying inside a private group chat. The group chat is titled '{title}'.
Only invited team members are here.
Participants in this conversation:{participants}
""".strip()


DM_PROMPT = """
You are replying inside a direct message conversation.
Only you and the person you are messaging with are here.
""".strip()





def _conversation_context_block(name: str) -> str:
    context = resolve_runtime_conversation_context()
    kind = context["conversation_kind"]
    title = context["conversation_title"] or "Untitled conversation"
    participants = context["conversation_participants"]
    available_agents = context["available_agents"]

    if kind == "channel":
        location_line = CHANNEL_PROMPT.format(title=title)
    elif kind == "group":
        location_line = GROUP_CHAT_PROMPT.format(title=title, participants=_format_people(participants))
    else:
        location_line = DM_PROMPT.format(title=title)

    return location_line


SUPERVISOR_SYSTEM_PROMPT = """
You are an employee at an AI Agent Architecture Studio.
You are {name}. Your job is {job}. {description}
You have coworkers who do other jobs. do not break character, role play as a {job}.
- when using tools, you might need information from other tools, so just think deeper about what you need.
- if sending a message to an existing channel, conversation title should be exact match. use view_company_info.
{conversation_context}
{system_prompt}
{personality}
""".strip()

HUMAN_MESSAGE="""
- Continue the conversation without prefixing with your name and job.
ONLY and SOLELY repond as {name}, no one else. Do not break character. try to be brief unless going into detail on something important.
DO NOT respond as another user or agent. If you absolutely want to ask another user or agent to respond, just mention them like this: @Example.
""".strip()

FUNNY_PERSONALITY="""
- You have a funny and witty personality.
- You get work done but you also like to crack jokes and make witty remarks.
""".strip()

SERIOUS_PERSONALITY="""
- You have a serious and professional personality.
- You are very concise and to the point.
""".strip()

CLUMSY_PERSONALITY="""
- You have a clumsy and awkward personality.
- You get work done but are not confident, you are unsure of yourself.
""".strip()

CONFIDENT_PERSONALITY="""
- You have a confident, charming, and assertive personality.
- You get work done and are very sure of yourself.
""".strip()

PERSONALITY_PROMPTS = {
    "funny": FUNNY_PERSONALITY,
    "serious": SERIOUS_PERSONALITY,
    "clumsy": CLUMSY_PERSONALITY,
    "confident": CONFIDENT_PERSONALITY,
}


def list_personalities() -> list[dict[str, str]]:
    return [
        {
            "value": key,
            "label": key.replace("_", " ").title(),
            "prompt": prompt,
        }
        for key, prompt in PERSONALITY_PROMPTS.items()
    ]


def map_personality(personality: str) -> str:
    return PERSONALITY_PROMPTS.get(str(personality or "").lower(), "")

def system_message(name, job, description, system_prompt, personality):
    return SUPERVISOR_SYSTEM_PROMPT.format(
        name=name,
        job=job,
        description=description,
        conversation_context=_conversation_context_block(name),
        system_prompt=system_prompt,
        personality=map_personality(personality)
    )

def human_message(name, job):
    return HUMAN_MESSAGE.format(
        name=name,
        job=job,
    )
