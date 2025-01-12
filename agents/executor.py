# executor.py

from autogen_core import (
    MessageContext,
    RoutedAgent,
    TopicId,
    TypeSubscription,
    message_handler,
    type_subscription,
)
from autogen_core.models import ChatCompletionClient, SystemMessage, UserMessage
from dataclass import executor_topic_type, verifier_topic_type, Message, TaskContext, ExecuteTask, ExecutorResults, VerifyTask
from prompts import SYS_PROMPT_EXECUTOR
from autogen import ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor
import tempfile

@type_subscription(topic_type=executor_topic_type)
class ExecutorAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient, task_context: TaskContext) -> None:
        super().__init__("A code executor agent.")
        self._system_message = SystemMessage(
            content=SYS_PROMPT_EXECUTOR
        )
        self._model_client = model_client
        self._task_context = task_context


    @message_handler
    async def handle_user_description(self, message: ExecuteTask, ctx: MessageContext) -> None:
        #TODO
        # pass
        prompt = (f"Here is the formula {self._task_context.reasoner_task.get_formula_from_reason()} \n"
                  f"Here is the extracted value {self._task_context.extractor_task.get_extracted_var()}")

        # print(f"{'-' * 80}\n{self.id.type}:\n {prompt}")
        llm_result = await self._model_client.create(
            messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
            cancellation_token=ctx.cancellation_token,
        )
        response = llm_result.content
        assert isinstance(response, str)
        print(f"{'-'*80}\n{self.id.type}:\n{response}")

        code_res = self.run_code(response)

        executor_res = ExecutorResults(
            code=response,
            answer=code_res,
            review="pending"
        )

        # print(f"{'-' * 80}\n{self.id.type}:\n {code_res}")
        self._task_context.executor_task = ExecuteTask(task=message.task)
        self._task_context.executor_task.results.append(executor_res)

        verify_task = VerifyTask(task="")

        await self.publish_message(verify_task, topic_id=TopicId(verifier_topic_type, source=self.id.key))

    def run_code(self, message_with_code_block: str) -> str:
        temp_dir = tempfile.TemporaryDirectory()
        executor = LocalCommandLineCodeExecutor(
            timeout=10,  # Timeout for each code execution in seconds.
            work_dir=temp_dir.name,  # Use the temporary directory to store the code files.
        )
        code_executor_agent = ConversableAgent(
            "code_executor_agent",
            llm_config=False,  # Turn off LLM for this agent.
            code_execution_config={"executor": executor},  # Use the local command line code executor.
            # human_input_mode="ALWAYS",  # Always take human input for this agent for safety.
        )
        print(f"The code input:{'-' * 80}\n{self.id.type}:\n {message_with_code_block}")
        reply = code_executor_agent.generate_reply(messages=[{"role": "user", "content": message_with_code_block}])
        print(f"The code output:{'-' * 80}\n{self.id.type}:\n {reply}")
        return reply