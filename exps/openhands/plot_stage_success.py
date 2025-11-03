"""
Generate stage success rate plot for real-world CVE tasks.

Usage:
    python plot_stage_success.py --log_dir logs/openhands_experiments/real-world_cve_TIMESTAMP
"""

import os
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Add paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def load_results_from_directory(log_dir: Path, level: str = 'real-world', category: str = 'cve') -> list:
    """Load all result.json files for specified category."""
    results = []
    
    # Find all result.json files matching the category
    for result_file in log_dir.rglob('result.json'):
        try:
            with open(result_file, 'r') as f:
                result = json.load(f)
                if result.get('level') == level and result.get('category') == category:
                    results.append(result)
        except Exception as e:
            print(f"Warning: Failed to load {result_file}: {e}")
    
    return results


def calculate_stage_success_rates(results: list) -> dict:
    """Calculate success rate for each stage milestone."""
    
    # Collect all stage names and count achievements
    stage_counts = defaultdict(lambda: {'achieved': 0, 'total': 0})
    
    # Also track flag success for "Exploitation" (renamed from Success)
    flag_success_count = 0
    total_instances = len(results)
    
    for r in results:
        stage_m = r.get('milestones', {}).get('stage', {})
        achieved_stages = stage_m.get('achieved_list', [])
        remaining_stages = stage_m.get('remaining_list', [])
        
        # All stages that were defined for this task
        all_stages = achieved_stages + remaining_stages
        
        for stage in all_stages:
            stage_counts[stage]['total'] += 1
            if stage in achieved_stages:
                stage_counts[stage]['achieved'] += 1
        
        # Track flag success
        if r.get('success', False):
            flag_success_count += 1
    
    # Calculate success rates
    stage_success_rates = {}
    for stage, counts in stage_counts.items():
        sr = counts['achieved'] / counts['total'] if counts['total'] > 0 else 0.0
        stage_success_rates[stage] = sr
    
    # Merge stages: Target Discovery + Reconnaissance + Vulnerability Discovery → Reconnaissance
    recon_stages = ['Target Discovery', 'Reconnaissance', 'Vulnerability Discovery']
    recon_present = [s for s in recon_stages if s in stage_success_rates]
    
    if recon_present:
        # Calculate average success rate across these stages
        recon_rates = [stage_success_rates[s] for s in recon_present]
        merged_recon_rate = sum(recon_rates) / len(recon_rates)
        # Remove original stages first
        for s in recon_stages:
            stage_success_rates.pop(s, None)
        # Add merged stage
        stage_success_rates['Reconnaissance'] = merged_recon_rate
    
    # Split Exploitation into Weaponization and Delivery (both use same rate)
    if 'Exploitation' in stage_success_rates:
        exploitation_rate = stage_success_rates['Exploitation']
        stage_success_rates['Weaponization'] = exploitation_rate
        stage_success_rates['Delivery'] = exploitation_rate
        stage_success_rates.pop('Exploitation')
    
    # Remove Flag Capturing
    stage_success_rates.pop('Flag Capturing', None)
    
    # Rename Success → Exploitation (use flag success rate)
    if 'Success' in stage_success_rates:
        stage_success_rates['Exploitation'] = flag_success_count / total_instances if total_instances > 0 else 0.0
        stage_success_rates.pop('Success')
    
    return stage_success_rates


def plot_stage_success(stage_rates: dict, output_path: str):
    """Create horizontal bar plot of stage success rates."""
    
    # Define pentest stage order (Reconnaissance at bottom, Exploitation at top)
    stage_order = [
        'Reconnaissance',  # Bottom: Merged Target Discovery + Reconnaissance + Vulnerability Discovery
        'Weaponization',   # 
        'Delivery',        # 
        'Exploitation',    # Top: Renamed from Success (actual flag success rate)
    ]
    
    # Filter to only stages that exist in results
    stages_to_plot = [s for s in stage_order if s in stage_rates]
    rates = [stage_rates[s] * 100 for s in stages_to_plot]  # Convert to percentage
    
    # Create plot (matching command_frequency.py style)
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create horizontal bars (thinner)
    y_pos = range(len(stages_to_plot))
    bars = ax.barh(y_pos, rates, height=0.5, color='#6baed6', edgecolor='black', linewidth=1.0)
    
    # Add value labels (larger)
    for i, (bar, rate) in enumerate(zip(bars, rates)):
        ax.text(rate + 1, bar.get_y() + bar.get_height()/2, 
                f'{rate:.1f}',
                ha='left', va='center', fontsize=14, fontweight='bold')
    
    # Customize plot (larger fonts)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(stages_to_plot, fontsize=14, fontweight='bold')
    ax.set_xlabel('Stage Success Rate (%)', fontsize=16, fontweight='bold')
    ax.set_xlim(0, max(rates) * 1.15)  # Extra space for labels (rates are now percentages)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    # Don't invert - Exploitation (highest) at top, Reconnaissance (lowest) at bottom
    
    # Increase tick label size and make bold
    ax.tick_params(axis='x', labelsize=12)
    ax.tick_params(axis='both', width=1.5)
    for label in ax.get_xticklabels():
        label.set_fontweight('bold')
    
    plt.tight_layout()
    
    # Save
    plt.savefig(output_path, format='pdf', bbox_inches='tight', dpi=300)
    print(f"✅ Plot saved to: {output_path}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='Plot stage success rates for real-world CVE')
    parser.add_argument('--log_dir', type=str, required=True, help='Log directory with real-world cve results')
    parser.add_argument('--output', type=str, default='autopenbench_stage_success_rates.pdf', help='Output PDF file')
    
    args = parser.parse_args()
    
    log_dir = Path(args.log_dir)
    if not log_dir.exists():
        print(f"❌ Error: Directory not found: {log_dir}")
        sys.exit(1)
    
    # Load results
    print(f"📂 Loading results from {log_dir}...")
    results = load_results_from_directory(log_dir, level='real-world', category='cve')
    
    if not results:
        print("❌ Error: No real-world CVE results found")
        sys.exit(1)
    
    print(f"✅ Loaded {len(results)} real-world CVE results")
    
    # Calculate stage success rates
    stage_rates = calculate_stage_success_rates(results)
    
    print("\n" + "="*80)
    print("Stage Success Rates")
    print("="*80)
    for stage, rate in sorted(stage_rates.items()):
        print(f"{stage}: {rate:.2f}")
    
    # Generate plot
    print(f"\n📊 Generating plot...")
    plot_stage_success(stage_rates, args.output)


if __name__ == '__main__':
    main()

