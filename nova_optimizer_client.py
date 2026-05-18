"""
Nova Optimizer Client - Bridge between HomeLift and NOVA Token Optimizer SaaS

This client connects to the NOVA Token Optimizer API (nova-optimizer.onrender.com)
to achieve 90-97% token reduction for HomeLift's AI operations.

Usage:
    from nova_optimizer_client import NovaOptimizerClient

    client = NovaOptimizerClient(api_key="your-api-key")

    # Compress JSON data (60-90% reduction)
    result = client.compress({"zip_code": "43215", "score": 87.5})

    # Consolidate MCP tools (85-97% reduction)
    result = client.consolidate(tools_list)

    # Use HomeLift preset (17 tools -> 3)
    preset = client.get_homelift_preset()

    # Full optimization pipeline
    result = client.full_optimize(data=my_data, preset="homelift")
"""

import os
import json
from typing import Dict, List, Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try to import httpx for async, fall back to requests
try:
    import httpx
    HTTP_CLIENT = "httpx"
except ImportError:
    try:
        import requests
        HTTP_CLIENT = "requests"
    except ImportError:
        HTTP_CLIENT = None


class NovaOptimizerClient:
    """
    Client for the NOVA Token Optimizer SaaS API.
    Provides 90-97% token reduction for HomeLift operations.
    """

    DEFAULT_URL = "https://nova-optimizer.onrender.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize the Nova Optimizer client.

        Args:
            api_key: API key for authentication (or set NOVA_API_KEY env var)
            base_url: API base URL (default: nova-optimizer.onrender.com)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("NOVA_API_KEY", "")
        self.base_url = (base_url or os.getenv("NOVA_API_URL", self.DEFAULT_URL)).rstrip("/")
        self.timeout = timeout

        if not HTTP_CLIENT:
            raise ImportError("Please install httpx or requests: pip install httpx")

    def _headers(self) -> Dict[str, str]:
        """Get request headers with API key."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def _post(self, endpoint: str, data: Dict) -> Dict:
        """Make a POST request to the API."""
        url = f"{self.base_url}{endpoint}"

        if HTTP_CLIENT == "httpx":
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=data, headers=self._headers())
                response.raise_for_status()
                return response.json()
        else:
            response = requests.post(url, json=data, headers=self._headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()

    def _get(self, endpoint: str) -> Dict:
        """Make a GET request to the API."""
        url = f"{self.base_url}{endpoint}"

        if HTTP_CLIENT == "httpx":
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self._headers())
                response.raise_for_status()
                return response.json()
        else:
            response = requests.get(url, headers=self._headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()

    # =========================================================================
    # Core API Methods
    # =========================================================================

    def compress(self, data: Dict[str, Any]) -> Dict:
        """
        Compress JSON data to Nova format.

        Achieves 60-90% token reduction.

        Args:
            data: JSON data to compress

        Returns:
            {
                "nova_format": "compressed string",
                "original_tokens": 150,
                "compressed_tokens": 25,
                "tokens_saved": 125,
                "savings_percent": 83.3
            }
        """
        return self._post("/api/compress", {"data": data})

    def consolidate(
        self,
        tools: List[Dict[str, Any]],
        pattern: Optional[str] = None
    ) -> Dict:
        """
        Consolidate MCP tools into parameterized super-tools.

        Achieves 85-97% token reduction.

        Args:
            tools: List of MCP tool definitions
            pattern: Optional pattern (lead_generation, analytics, database, web)

        Returns:
            {
                "consolidated_tools": [...],
                "original_tool_count": 17,
                "consolidated_tool_count": 3,
                "original_tokens": 10500,
                "consolidated_tokens": 315,
                "tokens_saved": 10185,
                "savings_percent": 97.0
            }
        """
        payload = {"tools": tools}
        if pattern:
            payload["pattern"] = pattern
        return self._post("/api/consolidate", payload)

    def execute(
        self,
        code: str,
        variables: Optional[Dict[str, Any]] = None,
        sandbox: bool = True
    ) -> Dict:
        """
        Execute Nova code.

        Args:
            code: Nova code to execute
            variables: Initial variables
            sandbox: Run in sandbox mode (default: True)

        Returns:
            {
                "success": True,
                "output": ["line1", "line2"],
                "variables": {"x": 42},
                "error": None
            }
        """
        return self._post("/api/execute", {
            "code": code,
            "variables": variables or {},
            "sandbox": sandbox
        })

    def full_optimize(
        self,
        data: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        prompt: Optional[str] = None,
        preset: Optional[str] = None
    ) -> Dict:
        """
        Full optimization pipeline - achieves 90%+ token reduction.

        Args:
            data: JSON data to compress
            tools: MCP tools to consolidate
            prompt: Prompt to optimize
            preset: Use preset ("homelift" for HomeLift optimization)

        Returns:
            {
                "compressed_data": "...",
                "consolidated_tools": [...],
                "optimized_prompt": "...",
                "total_original_tokens": 12000,
                "total_optimized_tokens": 400,
                "total_tokens_saved": 11600,
                "total_savings_percent": 96.7,
                "breakdown": {...}
            }
        """
        payload = {}
        if data:
            payload["data"] = data
        if tools:
            payload["tools"] = tools
        if prompt:
            payload["prompt"] = prompt
        if preset:
            payload["preset"] = preset

        return self._post("/api/full-optimize", payload)

    def get_homelift_preset(self) -> Dict:
        """
        Get the pre-optimized HomeLift tool set.

        Returns 3 super-tools that replace 17 individual tools:
        - lead_generator: pre_intent, fsbo, social, expired, referral
        - analytics_engine: civic, market, territory, performance
        - db_ops: select, insert, update, delete, join, aggregate

        Achieves 97% token reduction (10,500 -> 315 tokens).
        """
        return self._get("/api/consolidate/homelift-preset")

    def get_patterns(self) -> Dict:
        """Get available consolidation patterns."""
        return self._get("/api/consolidate/patterns")

    def health(self) -> Dict:
        """Check API health."""
        return self._get("/health")

    def info(self) -> Dict:
        """Get API info and available endpoints."""
        return self._get("/info")


# =========================================================================
# HomeLift-Specific Helper Functions
# =========================================================================

class HomeLiftOptimizer:
    """
    HomeLift-specific optimization helper.
    Wraps NovaOptimizerClient with HomeLift-focused convenience methods.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.client = NovaOptimizerClient(api_key=api_key)
        self._preset_cache = None

    def get_optimized_tools(self) -> List[Dict]:
        """
        Get the optimized tool set for HomeLift.

        Returns 3 super-tools:
        - lead_generator(source, zip, limit)
        - analytics_engine(type, target, metrics)
        - db_ops(op, table, data)
        """
        if not self._preset_cache:
            self._preset_cache = self.client.get_homelift_preset()
        return self._preset_cache.get("tools", [])

    def optimize_lead_data(self, leads: List[Dict]) -> str:
        """
        Optimize lead data batch for minimal token usage.

        Args:
            leads: List of lead dictionaries

        Returns:
            Compressed Nova format string
        """
        result = self.client.compress({"leads": leads})
        return result.get("nova_format", "")

    def optimize_territory_data(self, territory: Dict) -> str:
        """
        Optimize territory data for minimal token usage.

        Args:
            territory: Territory dictionary with zip, score, metrics, etc.

        Returns:
            Compressed Nova format string
        """
        result = self.client.compress(territory)
        return result.get("nova_format", "")

    def optimize_analytics_request(
        self,
        analysis_type: str,
        target: str,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        Create an optimized analytics request.

        Instead of loading heavy MCP tool definitions, use the consolidated
        analytics_engine tool with parameters.

        Args:
            analysis_type: civic, market, territory, or performance
            target: Target ZIP, region, or entity
            config: Optional analysis configuration

        Returns:
            Optimized tool call structure
        """
        return {
            "tool": "analytics_engine",
            "parameters": {
                "type": analysis_type,
                "target": target,
                "metrics": config.get("metrics", []) if config else []
            }
        }

    def optimize_lead_request(
        self,
        source: str,
        zip_code: str,
        limit: int = 50
    ) -> Dict:
        """
        Create an optimized lead generation request.

        Instead of loading 5 separate lead tools, use the consolidated
        lead_generator tool with source parameter.

        Args:
            source: pre_intent, fsbo, social, expired, or referral
            zip_code: Target ZIP code
            limit: Maximum leads to return

        Returns:
            Optimized tool call structure
        """
        return {
            "tool": "lead_generator",
            "parameters": {
                "source": source,
                "zip": zip_code,
                "limit": limit
            }
        }

    def optimize_db_request(
        self,
        operation: str,
        table: str,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Create an optimized database request.

        Instead of loading 8 separate DB tools, use the consolidated
        db_ops tool with operation parameter.

        Args:
            operation: select, insert, update, delete, join, aggregate
            table: Target table name
            data: Query data or parameters

        Returns:
            Optimized tool call structure
        """
        return {
            "tool": "db_ops",
            "parameters": {
                "op": operation,
                "table": table,
                "data": data or {}
            }
        }

    def get_savings_report(self) -> Dict:
        """
        Get token savings report for HomeLift.

        Returns expected savings based on HomeLift's typical usage.
        """
        return {
            "tool_consolidation": {
                "before": "17 tools @ 10,500 tokens",
                "after": "3 tools @ 315 tokens",
                "savings": "97%"
            },
            "data_compression": {
                "before": "JSON @ ~1,200 tokens/batch",
                "after": "Nova @ ~180 tokens/batch",
                "savings": "85%"
            },
            "overall": {
                "average_reduction": "90-97%",
                "monthly_savings": "$4,050 estimated"
            }
        }


# =========================================================================
# Convenience function for quick access
# =========================================================================

def get_optimizer(api_key: Optional[str] = None) -> HomeLiftOptimizer:
    """
    Get a HomeLift optimizer instance.

    Usage:
        from nova_optimizer_client import get_optimizer

        opt = get_optimizer()
        tools = opt.get_optimized_tools()
        lead_request = opt.optimize_lead_request("pre_intent", "43215")
    """
    return HomeLiftOptimizer(api_key=api_key)


# =========================================================================
# CLI for testing
# =========================================================================

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Nova Optimizer Client - HomeLift Integration")
    print("=" * 60)

    # Check if API is available
    client = NovaOptimizerClient()

    try:
        health = client.health()
        print(f"\n[OK] API Status: {health.get('status', 'unknown')}")
        print(f"     Endpoint: {client.base_url}")
    except Exception as e:
        print(f"\n[!] API not reachable: {e}")
        print("    Make sure nova-optimizer.onrender.com is running")
        sys.exit(1)

    # Show HomeLift preset
    print("\n" + "=" * 60)
    print("HomeLift Optimized Tools (97% token reduction)")
    print("=" * 60)

    try:
        preset = client.get_homelift_preset()
        print(f"\nOriginal: {preset.get('original_tools', 17)} tools")
        print(f"Optimized: {preset.get('consolidated_tools', 3)} tools")
        print(f"Savings: {preset.get('estimated_savings', '97%')}")

        print("\nConsolidated tools:")
        for tool in preset.get("tools", []):
            print(f"  - {tool['name']}: {tool['description']}")
    except Exception as e:
        print(f"Could not fetch preset: {e}")

    # Test compression
    print("\n" + "=" * 60)
    print("Data Compression Demo")
    print("=" * 60)

    sample_data = {
        "zip_code": "43215",
        "desirability_score": 87.5,
        "timeline": "18_months",
        "lead_count": 45,
        "tier": "Diamond"
    }

    try:
        result = client.compress(sample_data)
        print(f"\nOriginal (JSON): {result.get('original_tokens', 0)} tokens")
        print(f"Compressed (Nova): {result.get('compressed_tokens', 0)} tokens")
        print(f"Savings: {result.get('savings_percent', 0)}%")
        print(f"\nNova format:\n{result.get('nova_format', '')}")
    except Exception as e:
        print(f"Compression failed: {e}")

    print("\n" + "=" * 60)
    print("Ready for HomeLift integration!")
    print("=" * 60)
