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
from dataclass import ReviewExtractResults, ReviewExtract, TASK_CONTEXT_MAPPING, extractor_topic_type, executor_topic_type, ExtractTask, ReasonTask, ReasonerResults, ExecuteTask, \
    TaskContext, ExtractorResults,verifier_topic_type
from prompts import SYS_PROMPT_EXTRACTOR,construct_extractor_prompt_1_turn
from typing import Dict, List
from modules.bm25 import BM25Model
from .utils import extract_variables

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
        self.task_id = ""

    @message_handler
    async def handle_extract_task(self, message: ExtractTask, ctx: MessageContext) -> None:
        self.task_id = message.task_id  # Set the current task_id
        task_context = TASK_CONTEXT_MAPPING[self.task_id]

        raw_response =  task_context.reasoner_task.get_var_from_reason()
        self.current_question = task_context.input_data.question
        self.current_context = task_context.input_data.context

        variables = extract_variables(raw_response)
        context = task_context.input_data.context

        relevant_chunks = self._bm25_model.get_top_chunks(query=self.current_question, passage=context)

        if self.current_context == None:
            self.current_context = self.current_question

        prompt = construct_extractor_prompt_1_turn(variables=variables, relevant_chunks=self.current_context, input_question=self.current_question)
        # TODO need to abstract
        response = await self.send_request(prompt=prompt, ctx=ctx)

        #TODO for test extract
        executor_task = ExecuteTask(
            task="",
            task_id=self.task_id
        )
        extractor_results = ExtractorResults(
            extracted_var_value=f"Variables: {variables} \n Extracted:{response}",
            review="not set",
        )

        task_context.extractor_task = ExtractTask(task="", task_id=self.task_id)
        task_context.extractor_task.results.append(extractor_results)

        await self.publish_message(executor_task, topic_id=TopicId(executor_topic_type, source=self.id.key))

        # TODO for verify agent
        # await self.send_review_task(response=response)

    async def send_request(self, prompt: str, ctx: MessageContext) -> str:
        """
        Sends a request to the ChatCompletionClient and returns the response content.
        """
        llm_result = await self._model_client.create(
            messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
            cancellation_token=ctx.cancellation_token,
        )
        response = llm_result.content
        assert isinstance(response, str)
        return response

    async def send_review_task(self, response:str) -> None:
        review_task = ReviewExtract(
            question=self.current_question,
            context=self.current_context,
            extraxt_results=response
        )
        await self.publish_message(review_task, topic_id=TopicId(verifier_topic_type, source=self.id.key))

    @message_handler
    async def handle_extract_review_res(self, message: ReviewExtractResults, ctx: MessageContext) -> None:
        response = await self.send_request(prompt=message.results, ctx=ctx)

        task_context = TASK_CONTEXT_MAPPING.get(self.task_id)

        prompt = f"Based on the reviewed results： {response}, answer the question again  \n"

        re_answer = await self.send_request(prompt=prompt, ctx=ctx)

        executor_task = ExecuteTask(
            task="",
            task_id=self.task_id
        )
        variables = extract_variables(re_answer)
        extractor_results = ExtractorResults(
            extracted_var_value=f"Variables: {variables} \n Extracted:{re_answer}",
            review=response,
        )

        task_context.extractor_task = ExtractTask(task="", task_id=self.task_id)
        task_context.extractor_task.results.append(extractor_results)
        await self.publish_message(executor_task, topic_id=TopicId(executor_topic_type, source=self.id.key))
