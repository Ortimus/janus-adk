# Janus ADK — Hierarchical policy management for  AI Agents

Policy-based AI Agent System with Google Gemini & ADK Integration

This project demonstrates how to integrate **policy-based action validation** into a Janus ADK agent using a **Policy Decision Point (PDP)** and **YAML policy configuration**.  

It is intended to evolve into a clean, enterprise-ready baseline for future expansion, including centralized policy services, distributed enforcement points, SOC logging pipelines, or governance reporting.

NOTE: This is a [submssion](kaggle.com/competitions/agents-intensive-capstone-project/writeups/hierarchical-policy-architecture) for the [Kaggle Agents Intensive Capstone project](https://www.kaggle.com/competitions/agents-intensive-capstone-project/overview). 

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TD
    subgraph core["🎯 Janus Core"]
        A2["Janus Agent"]
    end

    subgraph llm["🤖 LLM Integration"]
        A3["Gemini Client"]
    end

    subgraph policy["🛡️ Policy Engine"]
        A0["Policy Decision Point (PDP)"]
        A1["Policy Repository"]
    end

    subgraph adk["⚙️ ADK Layer"]
        A4["ADK Adapter (Agent & Orchestrator)"]
    end

    A2 -- "Consults" --> A0
    A2 -- "Uses LLM via" --> A3
    A2 -- "Manages" --> A4
    A0 -- "Retrieves policies from" --> A1
    A4 -- "Delegates policy evaluation" --> A0
    A4 -- "Communicates via" --> A3

    style core fill:#e8f4f8,stroke:#0369a1
    style llm fill:#fef3c7,stroke:#d97706
    style policy fill:#dcfce7,stroke:#16a34a
    style adk fill:#f3e8ff,stroke:#9333ea
```

## 🎯 Features

### Core Policy System
- ✅ Hierarchical policy enforcement (Enterprise > Domain > Agent)
- ✅ Pattern matching (e.g. finance-*)
- ✅ Amount-based conditions
- ✅ YAML policy configuration

### Google Gemini Integration
- ✅ Natural language intent extraction
- ✅ Intelligent response generation
- ✅ Context-aware conversations
- ✅ Multi-turn chat support

### Google ADK Integration
- ✅ ADK-compatible agent framework
- ✅ Tool registration system
- ✅ Multi-agent orchestration
- ✅ Policy-controlled tool execution

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [Overview](https://github.com/Ortimus/janus-adk/blob/main/docs/00_overview.md) | High-level system overview |
| [Janus Agent](https://github.com/Ortimus/janus-adk/blob/main/docs/01_janus_agent.md) | Core agent architecture and usage |
| [Policy Decision Point (PDP)](https://github.com/Ortimus/janus-adk/blob/main/docs/02_policy_decision_point_pdp.md) | Policy evaluation engine |
| [Policy Repository](https://github.com/Ortimus/janus-adk/blob/main/docs/03_policy_repository.md) | YAML policy storage and loading |
| [Gemini Client](https://github.com/Ortimus/janus-adk/blob/main/docs/04_gemini_client.md) | NLU/NLG processing and intent extraction |
| [ADK Adapter & Orchestrator](https://github.com/Ortimus/janus-adk/blob/main/docs/05_adk_adapter_agent_orchestrator.md) | Google ADK integration and multi-agent orchestration |
| [Sample Analysis Report](https://github.com/Ortimus/janus-adk/blob/main/docs/06_demo_analysis.md) | Sample analysis report of demo scripts|

- [Google Gemini API](https://ai.google.dev/docs)
- [Google ADK](https://cloud.google.com/agent-development-kit)


## 📁 Project Structure

```
janus-adk/
├── janus_agent/
│   ├── core/              # Core policy system
│   ├── adapters/          # ADK adapter
│   ├── integrations/      # Gemini client
│   └── agent.py           # Main agent
├── policies/
│   └── examples/          # YAML policies
└── examples/
    └── adk_demo/          # Gemini/ADK demo
```

## 🔧 Configuration

### Policy Levels

1. **Enterprise** - Organization-wide rules
2. **Domain** - Department/team rules  
3. **Agent** - Service-specific rules

### Example Policy

```yaml
policies:
  - id: "agent-allow-small-payments"
    description: "Allow payments under $1000"
    level: "agent"
    action: "payment.transfer"
    subject: "*"
    resource: "*"
    effect: "allow"
    match:
      amount_max: 999
    priority: 10
```

## 🤖 Using with Gemini

```python
from janus_agent.agent import JanusAgent

# Create Gemini-powered agent
agent = JanusAgent("financial-bot", use_gemini=True)

# Process natural language
response = await agent.run("Pay $100 to supplier")
```

## 📚 ADK Orchestration

```python
from janus_agent.agent import create_adk_orchestrator

# Create orchestrator
orchestrator = create_adk_orchestrator()

# Create specialized agents
payment_agent = orchestrator.create_agent("payment-processor")
audit_agent = orchestrator.create_agent("audit-monitor")
```

## 🔑 Getting Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/)
2. Click "Get API Key"
3. Create a new API key
4. Set as environment variable:
   ```bash
   export GOOGLE_API_KEY='your-key-here'
   ```


## 🚀 Quick Start

### 1. Create virtual environment 

```
   python -m venv .jagenv
   source .jagenv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Google API Key

```bash
# Option 1: Environment variable
export GOOGLE_API_KEY='your-api-key-here'

# Option 2: Create .env file
cp .env.template .env
# Edit .env and add your API key
```

Get your API key from: https://makersuite.google.com/app/apikey

### 4. Run Demos

```bash
# Gemini integration demo
python examples/adk_demo/main_demo.py
```

**Sample demo analysis can be found here: [DEMO Analysis](demo_analysis.md)**


## 🎓 Capstone Project

This project demonstrates:
- Integration of Google's Gemini LLM
- ADK-compatible agent architecture
- Policy-based access control
- Multi-agent orchestration
- Natural language processing


---

## License

This work is licensed under a
[Creative Commons Attribution 4.0 International License][cc-by].

[![CC BY 4.0][cc-by-image]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-image]: https://i.creativecommons.org/l/by/4.0/88x31.png