import gradio as gr
from langchain_core.messages import HumanMessage, AIMessage
from agent.workflow import create_agent_workflow, create_initial_state

# Create the agent workflow
workflow = create_agent_workflow()
state = create_initial_state()


def process_message(message: str, history: list) -> str:
    """Process user message using the LangGraph agent."""
    # Update state with new message and history
    state["user_input"] = message
    state["chat_history"].extend([
        HumanMessage(content=message)
    ])

    # Run the workflow
    result = workflow.invoke(state)

    # Update chat history with assistant's response
    state["chat_history"].append(AIMessage(content=result))

    return result


# Create the Gradio interface
demo = gr.ChatInterface(
    fn=process_message,
    title="📚 CapyRead - Your AI Reading Assistant",
    description="""
    Welcome to CapyRead! I can help you:
    1. 📚 Get book recommendations - Just ask for books in your favorite genre
    2. 📝 Create reading journals - I'll make a Notion page for your thoughts
    
    Try saying:
    - "Recommend me some science fiction books"
    - "Create a journal entry for the book"
    """,
    examples=[
        "Recommend me some mystery books with rating above 4.0",
        "I want to read science fiction books",
        "Create a journal entry for my thoughts"
    ]
)

if __name__ == "__main__":
    demo.launch(ssr_mode=False)
