"""
Analyze bash command usage frequency from OpenHands experiments.

Usage:
    python analyze_commands.py --log_dir logs/openhands_experiments
"""

import re
import argparse
from pathlib import Path
from collections import Counter


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
    
    # Remove common prefixes
    first_word = first_word.split('/')[-1]  # Remove path
    
    return first_word


def analyze_commands(log_base_dir: Path, top_n: int = 30) -> dict:
    """Analyze all bash commands from log directory."""
    
    all_commands = []
    command_categories = Counter()
    full_commands = Counter()
    
    # Collect from all stdout files
    for stdout_file in log_base_dir.rglob('stdout.log'):
        commands = extract_commands_from_stdout(stdout_file)
        all_commands.extend(commands)
    
    print(f"📊 Total commands executed: {len(all_commands)}")
    
    # Categorize by tool
    for cmd in all_commands:
        category = get_command_category(cmd)
        command_categories[category] += 1
        
        # Track full commands (truncated for display)
        cmd_display = cmd[:100] + '...' if len(cmd) > 100 else cmd
        full_commands[cmd_display] += 1
    
    return {
        'total': len(all_commands),
        'categories': command_categories,
        'full_commands': full_commands,
    }


def print_report(analysis: dict, top_n: int = 30):
    """Print analysis report."""
    
    print("\n" + "="*80)
    print("COMMAND CATEGORIES (by tool/binary)")
    print("="*80)
    
    categories = analysis['categories']
    for i, (cmd, count) in enumerate(categories.most_common(top_n), 1):
        percentage = count / analysis['total'] * 100
        print(f"{i:2}. {cmd:20} {count:4} ({percentage:5.1f}%)")
    
    print("\n" + "="*80)
    print("TOP FULL COMMANDS")
    print("="*80)
    
    full_commands = analysis['full_commands']
    for i, (cmd, count) in enumerate(full_commands.most_common(top_n), 1):
        if count >= 2:  # Only show commands used 2+ times
            print(f"{i:2}. [{count:2}x] {cmd}")


def main():
    parser = argparse.ArgumentParser(description='Analyze bash command usage')
    parser.add_argument('--log_dir', type=str, 
                       default='logs/openhands_experiments',
                       help='Base log directory')
    parser.add_argument('--top_n', type=int, default=30,
                       help='Show top N commands')
    parser.add_argument('--output', type=str, help='Save report to file')
    parser.add_argument('--search', type=str, help='Search for commands containing this keyword')
    
    args = parser.parse_args()
    
    log_dir = Path(args.log_dir)
    if not log_dir.exists():
        print(f"❌ Error: Directory not found: {log_dir}")
        return
    
    # Analyze
    print(f"🔍 Analyzing commands from {log_dir}...")
    analysis = analyze_commands(log_dir, args.top_n)
    
    # Search for specific keyword if requested
    if args.search:
        print("\n" + "="*80)
        print(f"COMMANDS CONTAINING '{args.search}'")
        print("="*80)
        
        matching = []
        log_dir_path = Path(args.log_dir)
        for stdout_file in log_dir_path.rglob('stdout.log'):
            commands = extract_commands_from_stdout(stdout_file)
            for cmd in commands:
                if args.search.lower() in cmd.lower():
                    matching.append((cmd, stdout_file.parent.name))
        
        if matching:
            # Group by command
            cmd_counts = Counter(cmd for cmd, _ in matching)
            for cmd, count in cmd_counts.most_common(50):
                print(f"[{count:2}x] {cmd}")
        else:
            print(f"No commands found containing '{args.search}'")
        
        return
    
    # Print report
    print_report(analysis, args.top_n)
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            f.write(f"Total commands: {analysis['total']}\n\n")
            f.write("="*80 + "\n")
            f.write("COMMAND CATEGORIES\n")
            f.write("="*80 + "\n")
            for cmd, count in analysis['categories'].most_common(args.top_n):
                percentage = count / analysis['total'] * 100
                f.write(f"{cmd:20} {count:4} ({percentage:5.1f}%)\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("TOP FULL COMMANDS (2+ uses)\n")
            f.write("="*80 + "\n")
            for cmd, count in analysis['full_commands'].most_common(args.top_n):
                if count >= 2:
                    f.write(f"[{count:2}x] {cmd}\n")
        
        print(f"\n✅ Report saved to: {args.output}")


if __name__ == '__main__':
    main()

