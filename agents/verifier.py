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
from dataclass import TASK_CONTEXT_MAPPING, verifier_topic_type, Message, TaskContext, VerifyTask, OutputTask, output_topic_type, VerifierResults
from prompts import SYS_PROMPT_VERIFICATION

@type_subscription(topic_type=verifier_topic_type)
class VerifierAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A verifier agent.")
        self._system_message = SystemMessage(
            content=SYS_PROMPT_VERIFICATION
        )
        self._model_client = model_client


    @message_handler
    async def handle_user_description(self, message: VerifyTask, ctx: MessageContext) -> None:
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
        print(f"{'-'*80}\n{self.id.type}:\n{response}")

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
