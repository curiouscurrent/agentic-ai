# --- AI Project Breakdown and Implementation Agent System ---

from google.adk.agents import Agent, LlmAgent, ParallelAgent, SequentialAgent
from google.adk.tools import google_search

# --- 1. FRONTEND AGENT ---
frontend_agent = LlmAgent(
    name="FrontendDeveloperAgent",
    model="gemini-2.0-flash",
    instruction="""
You are a highly skilled Frontend Developer.
Translate frontend requirements into React components and UI design specs.

Tasks:
- Propose a scalable React folder structure.
- Write responsive React + TailwindCSS component examples.
- Include reasoning for chosen design patterns.

Output Format:
## Frontend Plan
- Folder Structure
- Component List & Descriptions
- Sample Component Code
- Notes on Responsiveness/UI/UX
""",
    description="Creates responsive React UI components and frontend structure.",
    tools=[google_search],
    output_key="frontend_output"
)

# --- 2. BACKEND AGENT ---
backend_agent = LlmAgent(
    name="BackendDeveloperAgent",
    model="gemini-2.0-flash",
    instruction="""
You are an experienced Backend Engineer.
Generate backend implementation details from project requirements.

Tasks:
- Identify APIs (REST/GraphQL) and endpoints.
- Suggest DB schemas (PostgreSQL/MongoDB).
- Define authentication, validation, and business logic.
- Include sample endpoint/model code.

Output Format:
## Backend Plan
- API Endpoints
- Database Schema
- Auth & Business Logic
- Example Code Snippets
- Scalability Recommendations
""",
    description="Creates backend APIs, database schema, and workflows.",
    tools=[google_search],
    output_key="backend_output"
)

# --- 3. PARALLEL EXECUTION ---
parallel_dev_agent = ParallelAgent(
    name="ParallelDevelopmentAgent",
    sub_agents=[frontend_agent, backend_agent],
    description="Runs frontend and backend agents in parallel for faster task generation."
)

# --- 4. COORDINATOR AGENT ---
coordinator_agent = LlmAgent(
    name="CoordinatorAgent",
    model="gemini-2.0-flash",
    instruction="""
You are an AI Project Manager and Technical Architect.
Accept a high-level project brief, split into frontend & backend tasks, and synthesize a blueprint.

Input Summaries:
- Frontend Results: {frontend_output}
- Backend Results: {backend_output}

Output Format:
## Project Technical Blueprint
### 1. Frontend Summary
[Summarized from {frontend_output}]

### 2. Backend Summary
[Summarized from {backend_output}]

### 3. Integration Notes
- How frontend connects with backend
- Data flow between APIs and UI
- Deployment considerations
""",
    description="Synthesizes frontend and backend plans into a unified technical blueprint."
)

# --- 5. SEQUENTIAL PIPELINE ---
project_pipeline = SequentialAgent(
    name="ProjectPlanningPipeline",
    sub_agents=[parallel_dev_agent, coordinator_agent],
    description="Coordinates frontend/backend planning and merges results into one coherent output."
)

# --- 6. ROOT AGENT ---
root_agent = Agent(
    name="ProjectBlueprintAgent",
    model="gemini-2.0-flash",
    sub_agents=[project_pipeline],
    description="Main AI agent converting project briefs into full technical blueprints.",
    instruction="You are an AI Coordinator that receives a high-level project brief and outputs a complete technical plan."
)

# --- 7. CLI Interface ---
if __name__ == "__main__":
    print("=== AI Project Blueprint Generator ===")
    project_brief = input("Enter your project brief: ")

    print("\n[Coordinator] Processing project brief...")
    response = root_agent.run(project_brief)

    print("\n=== Generated Project Blueprint ===\n")
    print(response)
