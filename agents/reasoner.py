# reasoner.py
from autogen_core import (
    MessageContext,
    RoutedAgent,
    TopicId,
    TypeSubscription,
    message_handler,
    type_subscription,
)
from autogen_core.models import ChatCompletionClient, SystemMessage, UserMessage
from dataclass import VerifyTask, verifier_topic_type, ActionResults,ReasonerActionTask, TASK_CONTEXT_MAPPING, ReasonTask, VerifierResults,Message, ReasonerResults, ExtractTask, reasoner_topic_type, extractor_topic_type,TaskContext
from prompts import SYS_PROMPT_REASONER, construct_reason_prompt, ACTIONS, construct_action_evaluation_prompt
from typing import Dict, List, Optional
import uuid
from mcts.mcts_custom import MCTS_Searcher_Custom
from mcts.reason_node import ReasoningNode
import logging
import asyncio
import concurrent.futures
import re
from .utils import extract_formula, extract_variables, split_variables_from_formula


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
@type_subscription(topic_type=reasoner_topic_type)
class ReasonerAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A formula and variable identify agent.")
        self._system_message = SystemMessage(
            content=SYS_PROMPT_REASONER
        )
        self._model_client = model_client
        self._session_memory: Dict[str, List[VerifierResults | ReasonTask]] = {}
        self._mcts_searcher: Optional[MCTS_Searcher_Custom] = None
        self.current_question = ""
        self.current_context = ""
        self.action_queue: asyncio.Queue = asyncio.Queue()

        
    async def get_reward_async(self, action: str) -> float:
        future = asyncio.get_event_loop().create_future()
        await self.action_queue.put(future)

        await self.action_to_verifier(action)
        logger.info(f"Submitted action '{action}' for evaluation. Awaiting score...")
        try:
            score = await asyncio.wait_for(future, timeout=10)  #  # Adjust timeout as needed
            logger.info(f"Received score {score} for action '{action}'.")
        except concurrent.futures.TimeoutError:
            logger.error("Timeout while waiting for VerifierAgent response.")
            score = 0.0
        except Exception as e:
            logger.error(f"Error while fetching reward: {e}")
            score = 0.0

        return score

    @property
    def mcts_searcher(self) -> MCTS_Searcher_Custom:
        """
        Lazy initializer for MCTS_Searcher_Custom.
        """
        if self._mcts_searcher is None:
            self._mcts_searcher = MCTS_Searcher_Custom(
                exploration_weight=1.414,
                weight_scheduler="exp",
                num_rollouts=1, # default should 20
                discount=1.0,
                get_reward_func=self.get_reward_async,
                verbose=False
            )
            logger.info("Initialized MCTS_Searcher_Custom.")
        return self._mcts_searcher

    async def perform_mcts_search(self) -> List[str]:
        try:
            initial_state = {
                'actions_taken': [],
                'current_action_index': 0,
                'action_rewards': [],
                'possible_actions': list(ACTIONS.keys())
            }
            root_node = ReasoningNode(state=initial_state)

            logger.info("Starting MCTS rollouts.")
            best_action_sequence = await self.mcts_searcher.run_rollouts(root_node)
            logger.info(f"Completed MCTS rollouts. Best Action Sequence: {best_action_sequence}")

            return best_action_sequence
        except Exception as e:
            logger.error(f"Error during MCTS search: {e}")
            return []

    @message_handler
    async def handle_reason_task(self, message: ReasonTask, ctx: MessageContext) -> None:
        task_id = message.task_id
        task_context = TASK_CONTEXT_MAPPING[task_id]
        prompt = construct_reason_prompt(task_context.input_data)
        session_id = str(uuid.uuid4())
        self._session_memory.setdefault(session_id, []).append(message)
        self.current_question = task_context.input_data.question
        self.current_context = task_context.input_data.context

        best_action_sequence = await self.perform_mcts_search()

        if not best_action_sequence:
            logger.error("MCTS failed to determine a best action sequence. Aborting task.")
            return

        response = await self.execute_action_sequence(best_action_sequence, prompt, ctx.cancellation_token)

        reasoner_results = ReasonerResults(
            review="Review content",
            raw_response=response,
            formulas=response,
            variables=response,
            actions=best_action_sequence,
        )

        extract_task = ExtractTask(
            task="",
            task_id=message.task_id
        )

        task_context.reasoner_task = ReasonTask(task=message.task, task_id=message.task_id)
        task_context.reasoner_task.results.append(reasoner_results)

        await self.publish_message(message=extract_task, topic_id=TopicId(extractor_topic_type, source=self.id.key))

    async def execute_action_sequence(self, actions: List[str], initial_prompt: str, cancellation_token) -> str:
        """
        Executes the sequence of actions to derive the final answer.
        """
        aggregated_response = ""
        current_prompt = initial_prompt

        for action in actions:
            action_prompt = self.construct_action_prompt(action, current_prompt)
            llm_result = await self._model_client.create(
                messages=[self._system_message, UserMessage(content=action_prompt, source=self.id.key)],
                cancellation_token=cancellation_token,
            )
            response = llm_result.content
            assert isinstance(response, str)
            aggregated_response += response + " "
            current_prompt = response

        final_answer = self.process_aggregated_response(aggregated_response)
        return final_answer

    def construct_action_prompt(self, action: str, previous_response: str) -> str:
        """
        Constructs a prompt based on the current action and previous response.
        """
        action_prompt = ACTIONS.get(action, "")

        if previous_response:
            final_prompt = f"{previous_response}\n\n{action_prompt}"
        else:
            final_prompt = action_prompt
        return final_prompt

    def process_aggregated_response(self, aggregated_response: str) -> str:
        """
        Processes the aggregated responses from all actions to form the final answer.
        """
        return aggregated_response.strip()

    async def action_to_verifier(self, action: str) -> None:
        try:
            prompt = construct_action_evaluation_prompt(current_question=self.current_question, current_context=self.current_context,action=action)
            action_task = ReasonerActionTask(task="", action=prompt)
            await self.publish_message(message=action_task, topic_id=TopicId(verifier_topic_type, source=self.id.key))

        except asyncio.TimeoutError:
            logger.error("Timeout while sending action to VerifierAgent.")
            if not self.action_queue.empty():
                future = await self.action_queue.get()
                if not future.done():
                    future.set_result(0.0)  # Assign default score
                    logger.info("Assigned default score 0.0 due to timeout.")
        except Exception as e:
            logger.error(f"Error while sending action to VerifierAgent: {e}")
            if not self.action_queue.empty():
                future = await self.action_queue.get()
                if not future.done():
                    future.set_result(0.0)  # Assign default score
                    logger.info("Assigned default score 0.0 due to error.")


    @message_handler
    async def get_action_score(self, message:ActionResults, ctx: MessageContext) -> None:
        json_str = message.results
        pattern = r'"score"\s*:\s*([0-9]*\.?[0-9]+)'

        match = re.search(pattern, json_str)
        if match:
            try:
                score = float(match.group(1))
                logger.info(f"Extracted score using regex: {score}")
            except ValueError:
                logger.warning(f"Invalid score format: {match.group(1)}. Defaulting to 0.0.")
                score = 0.0
        else:
            logger.warning("No 'score' field found in the message. Defaulting to 0.0.")
            score = 0.0

        if not self.action_queue.empty():
            future = await self.action_queue.get()
            if not future.done():
                future.set_result(float(score))
                logger.info(f"Score {score} set in the next action's Future.")
            else:
                logger.warning("Future is already done. Cannot set result.")
        else:
            logger.warning("No pending action in the queue. Ignoring the score.")



    # @message_handler
        # async def handle_reason_task(self, message: ReasonTask, ctx: MessageContext) -> None:
        #     task_id = message.task_id
        #     task_context = TASK_CONTEXT_MAPPING[task_id]
        #     prompt = construct_reason_prompt(task_context.input_data)
        #     session_id = str(uuid.uuid4())
        #     self._session_memory.setdefault(session_id, []).append(message)
        #
        #     # TODO need to abstract
        #     llm_result = await self._model_client.create(
        #         messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
        #         cancellation_token=ctx.cancellation_token,
        #     )
        #     response = llm_result.content
        #     assert isinstance(response, str)
        #     # print(f"{'-'*80}\n{self.id.type}:\n{response}")
        #
        #     # TODO need to save the response to reasoner results
        #
        #     # TODO need to extract the  variables from response
        #
        #     # extract_res = ExtractorResults(
        #     #     review="Pending"
        #     # )
        #     # extract_res.add_reasoner_var_extractor(reasoner_vars=response)
        #     #
        #     reasoner_results = ReasonerResults(
        #         review="Review content",
        #         formulas=response,
        #         variables=response
        #     )
        #
        #     extract_task = ExtractTask(
        #         task="",
        #         task_id=message.task_id
        #     )
        #
        #     # Update task context
        #     task_context.reasoner_task = ReasonTask(task=message.task, task_id=message.task_id)
        #     task_context.reasoner_task.results.append(reasoner_results)
        #
        #     await self.publish_message(message=extract_task, topic_id=TopicId(extractor_topic_type, source=self.id.key))