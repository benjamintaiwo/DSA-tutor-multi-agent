import json
import asyncio
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

class DifficultyLevel(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

class LeetCodeProblemRequest(BaseModel):
    """Validation schema for LeetCode problem requests."""
    slug: Optional[str] = Field(None, description="Problem slug (e.g., 'two-sum')")
    difficulty: Optional[DifficultyLevel] = Field(None, description="Filter by difficulty")
    
    @validator('slug')
    def validate_slug(cls, v):
        if v and not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Invalid slug format")
        return v.lower() if v else v

class LeetCodeToolMCP:
    """
    A tool to fetch LeetCode problems using MCP (Model Context Protocol).
    Includes async support, error handling, and validation schemas.
    """

    def __init__(self, mcp_server_url: Optional[str] = None):
        self.mcp_server_url = mcp_server_url
        self.use_mcp = mcp_server_url is not None
        
        # Fallback to direct GraphQL if MCP not available
        if not self.use_mcp:
            self.base_url = "https://leetcode.com/graphql"
            self.headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://leetcode.com/"
            }

    async def _fetch_via_mcp(self, slug: str) -> Dict[str, Any]:
        """Fetch problem via MCP server (async)."""
        try:
            # In a real implementation, this would use the MCP client library
            # For now, we'll simulate the MCP call
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "method": "tools/call",
                    "params": {
                        "name": "get_leetcode_problem",
                        "arguments": {"slug": slug}
                    }
                }
                
                async with session.post(self.mcp_server_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("result", {})
                    else:
                        raise Exception(f"MCP server returned status {response.status}")
                        
        except Exception as e:
            raise Exception(f"MCP fetch failed: {str(e)}")

    async def _fetch_via_graphql(self, slug: str) -> Dict[str, Any]:
        """Fetch problem via direct GraphQL (async wrapper around requests)."""
        import requests
        
        query = """
        query getQuestionDetail($titleSlug: String!) {
          question(titleSlug: $titleSlug) {
            questionId
            title
            difficulty
            content
            topicTags {
              name
            }
            codeSnippets {
              lang
              code
            }
            sampleTestCase
            hints
          }
        }
        """
        
        payload = {
            "query": query,
            "variables": {"titleSlug": slug}
        }
        
        def _sync_fetch():
            response = requests.post(
                self.base_url, 
                json=payload, 
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                question = data.get("data", {}).get("question")
                
                if not question:
                    raise ValueError(f"Problem '{slug}' not found on LeetCode")
                    
                return {
                    "title": question["title"],
                    "difficulty": question["difficulty"],
                    "category": [tag["name"] for tag in question.get("topicTags", [])],
                    "description": question["content"],
                    "hints": question.get("hints", []),
                    "constraints": question.get("constraints", "See description"),
                    "examples": question.get("sampleTestCase")
                }
            else:
                print(f"[DEBUG] API Error Response: {response.text}")
                raise Exception(f"GraphQL API returned status {response.status_code}")

        # Run synchronous requests in a separate thread to avoid blocking event loop
        return await asyncio.to_thread(_sync_fetch)

    async def get_problem_async(self, request: LeetCodeProblemRequest) -> str:
        """
        Async method to fetch a problem with validation and error handling.
        
        Args:
            request: Validated request object
            
        Returns:
            JSON string with problem details
            
        Raises:
            ValueError: Invalid input
            Exception: Network or API errors
        """
        try:
            if not request.slug:
                # Get random problem if no slug provided
                import random
                popular_slugs = ["two-sum", "reverse-linked-list", "valid-parentheses", 
                               "merge-two-sorted-lists", "maximum-subarray"]
                slug = random.choice(popular_slugs)
            else:
                slug = request.slug
            
            # Try MCP first, fallback to GraphQL
            if self.use_mcp:
                try:
                    result = await self._fetch_via_mcp(slug)
                except Exception as mcp_error:
                    print(f"[LeetCodeTool] MCP failed, falling back to GraphQL: {mcp_error}")
                    result = await self._fetch_via_graphql(slug)
            else:
                result = await self._fetch_via_graphql(slug)
            
            return json.dumps(result, indent=2)
            
        except ValueError as ve:
            return json.dumps({"error": f"Validation error: {str(ve)}"})
        except Exception as e:
            return json.dumps({"error": f"Failed to fetch problem: {str(e)}"})

    async def get_random_problem_async(self) -> str:
        """Async method to fetch a random problem."""
        request = LeetCodeProblemRequest(slug=None)
        return await self.get_problem_async(request)

    def get_problem(self, slug: str = "") -> str:
        """
        Synchronous wrapper for compatibility.
        """
        request = LeetCodeProblemRequest(slug=slug if slug else None)
        
        # Run async function in sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.get_problem_async(request))

    def get_random_problem(self) -> str:
        """Returns a random problem."""
        return self.get_problem("")
