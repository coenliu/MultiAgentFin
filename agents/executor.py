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
from dataclass import ReviewExecute, TASK_CONTEXT_MAPPING, executor_topic_type, verifier_topic_type, Message, TaskContext, ExecuteTask, ExecutorResults, VerifyTask
from prompts import SYS_PROMPT_EXECUTOR
from autogen import ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor
import tempfile
from .utils import extract_formula

@type_subscription(topic_type=executor_topic_type)
class ExecutorAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A code executor agent.")
        self._system_message = SystemMessage(
            content=SYS_PROMPT_EXECUTOR
        )
        self._model_client = model_client

    @message_handler
    async def handle_execute_task(self, message: ExecuteTask, ctx: MessageContext) -> None:
        task_id = message.task_id
        task_context = TASK_CONTEXT_MAPPING[task_id]
        formula = extract_formula(task_context.reasoner_task.get_formula_from_reason())
        # Check if this is an initial execution or a review-based execution
        if not task_context.executor_task or not task_context.executor_task.results:
            prompt = (f"Please NOTE You are tasked with writing Python code based on the provided context."   
                      f"Here is the formula {formula} \n"
                      f"Here is the extracted value {task_context.extractor_task.get_extracted_var()}.\n"
                      f"You need to end with code by print(answer). And answer within 10 lines of code.")
            llm_result = await self._model_client.create(
                messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
                cancellation_token=ctx.cancellation_token,
            )
            response = llm_result.content
            assert isinstance(response, str)

            code_res = self.run_code(response)

            executor_res = ExecutorResults(
                code=response,
                answer=code_res,
                review="pending"
            )

            task_context.executor_task = ExecuteTask(task=message.task, task_id=message.task_id)
            task_context.executor_task.results.append(executor_res)

            review_execute = ReviewExecute(
                task_id=message.task_id,
                code=response,
                code_res=code_res,
            )
            await self.publish_message(review_execute, topic_id=TopicId(verifier_topic_type, source=self.id.key))

        else:
            last_result = task_context.executor_task.results[-1]
            review_results = last_result.review
            formula = extract_formula(task_context.reasoner_task.get_formula_from_reason())

            prompt = (f"Please NOTE You are tasked with writing Python code based on the provided context." 
                      f"Here is the formula {formula} \n"
                      f"Here is the extracted value {task_context.extractor_task.get_extracted_var()}.\n"
                      f"Here are the comments from the Verifier agent to help you refine your answer: {review_results}\n"
                      f"Refine your code accordingly. Ensure it ends with print(answer) and within 10 lines.")

            llm_result = await self._model_client.create(
                messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
                cancellation_token=ctx.cancellation_token,
            )
            response = llm_result.content
            assert isinstance(response, str)

            code_res = self.run_code(response)

            # Update the last ExecutorResults with the new response
            last_result.code = response
            last_result.answer = code_res

            executor_res = ExecutorResults(
                code=response,
                answer=code_res,
                review=review_results
            )
            task_context.executor_task.results.append(executor_res)

            review_execute = ReviewExecute(
                task_id=message.task_id,
                code=response,
                code_res=code_res,
            )
            await self.publish_message(review_execute, topic_id=TopicId(verifier_topic_type, source=self.id.key))

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
        )
        # print(f"The code input:{'-' * 80}\n{self.id.type}:\n {message_with_code_block}")
        reply = code_executor_agent.generate_reply(messages=[{"role": "user", "content": message_with_code_block}])
        # print(f"The code output:{'-' * 80}\n{self.id.type}:\n {reply}")
        return reply