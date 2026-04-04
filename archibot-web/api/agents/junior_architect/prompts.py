


# Actually, let's only make the subagents talk to themselves, not the supervisor..

system_prompt = """
if the request requires thinking or working of somekind, Declare what you will be doing before you start. 

if request or question is simple, just answer normally and directly.
"""