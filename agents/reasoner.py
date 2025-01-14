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
from dataclass import TASK_CONTEXT_MAPPING, ReasonTask, VerifierResults,Message, ReasonerResults, ExtractTask, reasoner_topic_type, extractor_topic_type,TaskContext
from prompts import SYS_PROMPT_REASONER, construct_reason_prompt
from typing import Dict, List
import uuid

@type_subscription(topic_type=reasoner_topic_type)
class ReasonerAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A formula and variable identify agent.")
        self._system_message = SystemMessage(
            content=SYS_PROMPT_REASONER
        )
        self._model_client = model_client
        self._session_memory: Dict[str, List[VerifierResults | ReasonTask]] = {}


    @message_handler
    async def handle_reason_task(self, message: ReasonTask, ctx: MessageContext) -> None:
        task_id = message.task_id
        task_context = TASK_CONTEXT_MAPPING[task_id]
        prompt = construct_reason_prompt(task_context.input_data)
        session_id = str(uuid.uuid4())
        self._session_memory.setdefault(session_id, []).append(message)

        #TODO need to abstract
        llm_result = await self._model_client.create(
            messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
            cancellation_token=ctx.cancellation_token,
        )
        response = llm_result.content
        assert isinstance(response, str)
        # print(f"{'-'*80}\n{self.id.type}:\n{response}")

        #TODO need to save the response to reasoner results

        #TODO need to extract the  variables from response

        # extract_res = ExtractorResults(
        #     review="Pending"
        # )
        # extract_res.add_reasoner_var_extractor(reasoner_vars=response)
        #
        reasoner_results = ReasonerResults(
            review="Review content",
            formulas=response,
            variables=response
        )

        extract_task = ExtractTask(
            task="",
            task_id=message.task_id
        )

        # Update task context
        task_context.reasoner_task = ReasonTask(task=message.task, task_id=message.task_id)
        task_context.reasoner_task.results.append(reasoner_results)

        await self.publish_message(message=extract_task, topic_id=TopicId(extractor_topic_type, source=self.id.key))