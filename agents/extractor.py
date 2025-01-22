# extractor.py

from autogen_core import (
    MessageContext,
    RoutedAgent,
    TopicId,
    TypeSubscription,
    message_handler,
    type_subscription,
)
from autogen_core.models import ChatCompletionClient, SystemMessage, UserMessage
from dataclass import TASK_CONTEXT_MAPPING, extractor_topic_type, executor_topic_type, ExtractTask, ReasonTask, ReasonerResults, ExecuteTask, \
    TaskContext, ExtractorResults
from prompts import SYS_PROMPT_EXTRACTOR,construct_extractor_prompt
from typing import Dict, List
from modules.bm25 import BM25Model
from .utils import extract_formula, extract_variables, split_variables_from_formula

@type_subscription(topic_type=extractor_topic_type)
class ExtractorAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient, top_n_chunk: int) -> None:
        super().__init__("A extractor agent.")
        self._system_message = SystemMessage(
            content=SYS_PROMPT_EXTRACTOR
        )
        self._model_client = model_client
        self._session_memory: Dict[str, List[ ReasonTask | ReasonerResults]] = {}
        self._bm25_model = BM25Model(model_name="BM25_Extractor", top_k=top_n_chunk)
        self.current_question = ""
        self.current_context = ""

    @message_handler
    async def handle_extract_task(self, message: ExtractTask, ctx: MessageContext) -> None:
        task_id = message.task_id
        task_context = TASK_CONTEXT_MAPPING[task_id]
        #TODO need to load comments from Verifier
        raw_response =  task_context.reasoner_task.get_var_from_reason()
        self.current_question = task_context.input_data.question
        self.current_context = task_context.input_data.context

        variables = extract_variables(raw_response)
        context = task_context.input_data.context

        relevant_chunks = self._bm25_model.get_top_chunks(query=self.current_question, passage=context)

        prompt = construct_extractor_prompt(variables=variables, relevant_chunks=relevant_chunks, input_question=self.current_question)
        # TODO need to abstract
        llm_result = await self._model_client.create(
            messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
            cancellation_token=ctx.cancellation_token,
        )
        response = llm_result.content
        assert isinstance(response, str)

        extractor_results = ExtractorResults(
            extracted_var_value=f"Variables: {variables} \n Extracted:{response}",
            review="pending"
        )
        executor_task = ExecuteTask(
            task="",
            task_id=message.task_id
        )

        task_context.extractor_task = ExtractTask(task=message.task, task_id=message.task_id)
        task_context.extractor_task.results.append(extractor_results)
        await self.publish_message(executor_task, topic_id=TopicId(executor_topic_type, source=self.id.key))
