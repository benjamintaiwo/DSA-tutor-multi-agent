import os
import sys
import logging

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tutor.agent import TutorAgent

def main():
    # Day 4a: Observability - Configure Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("tutor.log")
        ]
    )
    logger = logging.getLogger(__name__)

    print("Initializing AI DS & Algorithm Tutor...")
    logger.info("Starting AI Tutor application")
    
    # Configuration - In a real app, these would come from env vars
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
    LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    USE_PERSISTENT_MEMORY = os.getenv("USE_PERSISTENT_MEMORY", "false").lower() == "true"
    
    try:
        tutor = TutorAgent(
            project_id=PROJECT_ID, 
            location=LOCATION,
            use_persistent_memory=USE_PERSISTENT_MEMORY
        )
    except Exception as e:
        print(f"Error initializing TutorAgent: {e}")
        print("Please ensure you have Google Cloud credentials set up.")
        return

    print("\n--- AI Tutor Ready ---")
    print("Type 'exit' or 'quit' to stop.")
    
    session_id = "student_session_001"
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye! Happy coding.")
                break
            
            if not user_input:
                continue
                
            response = tutor.chat(user_input, session_id=session_id)
            
            # Show which agent is responding based on current state
            current_state = tutor.orchestrator.student.current_state.value
            if "INTERVIEW" in current_state:
                persona = "Interviewer"
            elif "TEACHING" in current_state:
                persona = "Student (Alex)"
            else:
                persona = "Tutor"
            
            print(f"\n{persona}: {response}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
