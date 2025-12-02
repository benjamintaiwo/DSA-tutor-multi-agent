import asyncio
from tools.leetcode_mcp import LeetCodeToolMCP, LeetCodeProblemRequest

async def test_leetcode():
    print("Testing LeetCode Tool (Direct GraphQL)...")
    tool = LeetCodeToolMCP() # No MCP URL, should use direct fallback
    
    # Test 1: Fetch specific problem
    print("\n1. Fetching 'two-sum'...")
    try:
        request = LeetCodeProblemRequest(slug="two-sum")
        result = await tool.get_problem_async(request)
        print(f"✓ Success! Length of result: {len(result)}")
        print(f"Preview: {result[:100]}...")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 2: Fetch random problem
    print("\n2. Fetching random problem...")
    try:
        result = await tool.get_random_problem_async()
        print(f"✓ Success! Length of result: {len(result)}")
        print(f"Preview: {result[:100]}...")
    except Exception as e:
        print(f"✗ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_leetcode())
