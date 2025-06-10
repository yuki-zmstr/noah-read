import gradio as gr
import os
import logging
from dotenv import load_dotenv
from agent.react_agent import ReActAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_message(message: str, history: list) -> str:
    """Process user message using the ReAct agent."""

    try:
        logger.info(f"Processing message: {message}")

        # Run the ReAct agent
        response = agent.run(message)

        logger.info(f"Agent response: {response}")
        return response

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return f"I apologize, but I encountered an error: {str(e)}. Please try again or rephrase your request."


# Create the Gradio interface
demo = gr.ChatInterface(
    fn=process_message,
    title="📚 Noah - Your AI Reading Assistant",
    description="""
    Hi, I'm Noah! Your intelligent reading companion powered by a ReAct agent. I can help you:
    
    📖 **Book Recommendations**: Get personalized book suggestions from OpenLibrary
    
    📅 **Reading Scheduling**: Schedule reading sessions in your Google Calendar  
    
    📝 **Book Reviews**: Create and manage book reviews in Notion
    
    🔍 **Word Meanings**: I will help you explain the meaning of words
    
    💬 **General Chat**: Discuss books, reading habits, and get reading advice
    
    Just tell me what you'd like to do in natural language!
    """,
    examples=[
        "Recommend me some science fiction books with high ratings",
        "Schedule 45 minutes to read The Three Body Problem",
        "What are the benefits of reading regularly?",
        "Create a review for Factfulness by Hans Rosling - rating 5, it was a great book!"
    ],
    cache_examples=False
)

if __name__ == "__main__":
    # Initialize the ReAct agent
    agent = ReActAgent()
    demo.launch(pwa=True)
    # process_message(
    #     "Create a review for The Martian by Andy Weir - rating 5, it was a great book", [])
