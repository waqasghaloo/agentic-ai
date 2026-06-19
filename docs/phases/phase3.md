# Phase 3 — Research Agent + Tool Use

## Goal
Build the Research Agent that finds trending YouTube topics using web search,
and connect it to the Script Agent to form the first two-agent pipeline.

## What Was Achieved
- `src/tools/search_tool.py` — DuckDuckGo search wrapped as a Claude tool
- `src/agents/research_agent.py` — agent that uses tool use to find trending topics
- `run.py` updated — chains Research Agent → Script Agent end to end
- Full pipeline verified: real trending topic found → full script generated automatically

## Steps Taken

### 1. Added `ddgs` library for web search
**Why DuckDuckGo over Google/Serper/Tavily:**
Free, no API key required for learning and development.
The search provider is isolated in `src/tools/search_tool.py` — swapping it
later requires changing only that one file, not any agent code.

### 2. Created `src/tools/search_tool.py`
Contains two things:
- `SEARCH_TOOL_DEFINITION` — JSON schema that tells Claude what the tool does
  and what arguments it accepts. Claude reads this to decide when and how to call it.
- `search_web()` — the actual Python function that performs the search.
  Claude does NOT run this. Claude requests it. Our code runs it.

**Why the tool lives in `src/tools/` not inside the agent:**
Tools are stateless functions that call external services.
Multiple agents can use the same tool without duplicating code.

### 3. Created `src/agents/research_agent.py` with the agentic loop
The most important pattern introduced in this phase.

```
while True:
    response = call Claude with tools
    
    if stop_reason == "end_turn":
        return Claude's final answer   ← done
    
    if stop_reason == "tool_use":
        run the tool Claude requested
        send results back to Claude    ← loop again
```

Claude ran 14 searches in its first real run — deciding each query itself based
on what the previous results told it. This is autonomous decision-making in action.

### 4. Updated `run.py` to chain both agents
```
research_agent.run(niche) → topic
script_agent.run(topic)   → script
```
The output of one agent becomes the input of the next. This is the pipeline pattern.

## Key Concepts Introduced

**Tool Use:** Claude does not run tools. It requests them. Your code runs them and
sends results back. This back-and-forth is what makes an agent truly agentic.

**Tool Definition (JSON Schema):** The contract between Claude and your tool.
Name, description, and input parameters. Claude reads this to know what's available.

**Agentic Loop:** The while loop that keeps the conversation going until Claude
has no more tools to call. Essential pattern in every agentic system.

**Tool Result:** The package sent back to Claude containing the tool's output,
linked to the original request via `tool_use_id`.

**Pipeline:** Chaining agents so the output of one becomes the input of the next.
Research → Script is the first two steps of our eventual full pipeline.

## What the Pipeline Looks Like Now

```
ResearchAgent.run(niche)
    └── calls Claude with search_web tool
    └── Claude searches 14 times autonomously
    └── Claude picks best trending topic
         └── ScriptAgent.run(topic)
             └── calls Claude with topic
             └── Claude writes full script
```

## What This Unlocks for Phase 4
With Research and Script agents working, Phase 4 adds the Voice Agent —
converting the script to audio using ElevenLabs. This introduces paid external
API integration and shows how to handle audio file output (not just text).
