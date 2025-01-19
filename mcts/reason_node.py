# reason_node.py

from .MCTS import MCTS_Node
from typing import Optional, List
from prompts import ACTIONS
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReasoningNode(MCTS_Node):
    def __init__(self, state: dict, parent: Optional['ReasoningNode'] = None, action: Optional[str] = None):
        super().__init__()
        self.state = state  # {'actions_taken': [...], 'current_action_index': int, 'action_rewards': [...]}
        self.parent = parent
        self.action = action

    def find_children(self, rollout_id: int) -> List['ReasoningNode']:
        """
        Generate child nodes by selecting the next action in the sequence.
        """
        logger.debug(f"Finding children for node {self.id} with rollout_id {rollout_id}.")
        possible_actions = self.state.get('possible_actions', [])
        children = []
        for action in possible_actions:
            # Create a new state for each action
            new_actions_taken = self.state.get('actions_taken', []) + [action]
            new_state = {
                'actions_taken': new_actions_taken,
                'current_action_index': self.state.get('current_action_index', 0) + 1,
                'action_rewards': self.state.get('action_rewards', []) + [0.0],  # Placeholder for reward
                'possible_actions': [a for a in possible_actions if a != action]
            }
            child_node = ReasoningNode(state=new_state, parent=self, action=action)
            children.append(child_node)
        return children

    def is_terminal(self) -> bool:
        """
        Terminal if all actions have been taken.
        """
        return self.state['current_action_index'] >= len(ACTIONS)

    def calculate_reward(self) -> float:
        """
        Calculate the cumulative reward based on action_rewards.
        """
        rewards = self.state.get('action_rewards', [])

        logger.info(f"Node {id(self)}: Calculated reward = {rewards}")
        return sum(rewards) / len(rewards)

    def skip_backprop(self) -> bool:
        """
        Do not skip backpropagation.
        """
        return False