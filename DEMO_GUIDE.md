# 🚀 Demo Setup Guide: Agents & Workflows

This guide will help you set up two powerful multi-agent workflows from scratch using the **AgentOrch** platform. Whether you're a developer or a non-tech user, follow these steps to see the platform in action.

---

## 🏗️ Getting Started
Ensure you have the platform running and you have your **Groq API Key** and **Telegram Bot Token** configured in your `.env` file.

1. Open the **Web Dashboard** (usually `http://localhost:3000`).
2. Navigate to the **Agents** tab.

---

## 🌤️ Demo 1: The Personal Weather Assistant
This workflow allows you to ask for the weather anywhere in the world, even through Telegram!

### Step 1: Create the Weather Agent
In the **Agents** tab, click **"Create New Agent"** and enter the following:
- **Name**: `Weather Specialist`
- **Role**: `Meteorologist`
- **Description**: `An agent that provides accurate real-time weather updates.`
- **System Prompt**: `You are a helpful weather assistant. When a user asks for the weather in a location, use the weather tool to find the information and provide a friendly summary. If no location is provided, ask the user for one.`
- **Tools**: Select `weather` from the list.
- **Save** the agent.

### Step 2: Build the Weather Workflow
1. Navigate to the **Builder** tab.
2. Drag a **Trigger (Input)** node onto the canvas.
3. Drag an **Agent** node onto the canvas.
4. Click on the Agent node and select `Weather Specialist` from the dropdown.
5. **Connect** the Trigger node to the Weather Specialist node.
6. **Save** the workflow as `Weather Assistant Workflow`.

### Step 3: Test It!
- **In Dashboard**: Click **"Execute"** on the workflow and type "What is the weather in Tokyo?".
- **On Telegram**: Message your bot "How is the weather in London?".

---

## 🔍 Demo 2: Smart Research & Triage
This is a more complex workflow where one agent "thinks" and conditionally routes to another agent to "search" only if necessary.

### Step 1: Create the Search Sub-Agent
Create an agent with these details:
- **Name**: `Data Researcher`
- **Role**: `Web Researcher`
- **Description**: `Specializes in fetching live data from the internet.`
- **System Prompt**: `You are a research expert. Read the conversation history. Use your tools to find the single most relevant piece of information or data point requested. Provide a concise, final response to the user.`
- **Tools**: Select `web_search` and `http_request`.
- **Save** the agent.

### Step 2: Create the Triage Agent
Create another agent:
- **Name**: `System Triage`
- **Role**: `Intent Classifier`
- **Description**: `Analyzes user requests and routes them to the search team.`
- **System Prompt**: `You are the first point of contact. Analyze the user's request. If they are asking for live data, facts, or news that requires a web search, your response MUST include the exact phrase 'ROUTE_TO_SEARCH' followed by a summary of what needs to be searched. If it's just a general greeting or conversation, answer them normally without the phrase.`
- **Tools**: None (This agent uses its "brain" to triage).
- **Save** the agent.

### Step 3: Build the Research Workflow
To make the agents work together intelligently, we will use a **Condition Node**.
1. Go to the **Builder** tab.
2. Drag a **Trigger (Input)** node to the canvas.
3. Drag **two Agent nodes**. Set the first to `System Triage` and the second to `Data Researcher`.
4. Drag a **Condition** node to the canvas.
5. Click on the Condition node and enter the condition: `contains 'ROUTE_TO_SEARCH'`
6. **Connect** them using the specific True/False handles:
   * `Trigger` ➡️ `System Triage`
   * `System Triage` ➡️ `Condition Node` (connect to its left input)
   * `Condition Node` (**True** handle) ➡️ `Data Researcher`
   * *(Leave the **False** handle unconnected so the workflow simply returns the Triage Agent's conversational response!)*
7. **Save** the workflow as `Smart Research Pipeline`.

### Step 4: Test It!
- Execute the workflow and type: "Find me the latest stock price of NVIDIA and explain why it changed today."
- Watch the **Live Logs** to see the `System Triage` agent analyze your request and the `Data Researcher` agent dive into the web to find the answer!

---

## 💡 Pro Tips for Success
- **System Prompts Matter**: The more specific you are in the "System Prompt" field, the better the agent performs.
- **Watch the Logs**: Use the logs in the dashboard to see exactly how agents are "thinking" and which tools they are calling.
- **Telegram Connection**: If your Telegram bot isn't responding, double-check your `TELEGRAM_BOT_TOKEN` in the `.env` file and restart the backend.
