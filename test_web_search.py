#!/usr/bin/env python3
"""
Test script for web search functionality.
This script extracts and tests the web search logic from agent_gemini.py
without LiveKit dependencies.
"""

from dotenv import load_dotenv
import os
from datetime import datetime
import time
import asyncio

from mistralai import Mistral
from loguru import logger

# Load environment variables
load_dotenv()

# Configure loguru logging with daily rotation
logger.remove()  # Remove default handler
logger.add(
    "logs/{time:YYYY-MM-DD}_test_data.log",
    rotation="00:00",  # Rotate at midnight
    retention="30 days",  # Keep logs for 30 days
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    level="INFO",
    serialize=True  # JSON format for structured logging
)

# Add console output for testing
logger.add(
    lambda msg: print(msg),
    format="{time:HH:mm:ss} | {level: <8} | {message}",
    level="INFO"
)


async def test_web_search(query: str, session_id: str = "test_session"):
    """
    Test web search functionality extracted from agent_gemini.py
    """
    
    start_time = time.time()
    
    logger.info("Web search test initiated", extra={
        "query": query,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "function": "test_web_search"
    })
    
    try:
        # Get Mistral API key from environment
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            logger.error("Mistral API key not configured", extra={
                "query": query,
                "session_id": session_id,
                "error": "missing_api_key"
            })
            return {"error": "Mistral API key not configured"}
        
        logger.debug("API key validation successful", extra={
            "session_id": session_id,
            "has_api_key": True
        })
        
        # Initialize Mistral client
        client = Mistral(api_key=api_key)
        logger.debug("Mistral client initialized", extra={"session_id": session_id})
        
        # Create a temporary agent with web search capability
        search_agent = client.beta.agents.create(
            model="mistral-medium-2505",
            description="Agent able to search information over the web",
            name="Web Search Test Agent",
            instructions="You have the ability to perform web searches to find up-to-date information. Provide concise, accurate answers suitable for voice responses.",
            tools=[{"type": "web_search"}],
            completion_args={
                "temperature": 0.3,
                "top_p": 0.95,
            }
        )
        
        logger.info("Search agent created", extra={
            "agent_id": search_agent.id,
            "session_id": session_id,
            "query": query
        })
        
        # Perform the search
        search_start = time.time()
        response = client.beta.conversations.start(
            agent_id=search_agent.id,
            inputs=[{"role": "user", "content": query}]
        )
        search_duration = time.time() - search_start
        
        # Extract the search result
        result = response.model_dump()['outputs'][1]['content'][0]['text']
        result_length = len(result)
        
        logger.info("Search completed successfully", extra={
            "query": query,
            "session_id": session_id,
            "agent_id": search_agent.id,
            "search_duration_seconds": round(search_duration, 3),
            "result_length_chars": result_length,
            "result_preview": result[:100] + "..." if len(result) > 100 else result
        })
        
        # Clean up the temporary agent
        try:
            client.beta.agents.delete(agent_id=search_agent.id)
            logger.debug("Search agent cleanup successful", extra={
                "agent_id": search_agent.id,
                "session_id": session_id
            })
        except Exception as cleanup_error:
            logger.warning("Agent cleanup failed", extra={
                "agent_id": search_agent.id,
                "session_id": session_id,
                "cleanup_error": str(cleanup_error)
            })
        
        total_duration = time.time() - start_time
        logger.info("Web search test completed", extra={
            "query": query,
            "session_id": session_id,
            "total_duration_seconds": round(total_duration, 3),
            "success": True
        })
        
        return {"result": result, "duration": total_duration, "success": True}
        
    except Exception as e:
        total_duration = time.time() - start_time
        logger.error("Web search test failed with exception", extra={
            "query": query,
            "session_id": session_id,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "total_duration_seconds": round(total_duration, 3),
            "success": False
        })
        return {"error": f"Web search failed: {str(e)}", "duration": total_duration, "success": False}


async def run_tests():
    """
    Run multiple test cases to verify web search functionality
    """
    print("🚀 Starting web search functionality tests...\n")
    
    test_queries = [
        "Give me updated information about Indian cricket match?",
        "Latest news about artificial intelligence",
    ]
    
    results = []
    import time
    for i, query in enumerate(test_queries, 1):
        print(f"📝 Test {i}/{len(test_queries)}: {query}")
        print("-" * 50)
        time.sleep(5)
        result = await test_web_search(query, f"test_session_{i}")
        results.append(result)
        
        if result.get("success"):
            print(f"✅ SUCCESS: {result['result'][:200]}{'...' if len(result['result']) > 200 else ''}")
            print(f"⏱️  Duration: {result['duration']:.2f}s")
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
            print(f"⏱️  Duration: {result['duration']:.2f}s")
        
        print("\n" + "="*60 + "\n")
        
        # Add a small delay between tests
        await asyncio.sleep(1)
    
    # Summary
    successful_tests = sum(1 for r in results if r.get("success"))
    total_tests = len(results)
    
    print(f"📊 TEST SUMMARY:")
    print(f"   Total tests: {total_tests}")
    print(f"   Successful: {successful_tests}")
    print(f"   Failed: {total_tests - successful_tests}")
    print(f"   Success rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests == total_tests:
        print("🎉 All tests passed! Web search functionality is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs for details.")


if __name__ == "__main__":
    print("🔍 Web Search Functionality Test")
    print("=" * 40)
    
    # Check if API key is available
    if not os.getenv("MISTRAL_API_KEY"):
        print("❌ ERROR: MISTRAL_API_KEY not found in environment variables")
        print("Please add your Mistral API key to the .env file:")
        print("MISTRAL_API_KEY=your_api_key_here")
        exit(1)
    
    print("✅ API key found, starting tests...\n")
    
    # Run the tests
    asyncio.run(run_tests())