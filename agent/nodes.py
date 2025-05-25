from typing import Dict, List, Annotated, Tuple
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
# from services.calendar_service import CalendarService
from services.notion_service import NotionService
from book_api import OpenLibraryService

import logging
logging.basicConfig(level=logging.INFO)

# Initialize services
book_service = OpenLibraryService()
# calendar_service = CalendarService()
notion_service = NotionService()

# State management


class AgentState:
    def __init__(self):
        self.current_book = None
        self.last_recommendations = []
        self.chat_history = []


# Intent detection prompt
intent_prompt = ChatPromptTemplate.from_messages([
    MessagesPlaceholder(variable_name="chat_history"),
    ("system", """You are an AI reading assistant that helps users discover books and journal their thoughts.
    Analyze the user's message and determine their intent. The possible intents are:
    1. RECOMMEND - User wants book recommendations
    2. JOURNAL - User wants to write/record thoughts about a book
    3. UNKNOWN - Cannot determine the intent

    Also extract any relevant parameters like:
    - genres (for recommendations)
    - book selection (index of book from last recommendations)
    
    Output format:
    {{
        "intent": "RECOMMEND|JOURNAL|UNKNOWN",
        "params": {{
            "genres": ["fiction", "mystery"],  // for RECOMMEND
            "book_index": 0,  // index of selected book
            "reflection": ""  // for JOURNAL
        }}
    }}"""),
    ("human", "{input}")
])

# Action execution prompt
action_prompt = ChatPromptTemplate.from_messages([
    MessagesPlaceholder(variable_name="chat_history"),
    ("system", """You are an AI reading assistant. Based on the detected intent and parameters, 
    format a natural, friendly response to the user. Include relevant details from the action results.
    
    For recommendations, list each book with its title, author, and a brief description.
    For journaling, confirm the creation of the Notion page and provide the link."""),
    ("human", "{input}"),
    ("assistant", "{action_result}")
])

# Initialize LangChain chat model
model = ChatOpenAI(model="gpt-4.1-nano", temperature=0)

# Intent detection node


def detect_intent(state: Dict) -> Dict:
    """Detect user intent using LLM."""
    messages = intent_prompt.format_messages(
        chat_history=state.get("chat_history", []),
        input=state["user_input"]
    )
    response = model.invoke(messages)
    intent_data = JsonOutputParser().parse(response.content)
    return {"intent_data": intent_data}

# Action execution nodes


def recommend_books(state: Dict) -> Dict:
    """Get book recommendations based on genres."""
    genres = state["intent_data"]["params"].get("genres", ["fiction"])

    recommendations = []
    for genre in genres:
        genre_books = book_service.get_books_by_genre(genre)
        recommendations.extend(genre_books)

    # Limit total recommendations
    recommendations = recommendations[:5]

    state["last_recommendations"] = recommendations
    state["action_result"] = {
        "status": "success",
        "recommendations": recommendations,
        "message": f"Here are some {', '.join(genres)} books you might enjoy!"
    }
    return state

# def schedule_reading(state: Dict) -> Dict:
#     """Schedule reading time in calendar."""
#     if not state.get("last_recommendations"):
#         state["action_result"] = {
#             "status": "error",
#             "message": "Please get book recommendations first!"
#         }
#         return state

#     duration = state["intent_data"]["params"].get("duration", 30)
#     book_index = state["intent_data"]["params"].get("book_index", 0)
#     book = state["last_recommendations"][book_index]

#     result = calendar_service.schedule_reading_time(book, duration)
#     if result["status"] == "success":
#         state["current_book"] = book

#     state["action_result"] = result
#     return state


def create_journal(state: Dict) -> Dict:
    """Create journal entry in Notion."""
    if not state.get("current_book") and not state.get("last_recommendations"):
        state["action_result"] = {
            "status": "error",
            "message": "Please select a book first!"
        }
        return state

    book = state.get("current_book") or state["last_recommendations"][0]
    reflection = state["intent_data"]["params"].get("reflection", "")

    # Create Notion page
    result = notion_service.create_book_page(book)
    state["action_result"] = result
    return state

# Response formatting node


def format_response(state: Dict) -> Dict:
    """Format the final response to the user."""
    messages = action_prompt.format_messages(
        chat_history=list(state.get("chat_history", [])),
        input=state["user_input"],
        action_result=state["action_result"]
    )
    response = model.invoke(messages)

    return {
        "final_response": response.content,
        **state
    }


# Main processing node


def process_request(state: Dict) -> Dict:
    """Process the request based on detected intent."""
    intent = state["intent_data"]["intent"]

    if intent == "RECOMMEND":
        return recommend_books(state)
    # elif intent == "SCHEDULE":
    #     return schedule_reading(state)
    elif intent == "JOURNAL":
        return create_journal(state)
    else:
        state["action_result"] = {
            "status": "error",
            "message": "I'm not sure what you want to do. Try asking for a book recommendation or creating a journal entry!"
        }
        return state
