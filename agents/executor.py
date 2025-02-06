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
import textwrap
import io
import sys


@type_subscription(topic_type=executor_topic_type)
class ExecutorAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A code executor agent.")
        self._system_message = SystemMessage(
            content=SYS_PROMPT_EXECUTOR
        )
        self._model_client = model_client

    def _has_code_error(self, output: str) -> bool:
        error_keywords = ["Traceback", "NameError", "SyntaxError", "TypeError", "ValueError", "IndexError","KeyError", "AttributeError", "Error"]
        return any(keyword in output for keyword in error_keywords)

    @message_handler
    async def handle_execute_task(self, message: ExecuteTask, ctx: MessageContext) -> None:
        task_id = message.task_id
        task_context = TASK_CONTEXT_MAPPING[task_id]
        formula = task_context.reasoner_task.get_formula_from_reason()

        if not task_context.executor_task or not task_context.executor_task.results:
            prompt = (f"Please NOTE You are tasked with writing Python code based on the provided context."
                      f"Here is the formula from other assistant {formula} \n"
                      f"Here is the extracted value {task_context.extractor_task.get_extracted_var()}.\n"
                      f"Make sure that initialize extracted value at the start of your code.\n"
                      f"You need to end with code by print(answer). And answer within 10 lines of code.")
        else:
            review_results = task_context.executor_task.results[-1].review
            prompt = (f"Please NOTE You are tasked with writing Python code based on the provided context."
                      f"Here is the formula other assistant {formula} \n"
                      f"Here is the extracted value {task_context.extractor_task.get_extracted_var()}.\n"
                      f"Make sure that initialize extracted value at the start of your code.\n"
                      f"Here are the comments from the Verifier agent to help you refine your answer: {review_results}\n"
                      f"Refine your code accordingly. Ensure it ends with print(answer) and within 10 lines.")

        # llm_result = await self._model_client.create(
        #     messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
        #     cancellation_token=ctx.cancellation_token,
        # )
        # response = llm_result.content
        # assert isinstance(response, str)
        #
        # code_res = self.run_code(response)

        max_attempts = 3
        attempt = 0
        code_res = ""
        response = ""
        re_prompt = prompt

        while attempt < max_attempts:
            llm_result = await self._model_client.create(
                messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
                cancellation_token=ctx.cancellation_token,
            )
            response = llm_result.content
            assert isinstance(response, str)

            code_res_cli = self.run_code(response)
            code_res_inprocess = self.execute_python_code(response)
            combined_output = (
                f"Local Executor Output:\n{code_res_cli}\n\n"
                f"In-Process Executor Output:\n{code_res_inprocess}"
            )

            if not self._has_code_error(code_res) and not self._has_code_error(code_res_inprocess):
                code_res = combined_output
                break
            else:
                prompt = (
                    f"Your previous code produced the following error:\n{combined_output}\n"
                    f"{re_prompt}"
                    f"Your previous Code: {response}"
                )
                attempt += 1
                code_res = combined_output

        executor_res = ExecutorResults(
            code=response,
            answer=code_res,
            review="pending" if not task_context.executor_task or not task_context.executor_task.results else
            task_context.executor_task.results[-1].review
        )

        if not task_context.executor_task:
            task_context.executor_task = ExecuteTask(task=message.task, task_id=message.task_id)

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

    def execute_python_code(self, code: str) -> str:

        code = textwrap.dedent(code).lstrip()

        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        try:
            exec(code, {})  # Execute in an isolated global namespace.
        except Exception as e:
            result = f"Error during code execution: {e}"
        else:
            result = buffer.getvalue()
        finally:
            sys.stdout = old_stdout
        return result.strip()