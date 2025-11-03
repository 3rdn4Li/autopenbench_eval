"""
Run OpenHands on a specific category.

Usage:
    python run_category.py --level in-vitro --category access_control
    python run_category.py --level real-world --category cve
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from run_all_experiments import run_category, BENCHMARK_CONFIG


async def main():
    parser = argparse.ArgumentParser(description='Run OpenHands on AutoPenBench category')
    parser.add_argument('--level', required=True, choices=['in-vitro', 'real-world'],
                       help='Benchmark level')
    parser.add_argument('--category', required=True,
                       help='Category name (e.g., access_control, cve)')
    
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
    
    # Validate category
    if args.level not in BENCHMARK_CONFIG or args.category not in BENCHMARK_CONFIG[args.level]:
        print(f"❌ Error: Invalid level/category: {args.level}/{args.category}")
        print(f"\nAvailable combinations:")
        for level, categories in BENCHMARK_CONFIG.items():
            for category in categories:
                print(f"  - {level}/{category}")
        sys.exit(1)
    
    # Create log directory
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = project_root / "logs" / "openhands_experiments" / f"{args.level}_{args.category}_{timestamp}"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Logs will be saved to: {log_dir}\n")
    
    # Run category
    results = await run_category(
        level=args.level,
        category=args.category,
        anthropic_key=ANTHROPIC_API_KEY,
        openai_key=OPENAI_API_KEY,
        log_dir=log_dir,
    )
    
    # Print summary
    import json
    summary = {
        'level': args.level,
        'category': args.category,
        'timestamp': timestamp,
        'total_instances': len(results),
        'successful': sum(1 for r in results if r.get('success')),
        'results': results,
    }
    
    summary_file = log_dir / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"📊 Summary for {args.level}/{args.category}")
    print(f"{'='*80}")
    print(f"Success rate: {summary['successful']}/{summary['total_instances']} ({summary['successful']/summary['total_instances']*100:.1f}%)")
    print(f"Results saved to: {summary_file}")


if __name__ == '__main__':
    asyncio.run(main())

