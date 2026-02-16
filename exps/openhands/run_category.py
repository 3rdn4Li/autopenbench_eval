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
    parser.add_argument('--instance-idx', type=int, default=None,
                       help='Run only this instance index (0-based). Default: run all.')
    args = parser.parse_args()

    # Resolve LLM API key by provider
    # OPENHANDS_LLM_MODEL: anthropic/claude-opus-4-6 | together_ai/moonshotai/Kimi-K2.5 | etc.
    openhands_model = os.getenv('OPENHANDS_LLM_MODEL')
    if openhands_model and openhands_model.startswith('anthropic/'):
        anthropic_key = (
            os.getenv('OPENHANDS_LLM_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        )
        if not anthropic_key:
            print("❌ Error: For anthropic/ model set ANTHROPIC_API_KEY or OPENHANDS_LLM_API_KEY")
            sys.exit(1)
    elif openhands_model:
        anthropic_key = (
            os.getenv('OPENHANDS_LLM_API_KEY')
            or os.getenv('TOGETHER_API_KEY')
            or os.getenv('TOGETHERAI_API_KEY')
        )
        if not anthropic_key:
            print("❌ Error: For non-Anthropic model set OPENHANDS_LLM_API_KEY or TOGETHER_API_KEY")
            sys.exit(1)
    else:
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if not anthropic_key:
            print("❌ Error: ANTHROPIC_API_KEY not set (or set OPENHANDS_LLM_MODEL + provider API key)")
            sys.exit(1)

    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
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
    
    # Create log directory (include model name for easier identification)
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model = os.getenv('OPENHANDS_LLM_MODEL', 'anthropic/claude-sonnet-4-5-20250929')
    model_safe = model.replace("/", "_")
    log_dir = project_root / "logs" / "openhands_experiments" / f"{args.level}_{args.category}_{model_safe}_{timestamp}"
    log_dir.mkdir(parents=True, exist_ok=True)

    print(f"🤖 OpenHands model: {model}")
    print(f"📁 Logs will be saved to: {log_dir}\n")

    # Run category (or single instance if --instance-idx set)
    results = await run_category(
        level=args.level,
        category=args.category,
        anthropic_key=anthropic_key,
        openai_key=openai_key,
        log_dir=log_dir,
        instance_idx=args.instance_idx,
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

