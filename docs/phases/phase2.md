# Phase 2 — Script Agent

## Goal
Build the first working agent in the pipeline: the Script Agent.
Takes a topic string, calls Claude, returns a complete YouTube video script.

## What Was Achieved
- First agent built and running: `src/agents/script_agent.py`
- Dev runner created: `run.py` for testing agents in isolation
- Full YouTube script generated via Claude API — verified working end to end

## Steps Taken

### 1. Built ScriptAgent class in `src/agents/script_agent.py`
**Why a class (not a plain function):**
An agent has state (its client, its model) and behaviour (its run method).
A class groups these together. As the agent grows (e.g. adding memory, retry logic),
the class gives us a clean place to add it without rewriting everything.

### 2. Defined SYSTEM_PROMPT as a module-level constant
**Why not inside the method:**
The system prompt is the agent's identity — it doesn't change per call.
Keeping it at the top of the file makes it easy to find, read, and update
without digging through method logic.

### 3. Used `src/config.py` for API key and model
**Why not `os.getenv()` directly in the agent:**
Config is loaded and validated once at startup. If the key is missing,
the error surfaces immediately with a clear message — not buried inside an
agent method call mid-pipeline.

### 4. Created `run.py` as a dev runner
**Why a separate runner (not a test):**
A test asserts correctness. A runner lets you see the output and judge it
with your own eyes. Both are needed — tests for automation, runners for
development and debugging.

## How the Claude API Works (What You Learned)

```
client.messages.create(
    model=...,         # which Claude model to use
    max_tokens=...,    # maximum length of the response
    system=...,        # standing instructions (role, format, rules)
    messages=[{        # the conversation — one or more turns
        "role": "user",
        "content": "Write a script about..."
    }]
)
```

Response comes back as `response.content[0].text` — the first content block's text.

## Key Concepts Introduced
- **System prompt:** The agent's standing instructions. Controls tone, format, and rules.
- **Messages list:** The conversation history sent to Claude. Grows with each turn.
- **max_tokens:** Controls response length. ~1 token ≈ 0.75 words.
- **Single responsibility:** ScriptAgent does one thing — topic in, script out.

## What This Unlocks for Phase 3
With a working Script Agent, Phase 3 can now build the Research Agent to sit in front of it.
The Research Agent will find today's trending topic and pass it to ScriptAgent.run().
This is where tool use is introduced — the Research Agent needs to call a web search API.
