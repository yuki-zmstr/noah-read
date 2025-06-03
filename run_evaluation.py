#!/usr/bin/env python3
"""
Run evaluation on the CapyRead ReAct Agent
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from langsmith import Client
from agent.react_agent import ReActAgent
from agent.evaluations import CapyReadEvaluator, run_evaluation, analyze_evaluation_results

# Load environment variables
load_dotenv()

async def main():
    """Main evaluation runner"""
    print("🧪 Starting CapyRead Agent Evaluation...")
    
    # Initialize LangSmith client
    langsmith_client = Client()
    
    # Initialize evaluator
    evaluator = CapyReadEvaluator(langsmith_client)
    
    # Create evaluation dataset
    print("📊 Creating evaluation dataset...")
    dataset_id = evaluator.create_evaluation_dataset()
    
    if not dataset_id:
        print("❌ Failed to create evaluation dataset")
        return
    
    print(f"✅ Created dataset with ID: {dataset_id}")
    
    # Initialize agent
    print("🤖 Initializing ReAct agent...")
    agent = ReActAgent()
    
    # Run evaluation
    print("🔄 Running evaluation...")
    try:
        results = await run_evaluation(agent, dataset_id, langsmith_client)
        
        # Analyze results
        print("📈 Analyzing results...")
        analysis = analyze_evaluation_results(results)
        
        # Print results
        print("\n" + "="*50)
        print("📊 EVALUATION RESULTS")
        print("="*50)
        
        print(f"Total Examples: {analysis['total_examples']}")
        print(f"Overall Score: {analysis['overall_score']:.2%}")
        
        print("\n📋 Scores by Evaluator:")
        for evaluator_name, scores in analysis['evaluator_scores'].items():
            print(f"  {evaluator_name}: {scores['mean']:.2%}")
        
        print("\n📂 Scores by Category:")
        for category, score in analysis['category_scores'].items():
            print(f"  {category}: {score:.2%}")
        
        if analysis['recommendations']:
            print("\n💡 Recommendations:")
            for rec in analysis['recommendations']:
                print(f"  • {rec}")
        
        # Save detailed results
        results_file = "evaluation_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "analysis": analysis,
                "raw_results": results
            }, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())