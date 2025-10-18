from dotenv import load_dotenv
from langchain.globals import set_verbose, set_debug
from langchain_groq.chat_models import ChatGroq
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent

from agent.prompts import *
from agent.states import *
from agent.tools import write_file, read_file, get_current_directory, list_files

_ = load_dotenv()

set_debug(True)
set_verbose(True)

llm = ChatGroq(model="openai/gpt-oss-120b")


def planner_agent(state: dict) -> dict:
    """Converts user prompt into a structured Plan."""
    user_prompt = state["user_prompt"]
    resp = llm.with_structured_output(Plan).invoke(
        planner_prompt(user_prompt)
    )
    if resp is None:
        raise ValueError("Planner did not return a valid response.")
    return {"plan": resp}


def architect_agent(state: dict) -> dict:
    """Creates TaskPlan from Plan."""
    plan: Plan = state["plan"]
    resp = llm.with_structured_output(TaskPlan).invoke(
        architect_prompt(plan=plan.model_dump_json())
    )
    if resp is None:
        raise ValueError("Planner did not return a valid response.")

    resp.plan = plan
    print(resp.model_dump_json())
    return {"task_plan": resp}


def coder_agent(state: dict) -> dict:
    """LangGraph tool-using coder agent."""
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]
    existing_content = read_file.run(current_task.filepath)

    system_prompt = coder_system_prompt()
    user_prompt = (
        f"Task: {current_task.task_description}\n"
        f"File: {current_task.filepath}\n"
        f"Existing content:\n{existing_content}\n"
        "Use write_file(path, content) to save your changes."
    )

    coder_tools = [read_file, write_file, list_files, get_current_directory]
    react_agent = create_react_agent(llm, coder_tools)

    react_agent.invoke({"messages": [{"role": "system", "content": system_prompt},
                                     {"role": "user", "content": user_prompt}]})

    coder_state.current_step_idx += 1
    return {"coder_state": coder_state}


graph = StateGraph(dict)

graph.add_node("planner", planner_agent)
graph.add_node("architect", architect_agent)
graph.add_node("coder", coder_agent)

graph.add_edge("planner", "architect")
graph.add_edge("architect", "coder")
graph.add_conditional_edges(
    "coder",
    lambda s: "END" if s.get("status") == "DONE" else "coder",
    {"END": END, "coder": "coder"}
)

graph.set_entry_point("planner")
agent = graph.compile()

'''
#version 1
import os, sys
from gc import set_debug
from langchain import hub
from langchain.agents import create_react_agent
from langchain.globals import set_verbose,set_debug
from langgraph.constants import END
#load the api key
from dotenv import load_dotenv
from langgraph.graph import StateGraph
sys.path.append(os.path.dirname(__file__))
#import all the prompts from prompts.py
from agent.prompts import *
# import the langgraph schemas
from agent.states import *
#import the tools
from agent.tools import write_file, read_file, get_current_directory, list_files
from langchain_groq import ChatGroq
_ = load_dotenv()

# to get internal details, token usage,etc
set_debug(True)
set_verbose(True)

# langgraph
# states (where we take the user prompt) -> planner node -> architect node ->
# coder node(has multiple iterations) -> end
# every node in the graph takes state as an input and outputs state

from pydantic import BaseModel,Field

#keys present in .env successfully loaded
llm = ChatGroq(model="openai/gpt-oss-120b")
#llm = ChatGroq(model="openai/gpt-oss-20b")


#user prompt is something we will get from the state
def planner_agent(state : dict) -> dict:
    user_prompt = state["user_prompt"]
    resp = llm.with_structured_output(Plan).invoke(
        planner_prompt(user_prompt))
    if resp is None:
        raise ValueError("Planner did not return a valid response.")
    return {"plan": resp}

#creating architect_agent function
# we will have state as an input as well as an output
#here we need to get the plan from the planner node
# and to maintain the whole context we will need the plan as well as the task plan
# resp will be of type TaskPlan, so we can add the plan from the previous planner node
def architect_agent(state: dict) -> dict:
    plan : Plan = state["plan"]
    resp = llm.with_structured_output(TaskPlan).invoke(
        architect_prompt(plan=plan.model_dump_json()))
    if resp is None:
        raise ValueError("Architect did not return a valid response.")

    resp.plan = plan
    #now the output will also have the original plan
    print(resp.model_dump_json())
    return {"task_plan": resp}

#we will create the function for coder_agent
#based on the task description in the task plan the coder agent will write the code in the
# respective file
# coder agent performs all the implementation steps from the taskplan
#implementation steps is an array
# and for each step the coder agent will write code
def coder_agent(state : dict) -> dict:
    #langgraph tool-using coder agent
    coder_state : CoderState = state.get("coder_state")
    #initally we will just have the task_plan and no coder state
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"],current_step_idx=0)

    #the steps will continue untill all the steps are done
    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]
    existing_content = read_file.run(current_task.filepath)

    system_prompt = coder_system_prompt()
    user_prompt = (
        f"Task : {current_task.task_description}\n"
        f"File : {current_task.filepath}\n"
        f"Existing content : \n{existing_content}\n"
        "Use write_file(path,content) to save your changes."
    )
    #coder agent implements a task
    # now we will combine the system prompt and the user prompt
    #basically we tell the coder system prompt to generate the coder for the task
    #description provided by the user_prompt
    #resp = llm.invoke(system_prompt + user_prompt)
    #resp.content will return the actual code


    #just think you are a programmer
    #these are the functions you need
    #reading from a file, writing to the file,knowing what files are present, directory
    coder_tools = [read_file,write_file,list_files,get_current_directory]
    react_agent = create_react_agent(llm, coder_tools)
    react_agent.invoke({"messages": [{"role": "system", "content": system_prompt},
                                     {"role": "user", "content": user_prompt}]})

    coder_state.current_step_idx += 1
    return {"coder_state" : coder_state}



    #return empty state for now since code is being written on the disk
    #return {}
    #return {"code" : resp.content}


#first we will create the planner node
#and we will create a function named planner_agent
# structure of the state we are passing
graph = StateGraph(dict)
graph.add_node("planner",planner_agent)
#adding architect node now and we will create a function named architect_agent
graph.add_node("architect",architect_agent)
#now we will add the coder node
graph.add_node("coder",coder_agent)
#now add the edge between planner and architect
graph.add_edge("planner", "architect")
#now add the edge between architect to coder
graph.add_edge("architect", "coder")
graph.add_conditional_edges(
    "coder",
    lambda s:"END" if s.get("status") == "DONE" else "coder",
    {"END" : END, "coder" : "coder"}
)
graph.set_entry_point("planner")
#initially only the state is passed to the planner node
#but when it comes from the planner node it will contain both the user prompt and the plan

agent = graph.compile()

if __name__ == '__main__':
    result = agent.invoke({"user_prompt": "Build a colourful modern todo app in html css and js"},
                          {"recursion_limit": 100})
    print("Final State:", result)
'''

# features in the form of jira stories(individual programming tasks)
'''
#version 2
from dotenv import load_dotenv
from langchain.globals import set_verbose, set_debug
from langchain_groq.chat_models import ChatGroq
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent

from agent.prompts import *
from agent.states import *
from agent.tools import write_file, read_file, get_current_directory, list_files

_ = load_dotenv()

set_debug(True)
set_verbose(True)

llm = ChatGroq(model="openai/gpt-oss-120b")


def planner_agent(state: dict) -> dict:
    """Converts user prompt into a structured Plan."""
    user_prompt = state["user_prompt"]
    resp = llm.with_structured_output(Plan).invoke(
        planner_prompt(user_prompt)
    )
    if resp is None:
        raise ValueError("Planner did not return a valid response.")
    return {"plan": resp}


def architect_agent(state: dict) -> dict:
    """Creates TaskPlan from Plan."""
    plan: Plan = state["plan"]
    resp = llm.with_structured_output(TaskPlan).invoke(
        architect_prompt(plan=plan.model_dump_json())
    )
    if resp is None:
        raise ValueError("Planner did not return a valid response.")

    resp.plan = plan
    print(resp.model_dump_json())
    return {"task_plan": resp}

def coder_agent(state: dict) -> dict:
    steps = state['task_plan'].implementation_steps
    curr_step_idx = 0
    curr_task = steps[curr_step_idx]
    existing_content = read_file.run(curr_task.filepath)
    user_prompt = (
        f"Task : {curr_task.task_description}\n"
        f"File : {curr_task.filepath}\n"
        f"Existing content : \n{existing_content}\n"
        "Use write_file(path,content) to save your changes."
    )
    system_prompt = coder_system_prompt()
    coder_tools = [read_file, write_file, list_files, get_current_directory]
    react_agent = create_react_agent(llm, coder_tools)

    react_agent.invoke({"messages": [{"role": "system", "content": system_prompt},
                                     {"role": "user", "content": user_prompt}]})

    return {}


graph = StateGraph(dict)

graph.add_node("planner", planner_agent)
graph.add_node("architect", architect_agent)
graph.add_node("coder", coder_agent)

graph.add_edge("planner", "architect")
graph.add_edge("architect", "coder")
graph.add_conditional_edges(
    "coder",
    lambda s: "END" if s.get("status") == "DONE" else "coder",
    {"END": END, "coder": "coder"}
)

graph.set_entry_point("planner")
agent = graph.compile()
if __name__ == "__main__":
    result = agent.invoke({"user_prompt": "Build a colourful modern todo app in html css and js"},
                          {"recursion_limit": 100})
    print("Final State:", result)
'''