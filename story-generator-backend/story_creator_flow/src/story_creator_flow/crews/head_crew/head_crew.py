from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List


@CrewBase
class HeadCrew:
    """Head Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]
    @agent
    def genre_setter(self) -> Agent:
        return Agent(
            config=self.agents_config["genre_setter"],
            verbose=True
        )

    @agent
    def tone_setter(self) -> Agent:
        return Agent(
            config=self.agents_config["tone_setter"],
        )

    @agent
    def character_creator(self) -> Agent:
        return Agent(
            config=self.agents_config["character_creator"]
        )

    @task
    def set_genre(self) -> Task:
        return Task(
            config=self.tasks_config["set_genre"],
        )

    @task
    def set_tone(self) -> Task:
        return Task(
            config=self.tasks_config["set_tone"],
        )

    @task
    def create_character(self) -> Task:
        return Task(
            config=self.tasks_config["create_character"],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Research Crew"""
        return Crew(
            agents=[self.genre_setter(), self.tone_setter(), self.character_creator()],  
            tasks=[
                self.set_genre(),
                self.set_tone(),
                self.create_character(),
            ], 
            process=Process.sequential,
            verbose=True,
        )
