"""
Quick test script for single AutoPenBench instance.

Usage:
    python test_single.py
    
Or customize:
    python test_single.py --level in-vitro --category access_control --instance 0
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from run_all_experiments import run_single_instance, get_config, BENCHMARK_CONFIG
from datetime import datetime


async def main():
    parser = argparse.ArgumentParser(description='Test OpenHands on single AutoPenBench instance')
    parser.add_argument('--level', default='in-vitro', choices=['in-vitro', 'real-world'])
    parser.add_argument('--category', default='access_control')
    parser.add_argument('--instance', type=int, default=0)
    
    args = parser.parse_args()
    
    # Check API keys
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    if not ANTHROPIC_API_KEY:
        print("❌ Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)
    
    if not OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY not set")
        sys.exit(1)
    
    # Validate
    if args.level not in BENCHMARK_CONFIG or args.category not in BENCHMARK_CONFIG[args.level]:
        print(f"❌ Error: Invalid level/category: {args.level}/{args.category}")
        sys.exit(1)
    
    config_data = BENCHMARK_CONFIG[args.level][args.category]
    if args.instance >= config_data['num_instances']:
        print(f"❌ Error: Instance {args.instance} out of range (max: {config_data['num_instances']-1})")
        sys.exit(1)
    
    # Create config
    config = get_config(ANTHROPIC_API_KEY, config_data['max_iterations'])
    
    # Create log directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = project_root / "logs" / "openhands_test" / timestamp
    log_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Logs will be saved to: {log_dir}\n")
    
    # Run
    result = await run_single_instance(
        level=args.level,
        category=args.category,
        instance_idx=args.instance,
        config=config,
        anthropic_key=ANTHROPIC_API_KEY,
        openai_key=OPENAI_API_KEY,
        log_dir=log_dir,
    )
    
    print(f"\n{'='*80}")
    print("✅ Test completed!")
    print(f"Success: {result['success']}")
    cmd_m = result['milestones']['command']
    print(f"Command Milestones: {cmd_m['achieved']}/{cmd_m['total']}")
    stage_m = result['milestones']['stage']
    print(f"Stage Milestones: {stage_m['achieved']}/{stage_m['total']}")


if __name__ == '__main__':
    asyncio.run(main())

