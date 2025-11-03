# OpenHands Experiments on AutoPenBench

This directory contains scripts to run OpenHands agent on AutoPenBench instances, matching the experimental setup from `genai-pentest-paper`.

## Setup

1. **API Keys**: Set environment variables
   ```bash
   export ANTHROPIC_API_KEY="your-key"  # For OpenHands agent (Claude)
   export OPENAI_API_KEY="your-key"     # For Evaluator (GPT-4o)
   ```

2. **Dependencies**: Ensure virtual environment is activated
   ```bash
   source .venv/bin/activate
   ```

## Configuration

Matches `genai-pentest-paper` setup:

| Level | Category | Instances | Max Iterations | Special Tools |
|-------|----------|-----------|----------------|---------------|
| in-vitro | access_control | 5 | 30 | - |
| in-vitro | network_security | 6 | 30 | WriteFile (i=4,5) |
| in-vitro | cryptography | 4 | 30 | WriteFile (i=2,3) |
| in-vitro | web_security | 7 | 30 | - |
| real-world | cve | 10 | 60 | - |

## Usage

### Run All Experiments

Run all categories and instances:

```bash
python exps/openhands/run_all_experiments.py
```

This will:
- Run all 33 instances
- Save detailed logs for each instance
- Generate summary with success rates and milestones

### Run Single Category

Run a specific category:

```bash
# In-vitro categories
python exps/openhands/run_category.py --level in-vitro --category access_control
python exps/openhands/run_category.py --level in-vitro --category network_security
python exps/openhands/run_category.py --level in-vitro --category cryptography
python exps/openhands/run_category.py --level in-vitro --category web_security

# Real-world CVE
python exps/openhands/run_category.py --level real-world --category cve
```

## Outputs

### Log Directory Structure

```
logs/openhands_experiments/
└── YYYYMMDD_HHMMSS/
    ├── summary.json                              # Overall summary
    ├── in-vitro_access_control_0_*.json         # Instance logs
    ├── in-vitro_access_control_1_*.json
    └── ...
```

### Log Contents

Each instance log contains:
```json
{
  "level": "in-vitro",
  "category": "access_control",
  "instance_idx": 0,
  "target": "in-vitro_access_control_vm0",
  "task": "Task description...",
  "success": true,
  "iterations": 15,
  "max_iterations": 30,
  "duration_seconds": 234.5,
  "reached_command_milestones": 8,
  "total_command_milestones": 8,
  "remaining_stage_milestones": 0,
  "final_agent_state": "finished",
  "timestamp": "2025-01-26T12:34:56"
}
```

### Summary Format

```json
{
  "timestamp": "20250126_123456",
  "total_instances": 33,
  "successful": 28,
  "failed": 5,
  "results": [...]
}
```

## Metrics

Evaluation metrics match `genai-pentest-paper`:

1. **Success Rate**: Percentage of instances where flag was captured
2. **Command Milestones**: Number of intermediate milestones reached
3. **Stage Milestones**: High-level progress stages (e.g., "Network Discovery", "Privilege Escalation")
4. **Iterations**: Number of agent steps used