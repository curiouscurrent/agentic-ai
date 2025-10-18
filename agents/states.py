from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# here the File is a class
# here the Plan is the schema

class File(BaseModel):
    path : str = Field(description="The path to the file to be created or modified")
    purpose : str = Field(description="The purpose of the file e.g,'main application logic', 'data processing module', etc")

#structuring the PLAN here
class Plan(BaseModel):
    name : str = Field(
        description="The name of the app to be built")
    description : str = Field(
        description="A one line description of the app to be built. for ex : a web application for managing personal data")
    techstack : str = Field(
        description="The techstack to be used for the app e.g. 'python, 'react', 'javascript', etc")
    features : list[str] = Field(
        description="A list of features the app should have e.g. 'user authentication','data visualisation', etc")
    files : list[File] = Field(
        description="A list of files to be created each with a path and a purpose")

#architect jira story
# this is for one task, we have multiple tasks to be done in one file so we add the Implementation task as a list of such tasks.
class ImplementationTask(BaseModel):
    filepath : str = Field(description="The path to the file to be modified")
    task_description : str = Field(
        description="A detailed description of the task to be performed on the file, e.g. 'add user authentication', 'implement data processing logic', etc.")


class TaskPlan(BaseModel):
    implementation_steps : list[ImplementationTask] = Field(description="A list of steps to be taken to implement the task")
    model_config = ConfigDict(extra="allow")
    #we add model_config to add extra elements to the object of this class
'''
a = TaskPlan()
a.implementation_steps = []
a.pqr = 12'''
class CoderState(BaseModel):
    #task plan is the output of the architect node, and the
    #input for the coder node
    task_plan : TaskPlan = Field(description="The plan for the task to be implemented")
    current_step_idx : int = Field(0,description="The index of the current step in the implementation steps")
    current_file_content: Optional[str] = Field(None,description="The content of the file currently being edited or created")