from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from pydantic import BaseModel




@CrewBase
class StoryOutlineCrew:
    """Story Outline Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def story_outline_creator(self) -> Agent:
        return Agent(
            config=self.agents_config["story_outline_creator"],
        )

    @agent
    def story_detail_filler(self) -> Agent:
        return Agent(
            config=self.agents_config["story_detail_filler"],
        )

    @task
    def create_story_outline(self) -> Task:
        return Task(
            config=self.tasks_config["create_story_outline"],
        )

    @task
    def fill_story_details(self) -> Task:
        return Task(
            config=self.tasks_config["fill_story_details"],
            markdown=False,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Research Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )