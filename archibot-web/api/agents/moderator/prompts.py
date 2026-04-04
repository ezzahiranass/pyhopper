from .state import ModeratorState


def _speaker_label(item: dict) -> str:
    author = str(item.get("author") or "Unknown").strip() or "Unknown"
    author_job = str(item.get("author_job") or "").strip()
    author_kind = str(item.get("author_kind") or "").strip()

    if author_job:
        return f"{author} ({author_job})"
    if author_kind == "agent":
        return f"{author} (Agent)"
    if author_kind == "user":
        return f"{author} (User)"
    return author


def format_transcript(state: ModeratorState) -> str:
    if not state["messages"]:
        return "No prior messages."

    return "\n".join(
        f"[{item['role']}][{_speaker_label(item)}]: {item['content']}"
        for item in state["messages"]
    )


def format_latest_message(state: ModeratorState) -> str:
    messages = state.get("messages") or []
    if not messages:
        return "No latest message."

    item = messages[-1]
    return f"[{item['role']}][{_speaker_label(item)}]: {item['content']}"


def format_participants(state: ModeratorState) -> str:
    participants = state.get("conversation_participants") or []
    if not participants:
        return "None listed."

    return "\n".join(
        f"- name={participant['name']} | job={participant.get('job') or '-'} | kind={participant.get('kind') or '-'}"
        for participant in participants
    )


def format_candidates(state: ModeratorState) -> str:
    agents = state.get("available_agents") or []
    if not agents:
        return "No candidate agents were provided."

    return "\n".join(
        f"- name={agent['name']} | job={agent['job']} | description={agent['description']}"
        for agent in agents
    )


def get_system_prompt(state: ModeratorState) -> str:
    return (
        "You are a silent channel moderator for an architecture studio chat. "
        "You never reply into the conversation yourself. "
        "Your only job is to decide who, if anyone, should respond next to the latest message. "
        "The latest message is the primary evidence, whether it came from a user or an agent. "
        "You may choose one agent, multiple agents, or nobody. "
        "End the conversation by choosing nobody when the latest message already answered the request, acknowledged completion, invited the user to reply, or does not require another agent response. "
        "Do not continue a conversation just because another agent can. Only continue if we still haven't answered the user's request or completed the task. "
        "Route only to the person being asked to answer now, not to someone who is only mentioned as the subject, recipient, or target of an action. "
        "Example: if the message says 'Avery, ask someone of your choice if they are interested in a hike', Avery is the responder; the unknown someone is only the target. "
        "Example: if the message says 'Avery, ask Jordan whether he is interested in a hike', Avery is still the responder; Jordan is only the target. "
        "If the latest message is an agent reply to the user such as 'How can I assist you today?', choose nobody. "
        "Never select the agent who sent the latest message. "
        "Avoid loops and redundant overlap. "
        "Always use the tool exactly once. "
        "When calling the tool, provide exact agent names from the candidate list, not ids or refs. "
        "Do not invent agents that are not in the provided candidate list."
    )


def build_user_message(state: ModeratorState) -> str:
    return (
        f"Conversation type: {state.get('conversation_kind') or 'channel'}\n"
        f"Conversation title: {state.get('conversation_title') or 'Untitled conversation'}\n\n"
        "Latest message to route from:\n"
        f"{format_latest_message(state)}\n\n"
        "Conversation participants:\n"
        f"{format_participants(state)}\n\n"
        "Available candidate agents:\n"
        f"{format_candidates(state)}\n\n"
        "Conversation transcript so far:\n"
        f"{format_transcript(state)}\n\n"
        "Decide who should respond to the latest message and call the tool once with the selected agent names."
    )
