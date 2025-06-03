"""
Evaluation framework for CapyRead ReAct Agent
"""

import asyncio
import json
from typing import List, Dict, Any
from langsmith import Client
from langsmith.evaluation import evaluate
from langsmith.schemas import Run, Example
import logging

logger = logging.getLogger(__name__)

class CapyReadEvaluator:
    """Evaluator for CapyRead agent performance"""
    
    def __init__(self, langsmith_client: Client):
        self.client = langsmith_client
        
    def create_evaluation_dataset(self) -> str:
        """Create evaluation dataset with test cases"""
        dataset_name = "capyread-agent-eval"
        
        test_cases = [
            # Book recommendation tests
            {
                "inputs": {"user_input": "Recommend me some science fiction books"},
                "outputs": {"expected_action": "book_recommendation", "expected_genre": "science fiction"},
                "metadata": {"category": "book_recommendation", "difficulty": "easy"}
            },
            {
                "inputs": {"user_input": "I want mystery books with rating above 4.5"},
                "outputs": {"expected_action": "book_recommendation", "expected_genre": "mystery", "min_rating": 4.5},
                "metadata": {"category": "book_recommendation", "difficulty": "medium"}
            },
            
            # Calendar scheduling tests
            {
                "inputs": {"user_input": "Schedule 45 minutes to read Dune tomorrow at 2pm"},
                "outputs": {"expected_action": "schedule_reading", "book_title": "Dune", "duration": 45},
                "metadata": {"category": "calendar_scheduling", "difficulty": "medium"}
            },
            {
                "inputs": {"user_input": "I want to read for 30 minutes today"},
                "outputs": {"expected_action": "schedule_reading", "duration": 30},
                "metadata": {"category": "calendar_scheduling", "difficulty": "easy"}
            },
            
            # Book review tests
            {
                "inputs": {"user_input": "I just finished reading The Martian and I loved it! It was an amazing sci-fi novel with great humor and science."},
                "outputs": {"expected_action": "create_review", "book_title": "The Martian", "sentiment": "positive"},
                "metadata": {"category": "book_review", "difficulty": "medium"}
            },
            {
                "inputs": {"user_input": "Create a review for 1984 by George Orwell. Rating: 5/5. It's a masterpiece of dystopian fiction."},
                "outputs": {"expected_action": "create_review", "book_title": "1984", "author": "George Orwell", "rating": 5},
                "metadata": {"category": "book_review", "difficulty": "easy"}
            },
            
            # General conversation tests
            {
                "inputs": {"user_input": "What's your favorite book?"},
                "outputs": {"expected_action": "conversation", "topic": "books"},
                "metadata": {"category": "conversation", "difficulty": "easy"}
            },
            {
                "inputs": {"user_input": "How can reading help improve my vocabulary?"},
                "outputs": {"expected_action": "conversation", "topic": "reading_benefits"},
                "metadata": {"category": "conversation", "difficulty": "medium"}
            },
            
            # Edge cases
            {
                "inputs": {"user_input": "asdfghjkl"},
                "outputs": {"expected_action": "conversation", "should_ask_clarification": True},
                "metadata": {"category": "edge_case", "difficulty": "hard"}
            },
            {
                "inputs": {"user_input": "Book calendar review schedule notion"},
                "outputs": {"expected_action": "conversation", "should_ask_clarification": True},
                "metadata": {"category": "edge_case", "difficulty": "hard"}
            }
        ]
        
        try:
            # Create dataset
            dataset = self.client.create_dataset(
                dataset_name=dataset_name,
                description="Evaluation dataset for CapyRead ReAct Agent"
            )
            
            # Add examples to dataset
            for case in test_cases:
                self.client.create_example(
                    inputs=case["inputs"],
                    outputs=case["outputs"],
                    metadata=case["metadata"],
                    dataset_id=dataset.id
                )
            
            logger.info(f"Created evaluation dataset: {dataset_name}")
            return dataset.id
            
        except Exception as e:
            logger.error(f"Error creating evaluation dataset: {e}")
            return None

def evaluate_action_classification(run: Run, example: Example) -> Dict[str, Any]:
    """Evaluate if the agent correctly classified the user intent"""
    try:
        outputs = run.outputs or {}
        expected = example.outputs or {}
        
        # Extract actual action from agent response
        actual_action = outputs.get("action", "unknown")
        expected_action = expected.get("expected_action", "")
        
        # Check if action matches
        action_correct = actual_action == expected_action
        
        score = 1.0 if action_correct else 0.0
        
        return {
            "key": "action_classification",
            "score": score,
            "explanation": f"Expected: {expected_action}, Got: {actual_action}",
            "metadata": {
                "expected_action": expected_action,
                "actual_action": actual_action,
                "correct": action_correct
            }
        }
    except Exception as e:
        return {
            "key": "action_classification",
            "score": 0.0,
            "explanation": f"Evaluation error: {str(e)}"
        }

def evaluate_response_quality(run: Run, example: Example) -> Dict[str, Any]:
    """Evaluate the overall quality of the agent response"""
    try:
        outputs = run.outputs or {}
        response = outputs.get("response", "")
        
        # Check response length (should be substantive but not too long)
        length_score = 0.0
        if 10 <= len(response.split()) <= 200:
            length_score = 1.0
        elif 5 <= len(response.split()) <= 300:
            length_score = 0.5
        
        # Check if response is helpful (contains keywords related to the task)
        helpfulness_score = 0.0
        category = example.metadata.get("category", "")
        
        if category == "book_recommendation" and any(word in response.lower() for word in ["book", "recommend", "author", "genre"]):
            helpfulness_score = 1.0
        elif category == "calendar_scheduling" and any(word in response.lower() for word in ["schedule", "calendar", "time", "reading"]):
            helpfulness_score = 1.0
        elif category == "book_review" and any(word in response.lower() for word in ["review", "notion", "thoughts", "rating"]):
            helpfulness_score = 1.0
        elif category == "conversation":
            helpfulness_score = 1.0  # Give benefit of doubt for conversation
        
        overall_score = (length_score + helpfulness_score) / 2
        
        return {
            "key": "response_quality",
            "score": overall_score,
            "explanation": f"Length: {length_score}, Helpfulness: {helpfulness_score}",
            "metadata": {
                "response_length": len(response.split()),
                "category": category,
                "length_score": length_score,
                "helpfulness_score": helpfulness_score
            }
        }
    except Exception as e:
        return {
            "key": "response_quality", 
            "score": 0.0,
            "explanation": f"Evaluation error: {str(e)}"
        }

def evaluate_tool_usage(run: Run, example: Example) -> Dict[str, Any]:
    """Evaluate if the agent used tools appropriately"""
    try:
        outputs = run.outputs or {}
        expected = example.outputs or {}
        
        # Check if tools were used when expected
        tools_used = outputs.get("tools_used", [])
        expected_action = expected.get("expected_action", "")
        
        tool_usage_correct = True
        explanation = "Tool usage appropriate"
        
        # Define expected tool usage patterns
        if expected_action == "book_recommendation":
            if "book_recommendation" not in str(tools_used):
                tool_usage_correct = False
                explanation = "Should have used book recommendation tool"
        elif expected_action == "schedule_reading":
            if "schedule_reading" not in str(tools_used):
                tool_usage_correct = False
                explanation = "Should have used calendar scheduling tool"
        elif expected_action == "create_review":
            if "create_review" not in str(tools_used):
                tool_usage_correct = False
                explanation = "Should have used Notion review tool"
        
        score = 1.0 if tool_usage_correct else 0.0
        
        return {
            "key": "tool_usage",
            "score": score,
            "explanation": explanation,
            "metadata": {
                "tools_used": tools_used,
                "expected_action": expected_action,
                "correct": tool_usage_correct
            }
        }
    except Exception as e:
        return {
            "key": "tool_usage",
            "score": 0.0,
            "explanation": f"Evaluation error: {str(e)}"
        }

async def run_evaluation(agent, dataset_id: str, langsmith_client: Client) -> Dict[str, Any]:
    """Run evaluation on the agent"""
    
    def agent_wrapper(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper function for the agent"""
        try:
            user_input = inputs.get("user_input", "")
            response = agent.run(user_input)
            
            return {
                "response": response,
                "action": getattr(agent, 'last_action', 'unknown'),
                "tools_used": getattr(agent, 'tools_used', [])
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "action": "error",
                "tools_used": []
            }
    
    # Run evaluation
    results = evaluate(
        agent_wrapper,
        data=dataset_id,
        evaluators=[
            evaluate_action_classification,
            evaluate_response_quality,
            evaluate_tool_usage
        ],
        experiment_prefix="capyread-agent",
        client=langsmith_client
    )
    
    return results

def analyze_evaluation_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze evaluation results and provide insights"""
    summary = {
        "total_examples": len(results.get("examples", [])),
        "overall_score": 0.0,
        "category_scores": {},
        "evaluator_scores": {},
        "recommendations": []
    }
    
    if not results.get("examples"):
        return summary
    
    # Calculate scores by evaluator
    evaluators = ["action_classification", "response_quality", "tool_usage"]
    for evaluator in evaluators:
        scores = [ex.get(evaluator, {}).get("score", 0) for ex in results["examples"]]
        summary["evaluator_scores"][evaluator] = {
            "mean": sum(scores) / len(scores) if scores else 0,
            "count": len(scores)
        }
    
    # Calculate overall score
    all_scores = []
    for example in results["examples"]:
        example_scores = [example.get(eval_name, {}).get("score", 0) for eval_name in evaluators]
        all_scores.extend(example_scores)
    
    summary["overall_score"] = sum(all_scores) / len(all_scores) if all_scores else 0
    
    # Calculate scores by category
    categories = {}
    for example in results["examples"]:
        category = example.get("metadata", {}).get("category", "unknown")
        if category not in categories:
            categories[category] = []
        
        example_scores = [example.get(eval_name, {}).get("score", 0) for eval_name in evaluators]
        categories[category].extend(example_scores)
    
    for category, scores in categories.items():
        summary["category_scores"][category] = sum(scores) / len(scores) if scores else 0
    
    # Generate recommendations
    if summary["evaluator_scores"]["action_classification"]["mean"] < 0.8:
        summary["recommendations"].append("Improve intent classification accuracy")
    
    if summary["evaluator_scores"]["response_quality"]["mean"] < 0.7:
        summary["recommendations"].append("Enhance response quality and helpfulness")
    
    if summary["evaluator_scores"]["tool_usage"]["mean"] < 0.8:
        summary["recommendations"].append("Improve tool selection and usage")
    
    if summary["category_scores"].get("book_recommendation", 0) < 0.8:
        summary["recommendations"].append("Focus on book recommendation accuracy")
    
    return summary