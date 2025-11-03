"""
Generate LaTeX table from OpenHands experiment results.

Usage:
    python generate_latex_table.py --log_dir logs/openhands_experiments/TIMESTAMP
    
Or analyze multiple directories (will merge results):
    python generate_latex_table.py --log_dirs logs/openhands_experiments/dir1 logs/openhands_experiments/dir2
"""

import os
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import List, Dict

# Add paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def load_results_from_directory(log_dir: Path) -> List[Dict]:
    """Load all result.json files from a log directory."""
    results = []
    
    # Find all result.json files
    for result_file in log_dir.rglob('result.json'):
        try:
            with open(result_file, 'r') as f:
                result = json.load(f)
                results.append(result)
        except Exception as e:
            print(f"Warning: Failed to load {result_file}: {e}")
    
    return results


def calculate_metrics(results: List[Dict]) -> Dict:
    """Calculate SR and PR for each category."""
    
    # Group by category
    by_category = defaultdict(list)
    for r in results:
        key = (r['level'], r['category'])
        by_category[key].append(r)
    
    metrics = {}
    
    for (level, category), instances in by_category.items():
        # Calculate Success Rate (SR)
        total = len(instances)
        successful = sum(1 for r in instances if r.get('success', False))
        sr = successful / total if total > 0 else 0.0
        
        # Calculate Progress Rate (PR) - milestone completion rate
        pr_values_all = []
        pr_values_failed = []
        cost_values = []
        step_values = []
        
        for r in instances:
            cmd_m = r.get('milestones', {}).get('command', {})
            total_milestones = cmd_m.get('total', 0)
            achieved_milestones = cmd_m.get('achieved', 0)
            pr = achieved_milestones / total_milestones if total_milestones > 0 else 0.0
            pr_values_all.append(pr)
            
            # Track failed instances separately
            if not r.get('success', False):
                pr_values_failed.append(pr)
            
            # Get cost
            cost = r.get('metrics', {}).get('accumulated_cost', 0.0)
            cost_values.append(cost)
            
            # Get steps (iterations)
            steps = r.get('iterations', 0)
            step_values.append(steps)
        
        # Overall PR (all instances)
        overall_pr = sum(pr_values_all) / len(pr_values_all) if pr_values_all else 0.0
        
        # Failed PR (only failed instances)
        failed_pr_avg = sum(pr_values_failed) / len(pr_values_failed) if pr_values_failed else 0.0
        failed_pr_min = min(pr_values_failed) if pr_values_failed else 0.0
        failed_pr_max = max(pr_values_failed) if pr_values_failed else 0.0
        
        avg_cost = sum(cost_values) / len(cost_values) if cost_values else 0.0
        avg_steps = sum(step_values) / len(step_values) if step_values else 0.0
        
        metrics[(level, category)] = {
            'total': total,
            'sr': sr,
            'overall_pr': overall_pr,
            'failed_pr_avg': failed_pr_avg,
            'failed_pr_min': failed_pr_min,
            'failed_pr_max': failed_pr_max,
            'avg_cost': avg_cost,
            'avg_steps': avg_steps,
        }
    
    return metrics


def generate_latex_table(metrics: Dict, agent_name: str = "OpenHands + Claude Sonnet 4.5") -> str:
    """Generate LaTeX table."""
    
    # Define category abbreviations and order
    category_order = [
        ('in-vitro', 'access_control', 'AC'),
        ('in-vitro', 'web_security', 'WS'),
        ('in-vitro', 'network_security', 'NS'),
        ('in-vitro', 'cryptography', 'CRPT'),
    ]
    
    lines = []
    lines.append("\\begin{tabular}{l|c|cccc}")
    lines.append("\\hline")
    lines.append("& \\textbf{Tasks} & \\textbf{SR} & \\textbf{PR} & \\textbf{Avg Queries} & \\textbf{Avg Cost (\\$)} \\\\")
    lines.append("\\hline")
    
    # In-vitro categories
    total_in_vitro_tasks = 0
    total_in_vitro_successful = 0
    all_in_vitro_overall_pr = []
    all_in_vitro_failed_pr = []
    all_in_vitro_costs = []
    all_in_vitro_steps = []
    
    for level, category, abbr in category_order:
        if (level, category) in metrics:
            m = metrics[(level, category)]
            total_in_vitro_tasks += m['total']
            total_in_vitro_successful += int(m['sr'] * m['total'])
            all_in_vitro_overall_pr.append(m['overall_pr'])
            all_in_vitro_failed_pr.extend([m['failed_pr_min'], m['failed_pr_max']])
            all_in_vitro_costs.append(m['avg_cost'])
            all_in_vitro_steps.append(m['avg_steps'])
            
            lines.append(f"{abbr} & {m['total']} & {m['sr']:.2f} & {m['overall_pr']:.2f} & {m['avg_steps']:.1f} & {m['avg_cost']:.3f} \\\\")
    
    lines.append("\\hline")
    
    # Total in-vitro
    in_vitro_sr = total_in_vitro_successful / total_in_vitro_tasks if total_in_vitro_tasks > 0 else 0.0
    in_vitro_overall_pr = sum(all_in_vitro_overall_pr) / len(all_in_vitro_overall_pr) if all_in_vitro_overall_pr else 0.0
    in_vitro_failed_pr_avg = sum(all_in_vitro_failed_pr) / len(all_in_vitro_failed_pr) if all_in_vitro_failed_pr else 0.0
    in_vitro_failed_pr_min = min(all_in_vitro_failed_pr) if all_in_vitro_failed_pr else 0.0
    in_vitro_failed_pr_max = max(all_in_vitro_failed_pr) if all_in_vitro_failed_pr else 0.0
    in_vitro_avg_cost = sum(all_in_vitro_costs) / len(all_in_vitro_costs) if all_in_vitro_costs else 0.0
    in_vitro_avg_steps = sum(all_in_vitro_steps) / len(all_in_vitro_steps) if all_in_vitro_steps else 0.0
    
    lines.append(f"Tot. in-vitro & {total_in_vitro_tasks} & {in_vitro_sr:.2f} & {in_vitro_overall_pr:.2f} & {in_vitro_avg_steps:.1f} & {in_vitro_avg_cost:.3f} \\\\")
    lines.append("\\hline")
    
    # Real-world
    if ('real-world', 'cve') in metrics:
        m = metrics[('real-world', 'cve')]
        lines.append(f"Real-world & {m['total']} & {m['sr']:.2f} & {m['overall_pr']:.2f} & {m['avg_steps']:.1f} & {m['avg_cost']:.3f} \\\\")
        lines.append("\\hline")
        
        # Grand total
        grand_total_tasks = total_in_vitro_tasks + m['total']
        grand_total_successful = total_in_vitro_successful + int(m['sr'] * m['total'])
        grand_sr = grand_total_successful / grand_total_tasks if grand_total_tasks > 0 else 0.0
        
        all_overall_pr = all_in_vitro_overall_pr + [m['overall_pr']]
        grand_overall_pr = sum(all_overall_pr) / len(all_overall_pr) if all_overall_pr else 0.0
        
        all_failed_pr = all_in_vitro_failed_pr + [m['failed_pr_min'], m['failed_pr_max']]
        grand_failed_pr_avg = sum(all_failed_pr) / len(all_failed_pr) if all_failed_pr else 0.0
        grand_failed_pr_min = min(all_failed_pr) if all_failed_pr else 0.0
        grand_failed_pr_max = max(all_failed_pr) if all_failed_pr else 0.0
        
        all_costs = all_in_vitro_costs + [m['avg_cost']]
        grand_avg_cost = sum(all_costs) / len(all_costs) if all_costs else 0.0
        
        lines.append(f"Total & {grand_total_tasks} & {grand_sr:.2f} & {grand_overall_pr:.2f} & - & {grand_avg_cost:.3f} \\\\")
    
    lines.append("\\hline")
    lines.append("\\end{tabular}")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Generate LaTeX table from OpenHands results')
    parser.add_argument('--log_dir', type=str, help='Single log directory')
    parser.add_argument('--log_dirs', nargs='+', help='Multiple log directories to merge')
    parser.add_argument('--output', type=str, default='openhands_results.tex', help='Output file')
    
    args = parser.parse_args()
    
    # Collect results
    all_results = []
    
    if args.log_dir:
        log_dir = Path(args.log_dir)
        if not log_dir.exists():
            print(f"❌ Error: Directory not found: {log_dir}")
            sys.exit(1)
        all_results.extend(load_results_from_directory(log_dir))
        print(f"Loaded {len(all_results)} results from {log_dir}")
    
    if args.log_dirs:
        for dir_path in args.log_dirs:
            log_dir = Path(dir_path)
            if not log_dir.exists():
                print(f"⚠️  Warning: Directory not found: {log_dir}")
                continue
            results = load_results_from_directory(log_dir)
            all_results.extend(results)
            print(f"Loaded {len(results)} results from {log_dir}")
    
    if not all_results:
        print("❌ Error: No results found")
        sys.exit(1)
    
    print(f"\n📊 Total results loaded: {len(all_results)}")
    
    # Calculate metrics
    metrics = calculate_metrics(all_results)
    
    # Print summary
    print("\n" + "="*80)
    print("Metrics Summary")
    print("="*80)
    for (level, category), m in sorted(metrics.items()):
        print(f"{level}/{category}: {m['total']} tasks, SR={m['sr']:.2f}, PR={m['overall_pr']:.2f}, Avg Steps={m['avg_steps']:.1f}, Avg Cost=${m['avg_cost']:.3f}")
    
    # Generate LaTeX
    latex = generate_latex_table(metrics)
    
    # Save to file
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        f.write(latex)
    
    print(f"\n✅ LaTeX table saved to: {output_path}")
    print("\n" + "="*80)
    print("Generated LaTeX:")
    print("="*80)
    print(latex)


if __name__ == '__main__':
    main()

