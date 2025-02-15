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
from dataclass import executor_topic_type,ExecuteTask, ReviewExecute, extractor_topic_type, ReviewExtractResults, ReviewExtract, reasoner_topic_type, ActionResults,ReasonerActionTask, TASK_CONTEXT_MAPPING, verifier_topic_type, Message, TaskContext, VerifyTask, OutputTask, output_topic_type, VerifierResults
from prompts import SYS_PROMPT_VERIFICATION, construct_review_extractor_prompt, SYS_PROMPT_EXECUTE_VERIFICATION
from agents.rag.retrieval import FormulaRetriever
import json
from agents.utils import format_query_results,extract_approved
@type_subscription(topic_type=verifier_topic_type)
class VerifierAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A verifier agent.")
        self._system_message = SystemMessage(
            content=SYS_PROMPT_VERIFICATION
        )
        self._model_client = model_client
        self.formula_retriever = FormulaRetriever(collection_name="my_collection")
        self._execute_review_message = SystemMessage(
            content=SYS_PROMPT_EXECUTE_VERIFICATION
        )
        self.current_turn = 0


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

        query_text = message.question
        query_results = self.formula_retriever.query_collection(query=query_text, n_results=2)

        if query_results:
            # Process query_results as needed
            # For example, include query results in the prompt or use them in decision-making
            # formatted_results = json.dumps(query_results, indent=4)
            #TODO need to filter the formatted results
            formatted_results = format_query_results(query_result=query_results)
            prompt += f"\nHERE IS RELATED FORMULA TO HELP YOU DECIDE SCORE:\n{formatted_results}"

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

    @message_handler
    async def handle_execute_review(self, message: ReviewExecute, ctx: MessageContext) -> None:
        task_id = message.task_id
        task_context = TASK_CONTEXT_MAPPING[task_id]
        max_turn = 6

        if self.current_turn >= max_turn:
            output_task = OutputTask(task="", task_id=message.task_id)
            await self.publish_message(message=output_task, topic_id=TopicId(output_topic_type, source=self.id.key))
            self.current_turn = 0  # Reset the turn counter.
            return

        prompt = f"""What’s the problem with the above code? You should check the code line by line. \n.
        give your review comments: \n
        executor agent code:  {message.code}\n code executed results: {message.code_res}
        if there is ValueError, SyntaxError etc, you should set Approved: False
        **Format your response as JSON** 
        ...
        End your response with: Approved: True or False.
        """
        #
        llm_result = await self._model_client.create(
            messages=[self._execute_review_message, UserMessage(content=prompt, source=self.id.key)],
            cancellation_token=ctx.cancellation_token,
        )
        response = llm_result.content
        assert isinstance(response, str)

        last_result = task_context.executor_task.results[-1]
        last_result.review = response

        verifier_result = VerifierResults(
            session_id="",
            reasoner_comment="",
            extractor_comment="",
            executor_comment=response,
            approved=False,
        )
        task_context.verify_task = VerifyTask(task="", task_id=message.task_id)
        task_context.verify_task.results.append(verifier_result)

        # if approve
        if extract_approved(input_text=response):
            output_task = OutputTask(task="", task_id=message.task_id)
            await self.publish_message(message=output_task, topic_id=TopicId(output_topic_type, source=self.id.key))
            self.current_turn = 0
            return

        self.current_turn += 1
        task_context.executor_task.update_review(review=response)
        executor_task = ExecuteTask(task="", task_id=task_id)
        await self.publish_message(executor_task, topic_id=TopicId(executor_topic_type, source=self.id.key))