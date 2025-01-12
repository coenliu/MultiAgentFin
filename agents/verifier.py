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
from dataclass import verifier_topic_type, Message, TaskContext, VerifyTask
from prompts import SYS_PROMPT_VERIFICATION

@type_subscription(topic_type=verifier_topic_type)
class VerifierAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient, task_context: TaskContext) -> None:
        super().__init__("A verifier agent.")
        self._system_message = SystemMessage(
            content=SYS_PROMPT_VERIFICATION
        )
        self._model_client = model_client
        self._task_context = task_context


    @message_handler
    async def handle_user_description(self, message: VerifyTask, ctx: MessageContext) -> None:
        #TODO
        prompt = f"""You need to evaluate following and give your review comments: \n
        reasoner agent:  {self._task_context.reasoner_task.get_formula_from_reason()} \n
        extractor agent: {self._task_context.extractor_task.get_extracted_var()} \n
        executor agent:  {self._task_context.executor_task.get_code()} and {self._task_context.executor_task.get_answer()}
        """
        llm_result = await self._model_client.create(
            messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
            cancellation_token=ctx.cancellation_token,
        )
        response = llm_result.content
        assert isinstance(response, str)
        print(f"{'-'*80}\n{self.id.type}:\n{response}")

       # await self.publish_message(Message(response), topic_id=TopicId(extractor_topic_type, source=self.id.key))
