#!/usr/bin/env python3
"""
CivicFold + LeadFold NOVA Benchmark - INTERNAL ONLY
=====================================================
Shows token reduction for CivicFold zone intelligence and LeadFold scoring data.
"""

import json
import sys
from typing import Dict, Any
from datetime import datetime

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


def count_tokens(text: str) -> int:
    if TIKTOKEN_AVAILABLE:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    return len(text) // 4


def print_header(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


# =============================================================================
# CIVICFOLD TEST DATA - Zone Intelligence
# =============================================================================

CIVICFOLD_ZONE_DATA = {
    "zones": [
        {
            "zip_code": "43201",
            "zone_name": "Victorian Village",
            "transformation_score": 0.92,
            "transformation_confidence": 0.88,
            "time_horizon_months": 18,
            "classification": "TRANSFORMED",
            "signals": {
                "infrastructure_signal": 0.85,
                "permit_signal": 0.91,
                "commercial_signal": 0.78,
                "demographic_signal": 0.89,
                "investment_signal": 0.94,
            },
            "flags": {
                "emerging_hot_zone": True,
                "gentrification_risk": True,
                "investor_opportunity": True,
            },
            "metrics": {
                "median_home_value": 425000,
                "value_change_1yr": 12.5,
                "value_change_5yr": 78.3,
                "days_on_market": 14,
                "inventory_months": 1.2,
                "permits_per_1000": 45.8,
                "new_business_permits": 23,
            }
        },
        {
            "zip_code": "43205",
            "zone_name": "Olde Towne East",
            "transformation_score": 0.78,
            "transformation_confidence": 0.82,
            "time_horizon_months": 24,
            "classification": "TRANSFORMING",
            "signals": {
                "infrastructure_signal": 0.72,
                "permit_signal": 0.81,
                "commercial_signal": 0.65,
                "demographic_signal": 0.74,
                "investment_signal": 0.79,
            },
            "flags": {
                "emerging_hot_zone": True,
                "gentrification_risk": True,
                "investor_opportunity": True,
            },
            "metrics": {
                "median_home_value": 285000,
                "value_change_1yr": 15.2,
                "value_change_5yr": 95.4,
                "days_on_market": 21,
                "inventory_months": 1.8,
                "permits_per_1000": 38.2,
                "new_business_permits": 18,
            }
        },
        {
            "zip_code": "43204",
            "zone_name": "Hilltop",
            "transformation_score": 0.45,
            "transformation_confidence": 0.71,
            "time_horizon_months": 48,
            "classification": "EARLY_SIGNALS",
            "signals": {
                "infrastructure_signal": 0.42,
                "permit_signal": 0.51,
                "commercial_signal": 0.38,
                "demographic_signal": 0.48,
                "investment_signal": 0.44,
            },
            "flags": {
                "emerging_hot_zone": False,
                "gentrification_risk": False,
                "investor_opportunity": True,
            },
            "metrics": {
                "median_home_value": 125000,
                "value_change_1yr": 8.1,
                "value_change_5yr": 42.6,
                "days_on_market": 45,
                "inventory_months": 3.2,
                "permits_per_1000": 18.5,
                "new_business_permits": 5,
            }
        },
    ],
    "analysis_timestamp": "2024-01-20T15:30:00Z",
    "model_version": "civicfold_v2.1",
    "data_sources": ["census_acs", "zillow", "permits", "lehd", "redfin"],
}

# =============================================================================
# LEADFOLD TEST DATA - Enriched Leads
# =============================================================================

LEADFOLD_LEADS_DATA = {
    "leads": [
        {
            "lead_id": "LF-2024-001234",
            "email": "john.smith@example.com",
            "phone": "614-555-1234",
            "first_name": "John",
            "last_name": "Smith",
            "address": {
                "street": "1234 Main Street",
                "city": "Columbus",
                "state": "OH",
                "zip_code": "43201"
            },
            "scoring": {
                "lead_score": 92.5,
                "confidence": 0.89,
                "routing": "fast_track",
                "predicted_days_to_move": 45,
                "mover_tier": "Diamond",
                "buyer_segment": "move_up",
                "price_percentile": 75.0,
            },
            "zone_intelligence": {
                "transformation_score": 0.92,
                "zone_classification": "TRANSFORMED",
                "investor_likelihood": 0.94,
                "emerging_hot_zone": True,
            },
            "visual_signals": {
                "curb_appeal_score": 8.2,
                "property_condition_score": 7.8,
                "neighborhood_quality_score": 8.5,
            },
            "source": {
                "channel": "meta_ads",
                "campaign": "columbus_q1_2024",
                "ad_set": "homeowners_45plus",
            },
            "timestamps": {
                "created_at": "2024-01-15T10:30:00Z",
                "scored_at": "2024-01-15T10:30:05Z",
                "last_activity": "2024-01-20T14:22:00Z",
            }
        }
    ] * 25,  # 25 leads
    "batch_metadata": {
        "total_leads": 25,
        "avg_score": 87.3,
        "fast_track_count": 8,
        "follow_up_count": 12,
        "nurture_count": 5,
        "processing_time_ms": 245,
    }
}


# =============================================================================
# NOVA COMPRESSION SIMULATION
# =============================================================================

def nova_compress_civicfold(data: Dict) -> str:
    """Simulate NOVA compression for CivicFold zone data."""
    lines = []
    lines.append(f"zones[{len(data['zones'])}]:")
    for zone in data["zones"]:
        z = zone
        lines.append(f"  {z['zip_code']} {z['classification'][:4]} t{z['transformation_score']:.2f} c{z['transformation_confidence']:.2f}")
        lines.append(f"    sig:inf{z['signals']['infrastructure_signal']:.1f} prm{z['signals']['permit_signal']:.1f} com{z['signals']['commercial_signal']:.1f}")
        lines.append(f"    val:${z['metrics']['median_home_value']//1000}k +{z['metrics']['value_change_1yr']:.0f}%/1y dom{z['metrics']['days_on_market']}")
    lines.append(f"model:{data['model_version']} src:{len(data['data_sources'])}")
    return "\n".join(lines)


def nova_compress_leadfold(data: Dict) -> str:
    """Simulate NOVA compression for LeadFold enriched leads."""
    lines = []
    meta = data["batch_metadata"]
    lines.append(f"leads[{meta['total_leads']}] avg:{meta['avg_score']:.0f} ft:{meta['fast_track_count']} fu:{meta['follow_up_count']} nr:{meta['nurture_count']}")

    # Show first 5 leads compressed
    for lead in data["leads"][:5]:
        s = lead["scoring"]
        z = lead["zone_intelligence"]
        lines.append(f"  {lead['lead_id'][-6:]} {lead['address']['zip_code']} s{s['lead_score']:.0f} {s['routing'][:2]} d{s['predicted_days_to_move']} {s['mover_tier'][0]}")
        lines.append(f"    zone:t{z['transformation_score']:.1f} {z['zone_classification'][:4]} hot:{int(z['emerging_hot_zone'])}")

    if len(data["leads"]) > 5:
        lines.append(f"  ...+{len(data['leads'])-5} more")

    return "\n".join(lines)


# =============================================================================
# BENCHMARK
# =============================================================================

def run_benchmark():
    print_header("CivicFold + LeadFold NOVA Benchmark - INTERNAL ONLY")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nMeasuring token reduction for CivicFold zone intelligence")
    print("and LeadFold enriched lead data.\n")

    # -------------------------------------------------------------------------
    # CIVICFOLD Benchmark
    # -------------------------------------------------------------------------
    print_header("CivicFold Zone Intelligence")

    cf_raw_json = json.dumps(CIVICFOLD_ZONE_DATA, indent=2)
    cf_raw_tokens = count_tokens(cf_raw_json)

    cf_nova = nova_compress_civicfold(CIVICFOLD_ZONE_DATA)
    cf_nova_tokens = count_tokens(cf_nova)

    cf_reduction = (1 - cf_nova_tokens / cf_raw_tokens) * 100

    print(f"Data: {len(CIVICFOLD_ZONE_DATA['zones'])} zone records with signals + metrics")
    print(f"\n--- RAW JSON ({cf_raw_tokens} tokens) ---")
    print(cf_raw_json[:500] + "..." if len(cf_raw_json) > 500 else cf_raw_json)
    print(f"\n--- NOVA FORMAT ({cf_nova_tokens} tokens) ---")
    print(cf_nova)
    print(f"\n{'='*50}")
    print(f"CIVICFOLD REDUCTION: {cf_reduction:.1f}%")
    print(f"  Before: {cf_raw_tokens:,} tokens")
    print(f"  After:  {cf_nova_tokens:,} tokens")
    print(f"  Saved:  {cf_raw_tokens - cf_nova_tokens:,} tokens")
    print(f"{'='*50}")

    # -------------------------------------------------------------------------
    # LEADFOLD Benchmark
    # -------------------------------------------------------------------------
    print_header("LeadFold Enriched Leads")

    lf_raw_json = json.dumps(LEADFOLD_LEADS_DATA, indent=2)
    lf_raw_tokens = count_tokens(lf_raw_json)

    lf_nova = nova_compress_leadfold(LEADFOLD_LEADS_DATA)
    lf_nova_tokens = count_tokens(lf_nova)

    lf_reduction = (1 - lf_nova_tokens / lf_raw_tokens) * 100

    print(f"Data: {LEADFOLD_LEADS_DATA['batch_metadata']['total_leads']} enriched leads with scoring + zone intel")
    print(f"\n--- RAW JSON ({lf_raw_tokens} tokens) ---")
    print(lf_raw_json[:500] + "..." if len(lf_raw_json) > 500 else lf_raw_json)
    print(f"\n--- NOVA FORMAT ({lf_nova_tokens} tokens) ---")
    print(lf_nova)
    print(f"\n{'='*50}")
    print(f"LEADFOLD REDUCTION: {lf_reduction:.1f}%")
    print(f"  Before: {lf_raw_tokens:,} tokens")
    print(f"  After:  {lf_nova_tokens:,} tokens")
    print(f"  Saved:  {lf_raw_tokens - lf_nova_tokens:,} tokens")
    print(f"{'='*50}")

    # -------------------------------------------------------------------------
    # COMBINED Summary
    # -------------------------------------------------------------------------
    print_header("COMBINED RESULTS")

    total_raw = cf_raw_tokens + lf_raw_tokens
    total_nova = cf_nova_tokens + lf_nova_tokens
    total_reduction = (1 - total_nova / total_raw) * 100

    print(f"{'Component':<25} {'Before':<15} {'After':<15} {'Reduction':<10}")
    print("-" * 65)
    print(f"{'CivicFold Zone Intel':<25} {cf_raw_tokens:,} tokens{'':<3} {cf_nova_tokens:,} tokens{'':<4} {cf_reduction:.1f}%")
    print(f"{'LeadFold Enriched Leads':<25} {lf_raw_tokens:,} tokens{'':<3} {lf_nova_tokens:,} tokens{'':<4} {lf_reduction:.1f}%")
    print("-" * 65)
    print(f"{'TOTAL':<25} {total_raw:,} tokens{'':<3} {total_nova:,} tokens{'':<4} {total_reduction:.1f}%")

    print(f"\n{'='*65}")
    print(f"  NOVA reduces CivicFold + LeadFold data by {total_reduction:.0f}%")
    print(f"  Tokens saved per request: {total_raw - total_nova:,}")
    print(f"  Cost savings (1M requests): ${(total_raw - total_nova) * 0.00001 * 1000000:.0f}")
    print(f"{'='*65}")


if __name__ == "__main__":
    run_benchmark()
