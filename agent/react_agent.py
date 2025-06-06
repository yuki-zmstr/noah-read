"""
ReAct Agent for CapyRead - A reasoning and acting agent that can:
1. Recommend books using OpenLibrary
2. Schedule reading time in Google Calendar 
3. Create book reviews in Notion
4. Handle general conversation
"""

from typing import Dict, List, Optional, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import json
import re
import os
import logging
from services.book_service import BookService
from services.calendar_service import CalendarService
from services.notion_service import NotionService

# Configure LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "capyread-react-agent"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentDecision(BaseModel):
    """Model for agent's reasoning and action decision"""
    thought: str = Field(description="The agent's reasoning about what to do")
    action: str = Field(
        description="The action to take: 'book_recommendation', 'schedule_reading', 'create_review', 'conversation', or 'FINAL_ANSWER'")
    action_input: str = Field(description="The input for the chosen action")


class ReActAgent:
    """ReAct (Reasoning and Acting) Agent for CapyRead"""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.book_service = BookService()
        self.calendar_service = CalendarService()
        self.notion_service = NotionService()
        self.parser = PydanticOutputParser(pydantic_object=AgentDecision)

        # Initialize tools
        self.tools = self._create_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}

        # ReAct prompt template
        self.react_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])

        # Conversation history
        self.chat_history: List[BaseMessage] = []

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the ReAct agent"""
        return """You are CapyRead, an AI reading assistant that helps users discover books, schedule reading time, and track their reading journey.

You have access to the following tools:
1. book_recommendation - Get book recommendations from OpenLibrary
2. schedule_reading - Schedule reading time in Google Calendar  
3. create_review - Create book review/notes in Notion
4. conversation - Handle general conversation

Use the ReAct (Reasoning and Acting) framework:
1. THOUGHT: Think about what the user wants and what action to take
2. ACTION: Choose an appropriate tool or provide final answer
3. OBSERVATION: Analyze the tool result
4. Repeat if needed, or provide FINAL_ANSWER

For each response, provide your reasoning in JSON format:
{
    "thought": "Your reasoning about what to do",
    "action": "tool_name or FINAL_ANSWER", 
    "action_input": "input for the tool or final response"
}

Guidelines:
- For book recommendations: Ask for genres/preferences if not specified
- For scheduling: Confirm book selection and get time preferences
- For reviews: Ask for book details and user's thoughts
- For general chat: Respond naturally as a helpful reading assistant
- Always be friendly and enthusiastic about reading!

Available tools:
{tools}

{format_instructions}
"""

    def _create_tools(self) -> List[Tool]:
        """Create the available tools for the agent"""
        return [
            Tool(
                name="book_recommendation",
                description="Get book recommendations based on genre, author, or preferences. Input should be a JSON string with 'query', 'genre', 'min_rating' (optional)",
                func=self._recommend_books
            ),
            Tool(
                name="schedule_reading",
                description="Schedule reading time in Google Calendar. Input should be a JSON string with 'book_title', 'duration_minutes', 'preferred_time' (optional)",
                func=self._schedule_reading
            ),
            Tool(
                name="create_review",
                description="Create a book review or reading notes in Notion. Input should be a JSON string with 'book_title', 'author', 'review_text', 'rating' (1-5)",
                func=self._create_review
            ),
            Tool(
                name="conversation",
                description="Handle general conversation about reading, books, or other topics. Input is the conversation text.",
                func=self._handle_conversation
            )
        ]

    def _recommend_books(self, input_str: str) -> str:
        """Tool for getting book recommendations"""
        try:
            params = json.loads(input_str)
            query = params.get("query", "")
            genre = params.get("genre", "")
            min_rating = params.get("min_rating", 4.0)

            if genre:
                books = self.book_service.get_books_by_genre(genre, min_rating)
            elif query:
                books = self.book_service.search_books(query)
            else:
                return "Please specify either a genre or search query for book recommendations."

            if not books:
                return f"No books found for '{genre or query}'. Try a different genre or search term."

            result = "Here are some book recommendations:\n\n"
            for i, book in enumerate(books[:5], 1):
                result += f"{i}. **{book['title']}** by {book['author']}\n"
                result += f"   Rating: {book['rating']}/5\n"
                result += f"   {book['description'][:150]}...\n"
                result += f"   [More info]({book['link']})\n\n"

            return result

        except Exception as e:
            return f"Error getting book recommendations: {str(e)}"

    def _schedule_reading(self, input_str: str) -> str:
        """Tool for scheduling reading time"""
        try:
            params = json.loads(input_str)
            book_title = params.get("book_title", "")
            duration = params.get("duration_minutes", 30)
            preferred_time = params.get("preferred_time", "")

            if not book_title:
                return "Please specify a book title to schedule reading time for."

            result = self.calendar_service.schedule_reading_session(
                book_title=book_title,
                duration_minutes=duration,
                preferred_time=preferred_time
            )

            if result["success"]:
                return f"✅ Scheduled {duration} minutes to read '{book_title}' at {result['scheduled_time']}"
            else:
                return f"❌ Failed to schedule reading time: {result['error']}"

        except Exception as e:
            return f"Error scheduling reading time: {str(e)}"

    def _create_review(self, input_str: str) -> str:
        """Tool for creating book reviews in Notion"""
        try:
            params = json.loads(input_str)
            book_title = params.get("book_title", "")
            author = params.get("author", "")
            review_text = params.get("review_text", "")
            rating = params.get("rating", 5)

            if not book_title:
                return "Please specify a book title for the review."

            result = self.notion_service.create_book_review(
                title=book_title,
                author=author,
                review=review_text,
                rating=rating
            )

            if result["success"]:
                return f"✅ Created review for '{book_title}' in Notion: {result['page_url']}"
            else:
                return f"❌ Failed to create review: {result['error']}"

        except Exception as e:
            return f"Error creating review: {str(e)}"

    def _handle_conversation(self, input_str: str) -> str:
        """Tool for general conversation"""
        conversation_prompt = f"""
        You are CapyRead, a friendly AI reading assistant. The user said: "{input_str}"
        
        Respond naturally and helpfully. If they're asking about books, reading, or related topics,
        provide enthusiastic and knowledgeable responses. If they need specific actions like
        book recommendations, scheduling, or reviews, guide them appropriately.
        """

        response = self.llm.invoke(
            [SystemMessage(content=conversation_prompt)])
        return response.content

    def _parse_agent_decision(self, text: str) -> AgentDecision:
        """Parse the agent's decision from LLM output"""
        # Try to extract JSON from the response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                decision_data = json.loads(json_match.group())
                logger.info(f"Parsed agent decision: {decision_data}")
                
                # Convert action_input to string if it's a dict/object
                if isinstance(decision_data.get('action_input'), (dict, list)):
                    decision_data['action_input'] = json.dumps(decision_data['action_input'])
                    
                return AgentDecision(**decision_data)
            except Exception as e:
                logger.error(f"Error parsing decision JSON: {e}")
                pass

        # Fallback parsing
        if "FINAL_ANSWER" in text:
            return AgentDecision(
                thought="Providing final answer",
                action="FINAL_ANSWER",
                action_input=text
            )
        else:
            return AgentDecision(
                thought="Handling general conversation",
                action="conversation",
                action_input=text
            )

    def run(self, user_input: str, max_iterations: int = 5) -> str:
        """Run the ReAct agent"""
        self.chat_history.append(HumanMessage(content=user_input))

        agent_scratchpad = ""

        for iteration in range(max_iterations):
            logger.info(f"iteration: {iteration}")
            # Format the prompt
            formatted_prompt = self.react_prompt.format(
                tools="\n".join(
                    [f"- {tool.name}: {tool.description}" for tool in self.tools]),
                format_instructions=self.parser.get_format_instructions(),
                # All except current input
                chat_history=self.chat_history[:-1],
                input=user_input,
                agent_scratchpad=agent_scratchpad
            )

            # Get LLM response
            response = self.llm.invoke(
                [HumanMessage(content=formatted_prompt)])
            logger.info(f"LLM response: {response.content}")

            # Parse the decision
            try:
                decision = self._parse_agent_decision(response.content)
            except Exception as e:
                # Fallback to conversation
                decision = AgentDecision(
                    thought=f"Error parsing decision: {e}",
                    action="conversation",
                    action_input=response.content
                )

            agent_scratchpad += f"Thought: {decision.thought}\n"

            # Check if final answer
            if decision.action == "FINAL_ANSWER":
                final_response = decision.action_input
                self.chat_history.append(AIMessage(content=final_response))
                return final_response

            # Execute the tool
            if decision.action in self.tool_map:
                tool = self.tool_map[decision.action]
                agent_scratchpad += f"Action: {decision.action}\n"
                agent_scratchpad += f"Action Input: {decision.action_input}\n"

                try:
                    logger.info(f"Executing tool: {decision.action}")
                    observation = tool.func(decision.action_input)
                    
                    # If it's a book recommendation and we got results successfully
                    if decision.action == "book_recommendation" and "Here are some book recommendations:" in observation:
                        self.chat_history.append(AIMessage(content=observation))
                        return observation
                        
                except Exception as e:
                    observation = f"Error: {str(e)}"

                agent_scratchpad += f"Observation: {observation}\n"
            else:
                # Unknown action, treat as conversation
                observation = self._handle_conversation(decision.action_input)
                self.chat_history.append(AIMessage(content=observation))
                return observation

        # If we reach max iterations, return the last observation
        fallback_response = "I apologize, but I'm having trouble processing your request. Could you please rephrase what you'd like me to help you with?"
        self.chat_history.append(AIMessage(content=fallback_response))
        return fallback_response

    def reset_conversation(self):
        """Reset the conversation history"""
        self.chat_history = []
