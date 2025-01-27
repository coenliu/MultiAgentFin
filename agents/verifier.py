# verifier.py
from autogen_core import (
    MessageContext,
    RoutedAgent,
    TopicId,
    TypeSubscription,
    message_handler,
    type_subscription,
)
from autogen_core.models import ChatCompletionClient, SystemMessage, UserMessage
from dataclass import extractor_topic_type, ReviewExtractResults, ReviewExtract, reasoner_topic_type, ActionResults,ReasonerActionTask, TASK_CONTEXT_MAPPING, verifier_topic_type, Message, TaskContext, VerifyTask, OutputTask, output_topic_type, VerifierResults
from prompts import SYS_PROMPT_VERIFICATION, construct_review_extractor_prompt
from agents.rag.retrieval import FormulaRetriever
import json

@type_subscription(topic_type=verifier_topic_type)
class VerifierAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A verifier agent.")
        self._system_message = SystemMessage(
            content=SYS_PROMPT_VERIFICATION
        )
        self._model_client = model_client
        self.formula_retriever = FormulaRetriever(collection_name="my_collection")


    @message_handler
    async def handle_final_answer(self, message: VerifyTask, ctx: MessageContext) -> None:
        task_id = message.task_id
        task_context = TASK_CONTEXT_MAPPING[task_id]
        #TODO
        prompt = f"""You need to evaluate following and give your review comments: \n
        reasoner agent result:  {task_context.reasoner_task.get_formula_from_reason()} \n
        extractor agent result: {task_context.extractor_task.get_extracted_var()} \n
        executor agent result:  {task_context.executor_task.get_code()}\n Answer: {task_context.executor_task.get_answer()}
        **Format your response as JSON**

        """
        llm_result = await self._model_client.create(
            messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
            cancellation_token=ctx.cancellation_token,
        )
        response = llm_result.content
        assert isinstance(response, str)

        #TODO need to extract responding results
        verifier_result = VerifierResults(
            session_id="",
            reasoner_comment=response,
            extractor_comment="",
            executor_comment="",
            approved=False,
        )

        output_task = OutputTask(task="", task_id=message.task_id)
        task_context.verify_task = VerifyTask(task=message.task, task_id=message.task_id)
        task_context.verify_task.results.append(verifier_result)

        await self.publish_message(message=output_task, topic_id=TopicId(output_topic_type, source=self.id.key))

    @message_handler
    async def handle_reasoner_action(self, message: ReasonerActionTask, ctx: MessageContext) -> None:
        prompt = message.action

        #TODO should have logic to find the query
        query_text = "Gross Profit"  # Replace with dynamic query if needed
        query_results = self.formula_retriever.query_collection(query=query_text, n_results=2)

        if query_results:
            # Process query_results as needed
            # For example, include query results in the prompt or use them in decision-making
            formatted_results = json.dumps(query_results, indent=4)
            #TODO need to filter the formatted results
            prompt += f"\nRelated Formulas:\n{formatted_results}"
        else:
            prompt += "\nNo related formulas found."

        llm_result = await self._model_client.create(
            messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
            cancellation_token=ctx.cancellation_token,
        )
        response = llm_result.content
        assert isinstance(response, str)
        result = ActionResults(
           results=response
        )

        await self.publish_message(message=result, topic_id=TopicId(reasoner_topic_type, self.id.key))

    @message_handler
    async def handle_extract_review(self, message: ReviewExtract, ctx: MessageContext) -> None:
        prompt = construct_review_extractor_prompt(question=message.question, context=message.context, extraxt_results=message.extraxt_results)
        llm_result = await self._model_client.create(
            messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
            cancellation_token=ctx.cancellation_token,
        )
        response = llm_result.content
        assert isinstance(response, str)

        result = ReviewExtractResults(
            results=response
        )

        await self.publish_message(message=result, topic_id=TopicId(extractor_topic_type, self.id.key))
