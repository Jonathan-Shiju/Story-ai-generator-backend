#!/usr/bin/env python
from random import randint

from pydantic import BaseModel
from typing import List

from crewai.flow import Flow, listen, start

from story_creator_flow.crews.head_crew.head_crew import HeadCrew
from story_creator_flow.crews.story_outline_crew.story_outline_crew import StoryOutlineCrew
from story_creator_flow.crews.scene_creator_crew.scene_creator_crew import SceneCreatorCrew

class StoryFlowState(BaseModel):
    characters: str = ""
    story: str = ""
    user_story: str = ""
    user_genre: str = "" 
    user_tone: str = ""
    user_audience: str = ""

class Scenes(BaseModel):
    scene_1: str = ""
    scene_2: str = ""
    scene_3: str = ""
    scene_4: str = ""
    scene_5: str = ""

class ScenesFlowState(BaseModel):
    scenes: Scenes = Scenes()  # Provide a default value
    story: str = ""
    

class StoryFlow(Flow[StoryFlowState]):
    @start()
    def run_head_crew(self):
        print("Running HeadCrew")
        result = (
            HeadCrew()
            .crew()
            .kickoff(inputs={"story": self.state.user_story,
                             "genre":self.state.user_genre, "tone": self.state.user_tone,
                             "audience": self.state.user_audience})
        )
        self.state.characters = result.raw

    @listen(run_head_crew)
    def run_story_outline_crew(self):
        print("Running StoryOutlineCrew")
        result = (
            StoryOutlineCrew()
            .crew()
            .kickoff(inputs={
                "characters": self.state.characters,
                "audience": self.state.user_audience,
                "story_tone": self.state.user_story,
                "story_genre":self.state.user_genre,
            })
        )
        self.state.story = result.pydantic
        print("Story Details:")
        print(self.state.story.introduction_setting)
        print(self.state.story.conflict_rising_action)
        print(self.state.story.climax)
        print(self.state.story.resolution)

class ScenesFlow(Flow[ScenesFlowState]):
    @start()
    def run_scene_creator_crew(self):
        print("Running SceneCreatorCrew")
        result = (
            SceneCreatorCrew()
            .crew()
            .kickoff(inputs={
                "story": self.state.story,
            })
        )
        self.state.scenes = result.pydantic

        # Print all scenes
        print("Extracted Scenes:")
        print(self.state.scenes.scene_1)
        print(self.state.scenes.scene_2)
        print(self.state.scenes.scene_3)
        print(self.state.scenes.scene_4)
        print(self.state.scenes.scene_5)
        



def kickoff():
    story_flow = StoryFlow()
    story_flow.kickoff(inputs={"user_story": "A young girl finds a secret door in her grandmother's attic.", "user_tone": "foreshadowing", "user_genre": "mystery", "user_audience": "Kids"})
    scenes_flow = ScenesFlow()
    scenes_flow.kickoff(inputs={"story": str(story_flow.state.story)})


def plot():
    story_flow = StoryFlow()
    story_flow.plot()


if __name__ == "__main__":
    plot()


