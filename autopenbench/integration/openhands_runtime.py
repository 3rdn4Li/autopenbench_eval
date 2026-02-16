"""
AutoPenBench Runtime for OpenHands.

This runtime extends LocalRuntime and intercepts AutoPenBench-specific actions,
executing them through the AutoPenBench driver.
"""
import sys
from pathlib import Path

# Add OpenHands to path
openhands_path = Path(__file__).parent.parent.parent / "third_party" / "OpenHands"
sys.path.insert(0, str(openhands_path))

from openhands.events.observation import CmdOutputObservation, ErrorObservation
from openhands.runtime.impl.local.local_runtime import LocalRuntime
from openhands.events.action import Action

from autopenbench.driver import PentestDriver
from autopenbench.evaluation import Evaluator
from autopenbench.tools import ExecuteBash, SSHConnect, WriteFile, FinalAnswer


class AutoPenBenchRuntime(LocalRuntime):
    """Runtime that extends LocalRuntime to handle AutoPenBench actions.
    
    This runtime:
    1. Intercepts AutoPenBench*Action types
    2. Executes them through PentestDriver
    3. Delegates other actions to LocalRuntime
    
    Args:
        driver: AutoPenBench PentestDriver instance
        evaluator: Optional Evaluator for milestone tracking
        **kwargs: Arguments passed to LocalRuntime
    """
    
    def __init__(
        self,
        driver: PentestDriver,
        evaluator: Evaluator = None,
        **kwargs
    ):
        # Initialize LocalRuntime with all standard parameters
        super().__init__(**kwargs)
        
        # AutoPenBench specific
        self.driver = driver
        self.evaluator = evaluator
        self._done = False
    
    def run_action(self, action: Action):
        """Execute action through AutoPenBench driver or fallback runtime.
        
        Args:
            action: Action to execute
            
        Returns:
            Observation from execution
        """
        action_type = action.__class__.__name__
        
        try:
            # Handle AutoPenBench actions
            if action_type == 'ExecuteBashPentestAction':
                return self._handle_execute_bash(action)
            
            elif action_type == 'SSHConnectPentestAction':
                return self._handle_ssh_connect(action)
            
            elif action_type == 'WriteFilePentestAction':
                return self._handle_write_file(action)
            
            elif action_type == 'SubmitFlagPentestAction':
                return self._handle_submit_flag(action)
            
            # Delegate to LocalRuntime for other actions
            else:
                return super().run_action(action)
        
        except Exception as e:
            return ErrorObservation(content=f"Error executing {action_type}: {str(e)}")
    
    def _handle_execute_bash(self, action):
        """Handle ExecuteBashPentestAction."""
        tool = ExecuteBash(
            machine_ipaddr=action.machine_ipaddr,
            cmd=action.cmd
        )
        
        observation_text, done = self.driver.step(tool)
        print("____________________________________________________")
        print("tool name: ", tool.__class__.__name__)
        print(f"Action:{tool}\nObservation: {observation_text}")
        self._done = done
        
        # Evaluate
        if self.evaluator:
            step_text = f"Action:{tool}\nObservation: {observation_text}"
            self.evaluator.evaluate_step(step_text)

        print("[AutoPenBench] Observation returned to agent (waiting for next LLM response)...", flush=True)
        return CmdOutputObservation(
            command=action.cmd,
            content=observation_text,
            exit_code=0 if not done else 1,  # 0 for continue, 1 for done
        )

    def _handle_ssh_connect(self, action):
        """Handle SSHConnectPentestAction."""
        tool = SSHConnect(
            ssh_ipaddr=action.ssh_ipaddr,
            ssh_port=action.ssh_port,
            ssh_username=action.ssh_username,
            ssh_password=action.ssh_password,
        )
        
        observation_text, done = self.driver.step(tool)
        print("____________________________________________________")
        print("tool name: ", tool.__class__.__name__)
        print(f"Action:{tool}\nObservation: {observation_text}")
        self._done = done
        
        # Evaluate
        if self.evaluator:
            step_text = f"Action:{tool}\nObservation: {observation_text}"
            self.evaluator.evaluate_step(step_text)

        print("[AutoPenBench] Observation returned to agent (waiting for next LLM response)...", flush=True)
        return CmdOutputObservation(
            command=f"SSH to {action.ssh_username}@{action.ssh_ipaddr}:{action.ssh_port}",
            content=observation_text,
            exit_code=0,
        )

    def _handle_write_file(self, action):
        """Handle WriteFilePentestAction."""
        tool = WriteFile(
            file_name=action.file_name,
            content=action.content
        )
        
        observation_text, done = self.driver.step(tool)
        print("____________________________________________________")
        print("tool name: ", tool.__class__.__name__)
        print(f"Action:{tool}\nObservation: {observation_text}")
        self._done = done
        
        # Evaluate
        if self.evaluator:
            step_text = f"Action:{tool}\nObservation: {observation_text}"
            self.evaluator.evaluate_step(step_text)

        print("[AutoPenBench] Observation returned to agent (waiting for next LLM response)...", flush=True)
        return CmdOutputObservation(
            command=f"Write file {action.file_name}",
            content=observation_text,
            exit_code=0,
        )

    def _handle_submit_flag(self, action):
        """Handle SubmitFlagPentestAction."""
        tool = FinalAnswer(flag=action.flag)
        
        observation_text, done = self.driver.step(tool)
        print("____________________________________________________")
        print("tool name: ", tool.__class__.__name__)
        print(f"Action:{tool}\nObservation: {observation_text}")
        self._done = done
        
        # Evaluate
        if self.evaluator:
            step_text = f"Action:{tool}\nObservation: {observation_text}"
            self.evaluator.evaluate_step(step_text)

        print("[AutoPenBench] Observation returned to agent (waiting for next LLM response)...", flush=True)
        return CmdOutputObservation(
            command=f"Submit flag",
            content=observation_text,
            exit_code=0,
        )
    
    @property
    def is_task_done(self) -> bool:
        """Check if AutoPenBench task is completed."""
        return self._done
