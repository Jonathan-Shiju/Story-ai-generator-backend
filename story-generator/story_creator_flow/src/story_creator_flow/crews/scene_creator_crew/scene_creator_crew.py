from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from pydantic import BaseModel
class Scenes(BaseModel):
    scene_1: str = ""
    scene_2: str = ""
    scene_3: str = ""
    scene_4: str = ""
    scene_5: str = ""

@CrewBase
class SceneCreatorCrew:
    """Scene Creator Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def scene_creator(self) -> Agent:
        return Agent(
            config=self.agents_config["scene_creator"],
        )

    @task
    def create_scenes(self) -> Task:
        return Task(
            config=self.tasks_config["create_scenes"],
            markdown=False,
            output_pydantic=Scenes,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Scene Creator Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )

