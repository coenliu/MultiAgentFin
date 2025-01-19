# mcts/mcts_custom.py

from .MCTS import MCTS_Searcher, MCTS_Node, verbose_print
from typing import List, Callable,Awaitable
from .reason_node import ReasoningNode
import asyncio
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class MCTS_Searcher_Custom(MCTS_Searcher):
    """
    Custom MCTS Searcher tailored for ReasonerAgent and ReasoningNode.
    Handles per-action reward fetching via a callback provided by ReasonerAgent.
    """
    def __init__(
        self,
        exploration_weight: float = 1.414,
        weight_scheduler: str = "exp",
        num_rollouts: int = 1000,
        discount: float = 1.0,
        get_reward_func: Callable[[str], Awaitable[float]] = None,
        verbose: bool = False,
        max_concurrent_tasks: int = 1,
    ):
        super().__init__(
            exploration_weight=exploration_weight,
            weight_scheduler=weight_scheduler,
            num_rollouts=num_rollouts,
            discount=discount,
            verbose=verbose
        )
        self.get_reward_func = get_reward_func
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def run_rollouts(self, root_node: ReasoningNode) -> List[str]:
        """
        Performs rollouts asynchronously and returns the best action sequence based on cumulative rewards.
        """
        try:
            rollout_tasks = [self.do_rollout(root_node, rollout_id) for rollout_id in range(self.num_rollouts)]
            logger.debug(f"Starting {self.num_rollouts} rollouts.")
            await asyncio.gather(*rollout_tasks)
            logger.debug("All rollouts completed.")

            # Step 2: Traverse the tree to extract the best action sequence
            best_action_sequence = []
            current_node = root_node

            while current_node in self.parent2children:
                children = self.parent2children[current_node]
                if not children:
                    break  # No further actions possible

                # Select the child with the highest Q[c]/N[c] ratio
                best_child = max(
                    children,
                    key=lambda c: self.Q[c] / self.N[c] if self.N[c] > 0 else 0
                )

                # Append the latest action taken to reach this child
                last_action = best_child.state.get('actions_taken', [])[-1] if best_child.state.get(
                    'actions_taken') else None
                if last_action:
                    best_action_sequence.append(last_action)

                # Move to the next node in the path
                current_node = best_child

            logger.info(f"Best action sequence: {best_action_sequence}")
            return best_action_sequence
        except Exception as e:
            logger.error(f"Error during rollouts: {e}")
            raise


    async def do_rollout(self, root_node: ReasoningNode, rollout_id: int):
        """
        Perform a single rollout asynchronously.
        """
        async with self.semaphore:
            verbose_print("==> Selecting a node...", self.verbose)
            path = await self._select(root_node, rollout_id)
            leaf = path[-1]
            verbose_print(f"==> Expanding node {leaf.id}...", self.verbose)
            await self._expand(leaf, rollout_id)
            verbose_print(f"==> Simulating node {leaf.id}...", self.verbose)
            simulation_path = await self._simulate(leaf, rollout_id)
            verbose_print(f"==> Backpropagating...", self.verbose)
            await self._backpropagate(path + simulation_path)

    async def _simulate(self, node: 'ReasoningNode', rollout_id: int) -> List['ReasoningNode']:
        """
        Simulate a rollout from the given node to obtain a list of nodes with accumulated rewards.
        """
        simulation_path = []
        current_node = node

        while not current_node.is_terminal():
            possible_actions = current_node.state['possible_actions']
            if not possible_actions:
                break
            action = random.choice(possible_actions)
            # Asynchronously get the reward for the action
            score = await self.get_reward_func(action)
            current_node.state['action_rewards'].append(score)
            # Move to the next state
            new_state = {
                'actions_taken': current_node.state['actions_taken'] + [action],
                'current_action_index': current_node.state['current_action_index'] + 1,
                'action_rewards': current_node.state['action_rewards'].copy(),
                'possible_actions': [a for a in possible_actions if a != action]
            }
            child_node = ReasoningNode(state=new_state, parent=current_node, action=action)
            simulation_path.append(child_node)
            current_node = child_node

        return simulation_path

    async def _backpropagate(self, path: List[MCTS_Node]):
        """
        Backpropagate the reward through the path.
        """
        if not path:
            return

        leaf = path[-1]
        reward = leaf.calculate_reward()
        logger.debug(f"Backpropagating reward {reward} through path {[node.id for node in path]}.")

        for node in reversed(path):
            self.Q[node] += reward
            self.N[node] += 1
            self.explored_nodes.add(node)

    async def _select(self, node: MCTS_Node, rollout_id: int) -> List[MCTS_Node]:
        """
        Find an unexplored descendant of `node` and return the path.
        """
        path = []
        while True:
            path.append(node)
            if node not in self.parent2children.keys():
                return path

            unexplored = [n for n in self.parent2children[node] if n not in self.explored_nodes]
            if unexplored:
                n = random.choice(unexplored)
                path.append(n)
                return path

            node = self._uct_select(node, rollout_id)