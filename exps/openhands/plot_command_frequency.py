"""
Plot top command/tool usage frequency from OpenHands experiments.

Usage:
    python plot_command_frequency.py --log_dir logs/openhands_experiments
"""

import re
import argparse
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


def extract_commands_from_stdout(stdout_file: Path) -> list:
    """Extract bash commands from stdout.log file."""
    commands = []
    
    try:
        with open(stdout_file, 'r', errors='ignore') as f:
            content = f.read()
        
        # Match pattern: Action:machine_ipaddr='...' cmd='...'
        pattern = r"Action:machine_ipaddr='[^']+' cmd='([^']+)'"
        matches = re.findall(pattern, content)
        commands.extend(matches)
        
    except Exception as e:
        pass
    
    return commands


def get_command_category(cmd: str) -> str:
    """Categorize command by first word/tool."""
    cmd = cmd.strip()
    
    # Get first word
    first_word = cmd.split()[0] if cmd.split() else cmd
    
    # Remove path
    first_word = first_word.split('/')[-1]
    
    return first_word


def merge_metasploit_commands(command_categories: Counter) -> Counter:
    """Merge metasploit-related commands into one category."""
    
    msf_commands = ['msfconsole', 'set', 'show', 'use', 'sessions', 
                    'exploit', 'options', 'search', 'run', 'exit']
    
    merged = Counter()
    msf_total = 0
    
    for cmd, count in command_categories.items():
        if cmd.lower() in msf_commands:
            msf_total += count
        elif cmd.lower() in ['sleep', 'timeout']:
            # Skip sleep and timeout
            continue
        else:
            merged[cmd] = count
    
    # Add merged metasploit category
    if msf_total > 0:
        msf_label = 'metasploit'
        merged[msf_label] = msf_total
    
    return merged


def plot_command_frequency(command_counts: Counter, output_path: str, top_n: int = 10):
    """Plot horizontal bar chart of top N commands."""
    
    # Get top N
    top_commands = command_counts.most_common(top_n)
    
    if not top_commands:
        print("No commands to plot")
        return
    
    # Prepare data
    commands = [cmd for cmd, _ in top_commands]
    counts = [count for _, count in top_commands]
    total = sum(command_counts.values())
    percentages = [count / total * 100 for count in counts]
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create horizontal bars
    y_pos = range(len(commands))
    bars = ax.barh(y_pos, percentages, color='#6baed6', edgecolor='black', linewidth=1.0)
    
    # Add value labels
    for i, (bar, pct, count) in enumerate(zip(bars, percentages, counts)):
        ax.text(pct + 0.5, bar.get_y() + bar.get_height()/2, 
                f'{pct:.1f}',
                ha='left', va='center', fontsize=14, fontweight='bold')
    
    # Customize plot
    ax.set_yticks(y_pos)
    ax.set_yticklabels(commands, fontsize=14, fontweight='bold')
    ax.set_xlabel('Percentage (%)', fontsize=16, fontweight='bold')
    ax.set_xlim(0, max(percentages) * 1.25)  # Extra space for labels
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.invert_yaxis()  # Highest at top
    
    # Make x-axis tick labels bold
    ax.tick_params(axis='both', width=1.5, labelsize=12)
    for label in ax.get_xticklabels():
        label.set_fontweight('bold')
    
    plt.tight_layout()
    
    # Save
    plt.savefig(output_path, format='pdf', bbox_inches='tight', dpi=300)
    print(f"✅ Plot saved to: {output_path}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='Plot command usage frequency')
    parser.add_argument('--log_dir', type=str, 
                       default='logs/openhands_experiments',
                       help='Base log directory')
    parser.add_argument('--top_n', type=int, default=10,
                       help='Show top N commands')
    parser.add_argument('--output', type=str, default='command_frequency.pdf',
                       help='Output PDF file')
    
    args = parser.parse_args()
    
    log_dir = Path(args.log_dir)
    if not log_dir.exists():
        print(f"❌ Error: Directory not found: {log_dir}")
        return
    
    # Collect all commands
    print(f"🔍 Analyzing commands from {log_dir}...")
    all_commands = []
    
    for stdout_file in log_dir.rglob('stdout.log'):
        commands = extract_commands_from_stdout(stdout_file)
        all_commands.extend(commands)
    
    print(f"📊 Total commands executed: {len(all_commands)}")
    
    # Categorize
    command_categories = Counter()
    for cmd in all_commands:
        category = get_command_category(cmd)
        command_categories[category] += 1
    
    # Merge metasploit commands and remove sleep
    merged = merge_metasploit_commands(command_categories)
    
    print(f"\n📈 Top {args.top_n} commands after merging:")
    for i, (cmd, count) in enumerate(merged.most_common(args.top_n), 1):
        pct = count / len(all_commands) * 100
        print(f"{i:2}. {cmd:30} {count:4} ({pct:5.1f}%)")
    
    # Plot
    plot_command_frequency(merged, args.output, args.top_n)


if __name__ == '__main__':
    main()

