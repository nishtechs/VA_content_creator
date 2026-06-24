import os
import sys

from dotenv import load_dotenv
load_dotenv()

from agents import make_visual_designer_agent
from crewai import Task, Crew

def test():
    print("Initializing agent...")
    agent = make_visual_designer_agent()
    task = Task(
        description="Generate a simple title slide HTML.",
        expected_output="HTML code",
        agent=agent
    )
    crew = Crew(agents=[agent], tasks=[task])
    print("Kicking off crew...")
    try:
        result = crew.kickoff()
        print("Success:", result)
    except Exception as e:
        print("Error during kickoff:", e, file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

if __name__ == "__main__":
    test()
