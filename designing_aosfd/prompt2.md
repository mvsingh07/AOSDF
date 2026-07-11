Tasks to improvise the AOSDF before starting with execution

PS: Do the tasks in sequence to avoid ambiguity

Task 1: First add the instruction of improvement points in AOSDF itself (v1.2), everywhere neccessary

ie. AI_Development_Model/framework.md
AI_Development_Model/templates.md
AI_Development_Model/manual.md
AI_Development_Model/workflow_initiator.md


Task 2: Actually implement the improvements in our docs

Task 3: Add a example text format in the manual at last of AI_Development_Model/manual.md, for how to call the workflow_initiator i.e what details in what format should be defined in the very first prompt itself

Task 4: Also create a simulation in manual.md clearly describing in what sequence is the agents are being called 

Task 5: Define manuual about the agents that need to be called manually for obvious reason for example research_and_review agent hsould be called manually along wiht reference points decided by human in loop

Task 6: Clearly update the folder structure and other require features in AI_Development_Model/templates.md as per improvment we have decide in aosdf



Improvements:

1. Add a reference point for marking the project ready for execution (create a file called project status).. where all human and agents can clearly see the current project status with metadata

2. Create a commander_agent in agents that will actually start the implementation as per the strategy defined in our execution plan ( this agent should know where to look at when it is called by clearly seeing where we left off).. however this agent will only intruct the other agents from where to start 

i.e it will be the sole responsibility of the 

i. execution_agent (for single agent strategy (Note: Create this agent if missing))
ii. validator_agent ( for multiple agents strategy)

to update the status of task in tracking_board (or the same source from where commander_agent will get to know about the project status)


3. Clearly define in AOSDF, that in what folder structure are implementation_prompts going to being written? and how they are going to tracked , current its not defined anywhere


4.  Create a git file and mark whole all folders of ai documentation in project structure as ignore, (i.e it should never be pushed to github)( Suggestion:move all the docs into one folder called aosdf-project_name, and update the reference through out accordingly)


5. Make the tasks defined in milestones and execution plane more human readable with clear separations through separate columns without effecting agent readibility, also in the foundation and core setups, ( task for setting up project repo as per tech stack decided are missing,, create milestone 0 for that)

