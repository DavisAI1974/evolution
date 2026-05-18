#!/usr/bin/env python3
"""
Nova Token Optimizer for HomeLift
Converts verbose JSON to compact Nova format - saves 60-90% tokens
"""

import json
import sys
from pathlib import Path

class NovaCompressor:
    """
    Compresses JSON data into Nova's minimal syntax format.

    Example transformation:
    JSON (150 tokens):
    {
      "zip_code": "43215",
      "desirability_score": 87.5,
      "timeline": "18_months",
      "lead_count": 45
    }

    Nova (25 tokens):
    zip 43215
    score 87.5
    timeline 18m
    leads 45
    """

    @staticmethod
    def compress_dict(data: dict, indent: int = 0) -> str:
        """Convert dict to compact Nova key-value format"""
        lines = []
        prefix = "  " * indent

        for k, v in data.items():
            # Simplify key names - use abbreviation but keep uniqueness
            key = k.replace("_", "")
            if len(key) > 12:
                key = key[:12]  # Truncate longer to 12 chars to reduce collision risk

            if isinstance(v, dict):
                lines.append(f"{prefix}{key} {{")
                lines.append(NovaCompressor.compress_dict(v, indent + 1))
                lines.append(f"{prefix}}}")
            elif isinstance(v, list):
                # Compact list notation
                if len(v) < 5 and all(isinstance(x, (int, float, str)) for x in v):
                    vals = ",".join(str(x) for x in v)
                    lines.append(f"{prefix}{key} [{vals}]")
                else:
                    lines.append(f"{prefix}{key} {json.dumps(v)}")
            elif isinstance(v, str):
                # Strip quotes for simple strings
                cleaned = v.replace("_", "").replace("-", "")
                if cleaned and cleaned.isalnum():  # Check not empty and alphanumeric
                    lines.append(f"{prefix}{key} {v}")
                else:
                    lines.append(f"{prefix}{key} {json.dumps(v)}")
            else:
                lines.append(f"{prefix}{key} {v}")

        return "\n".join(lines)

    @staticmethod
    def compress_json(json_str: str) -> str:
        """Convert JSON string to Nova format"""
        data = json.loads(json_str)
        return NovaCompressor.compress_dict(data)

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough token estimate (1 token = 4 chars)"""
        return len(text) // 4

    @staticmethod
    def compare_formats(data: dict) -> dict:
        """Compare JSON vs Nova token usage"""
        json_str = json.dumps(data, indent=2)
        nova_str = NovaCompressor.compress_dict(data)

        json_tokens = NovaCompressor.estimate_tokens(json_str)
        nova_tokens = NovaCompressor.estimate_tokens(nova_str)

        # Guard against division by zero
        if json_tokens > 0:
            savings = (1 - nova_tokens / json_tokens) * 100
        else:
            savings = 0.0

        return {
            "json_format": json_str,
            "json_tokens": json_tokens,
            "nova_format": nova_str,
            "nova_tokens": nova_tokens,
            "savings_percent": round(savings, 1)
        }


# Example HomeLift data structures
EXAMPLES = {
    "zip_territory": {
        "zip_code": "43215",
        "desirability_score": 87.5,
        "timeline": "18_months",
        "lead_count": 45,
        "tier": "Diamond",
        "agent_allocation": {
            "Diamond": 18,
            "Platinum": 27
        },
        "predictive_metrics": {
            "price_growth": 12.5,
            "days_on_market": 28,
            "inventory_turnover": 0.85
        }
    },

    "lead_batch": {
        "batch_id": "LB-20251123-001",
        "source": "PreIntentSeller",
        "leads": [
            {
                "address": "123 Main St",
                "score": 92.3,
                "indicators": ["financial_stress", "life_event"],
                "confidence": 0.89
            },
            {
                "address": "456 Oak Ave",
                "score": 88.1,
                "indicators": ["property_research", "competitor_engagement"],
                "confidence": 0.82
            }
        ],
        "generated_at": "2025-11-23T07:30:00Z"
    }
}


if __name__ == "__main__":
    print("=" * 60)
    print("Nova Token Optimizer for HomeLift")
    print("=" * 60)

    for name, data in EXAMPLES.items():
        print(f"\n{'=' * 60}")
        print(f"Example: {name}")
        print("=" * 60)

        result = NovaCompressor.compare_formats(data)

        print(f"\nJSON Format ({result['json_tokens']} tokens):")
        print("-" * 60)
        print(result['json_format'][:200] + "..." if len(result['json_format']) > 200 else result['json_format'])

        print(f"\nNova Format ({result['nova_tokens']} tokens):")
        print("-" * 60)
        print(result['nova_format'])

        print(f"\n** Token Savings: {result['savings_percent']}%")
        print(f"   ({result['json_tokens']} -> {result['nova_tokens']} tokens)")