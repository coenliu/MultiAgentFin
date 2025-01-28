reasoner_topic_type = "ReasonerAgent"
extractor_topic_type = "ExtractorAgent"
verifier_topic_type = "VerifierAgent"
executor_topic_type = "ExecutorAgent"
user_topic_type = "User"
output_topic_type = "FormateOutput"

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union

@dataclass
class Message:
    content: str

@dataclass
class ReviewExtract:
    extraxt_results: str
    question: str
    context: str

@dataclass
class ReviewExtractResults:
    results: str

@dataclass
class ActionResults:
    results:str

@dataclass
class ReasonerResults:
    review: Optional[str]
    formulas: Optional[str]
    raw_response: Optional[str]
    variables: Optional[str] = None
    actions: Optional[List[str]] = None

    def add_variables(self, variables:str) -> None:
        """add the identified var results from reasoner to extractor"""
        if self.variables is None:
            self.variables = ""
        self.variables=variables
    def add_formulas(self, formulas:str) -> None:
        if self.formulas is None:
            self.formulas = ""
        self.formulas=formulas


@dataclass
class ExtractorResults:
    review: Optional[str]
    extracted_var_value: Optional[str] = None


@dataclass
class ExecutorResults:
    code:str
    answer:str
    review: str

@dataclass
class VerifierResults:
    session_id: str
    reasoner_comment:str
    extractor_comment:str
    executor_comment:str
    approved: bool

@dataclass
class ReasonTask:
    task: str
    task_id: str
    results: List[ReasonerResults] = field(default_factory=list)

    def get_var_from_reason(self) -> str:
        """
        Get the concatenated 'var_from_reason' from the latest ExtractorResults in the results list.
        """
        if not self.results:
            return ""
        return self.results[-1].variables

    def get_formula_from_reason(self) -> str:
        if not self.results:
            return ""
        return self.results[-1].formulas

    def get_actions_from_reason(self) -> List[str]:
        if not self.results:
            return []
        return self.results[-1].actions

@dataclass
class ExtractTask:
    task: str
    task_id: str
    results: List[ExtractorResults] = field(default_factory=list)

    def get_extracted_var(self) -> str:
        if not self.results:
            return ""
        return self.results[-1].extracted_var_value


@dataclass
class ExecuteTask:
    task: str
    task_id: str
    results: List[ExecutorResults] = field(default_factory=list)

    def get_code(self) -> str:
        if not self.results:
            return ""
        return self.results[-1].code

    def get_answer(self) -> str:
        if not self.results:
            return ""
        return self.results[-1].answer


@dataclass
class VerifyTask:
    task: str
    task_id: str
    results: List[VerifierResults] = field(default_factory=list)

    def get_verify_comment(self) -> str:
        if not self.results:
            return ""
        if not self.results:
            return ""

        latest_result = self.results[-1]
        comments = []

        if latest_result.reasoner_comment:
            comments.append(f"Reasoner Comment: {latest_result.reasoner_comment}")

        if latest_result.extractor_comment:
            comments.append(f"Extractor Comment: {latest_result.extractor_comment}")

        if latest_result.executor_comment:
            comments.append(f"Executor Comment: {latest_result.executor_comment}")

        approval_status = "Approved" if latest_result.approved else "Not Approved"
        comments.append(f"Approval Status: {approval_status}")

        return "\n".join(comments)

@dataclass
class ReasonerActionTask:
    task: str
    action: str
    question: str

@dataclass
class OutputTask:
    task: str
    task_id: str
    # results:str

@dataclass
class TaskInput:
    """
    Represents the input data for a task.
    """
    question: str
    answer: Optional[str] = None
    task: str = ""
    context: str = ""
    context_type: Optional[str] = None
    options: Optional[List[str]] = None
    program: Optional[str] = None

@dataclass
class TaskContext:
    input_data: Optional[TaskInput] = None
    reasoner_task: Optional[ReasonTask] = None
    extractor_task: Optional[ExtractTask] = None
    executor_task: Optional[ExecuteTask] = None
    verify_task: Optional[VerifyTask] = None
    
    def add_task(self, task: Union[ReasonTask, ExtractTask, ExecuteTask, VerifyTask]) -> None:
        if isinstance(task, ReasonTask):
            self.reasoner_task = task
        elif isinstance(task, ExtractTask):
            self.extractor_task = task
        elif isinstance(task, ExecuteTask):
            self.executor_task = task
        elif isinstance(task, VerifyTask):
            self.verify_task = task
        else:
            raise ValueError(f"Unsupported task type: {type(task).__name__}")

TASK_CONTEXT_MAPPING: Dict[str, TaskContext] = {}
# from dataclasses import dataclass, field
# from typing import Any, Dict, List, Optional, Set
# import json
# #TODO need to handle properly 111
#
#
# #for fincode
# user_inject = [
#     # {
#     #     "role": "user",
#     #     "content": """
#     #         f"**Step 2: Extraction Task**\n"
#     #         f"Before you extract you should recall the input question"
#     #         f"- **Segment the Data:** \n"
#     #         f"- Identify and label each table and paragraph in the provided data. \n"
#     #         f"- Separate the tables and paragraphs clearly to avoid confusion. \n"
#     #         f"- **Locate Relevant Sections:** \n"
#     #         f"  - Determine which table or paragraph contains information related to input question".\n"
#     #         f"  - Focus solely on the identified section, ignoring unrelated tables or paragraphs.\n"
#     #         f"  - From the relevant sections, extract the necessary data points required for the selected formulas.\n"
#     #         f"  - **List the top 4 potential candidates** that are most relevant to question, ranked in order of relevance (1 being the most relevant). \n"
#     #         f"  - You should carefully choose the candidates that best answers the question. \n
#     #         f"  - Present the extracted data in a clear and organized manner.\n"
#     #         f"  - **Note:** Do not perform any calculations in this step.\n"
#     #
#     #     """
#     # },
#     {
#         "role": "user",
#         "content": """
#         **Step 3: Calculation Task** \n
#         - **Apply Formulas:** \n
#           - Using the extracted data, apply the selected financial formulas to compute the required value. \n
#         - **Present Calculations:** \n
#         - Show the calculation steps leading to the final result.txt. \n
#         - Provide the final calculated value clearly. \n
#         f"  - **Note:** Only include calculation steps\n"
#         **Format your response exactly as follows:**\n
#         [step1] \n
#         [step2] \n
#         Result: [Calculated Value]
#         f" - **Note:** Please note that you should double check your finale answer to make sure get the accurate results\n"
#         f" - **Note:** You should be careful about the keywords "percentage", "change" etc in the question"
#         """
#     },
# ]
#
# #for program
# # user_inject = [
# #     {
# #         "role": "user",
# #         "content": """
# #             f"**Step 2: Extraction Task**\n"
# #             f"Before you extract you should recall the input question"
# #             f"- **Segment the Data:** \n"
# #             f"- Identify and label each table and paragraph in the provided data. \n"
# #             f"- Separate the tables and paragraphs clearly to avoid confusion. \n"
# #             f"- **Locate Relevant Sections:** \n"
# #             f"  - Determine which table or paragraph contains information related to input question".\n"
# #             f"  - Focus solely on the identified section, ignoring unrelated tables or paragraphs.\n"
# #             f"  - From the relevant sections, extract the necessary data points required for the selected formulas.\n"
# #             f"  - **List the top 4 potential candidates** that are most relevant to question, ranked in order of relevance (1 being the most relevant). \n"
# #             f"  - You should carefully choose the candidates that best answers the question. \n
# #             f"  - Present the extracted data in a clear and organized manner.\n"
# #             f"  - **Note:** Do not perform any calculations in this step.\n"
# #
# #         """
# #     },
# #     {
# #         "role": "user",
# #         "content": """
# #         **Step 3: Calculation Task** \n
# #         - **Apply Formulas:** \n
# #           - Using the extracted data, apply the selected financial formulas to compute the required value. \n
# #         - **Present Calculations:** \n
# #         - Show the calculation steps leading to the final result.txt. \n
# #         - Provide the final calculated value clearly. \n
# #         f"  - **Note:** Only include calculation steps\n"
# #         **Format your response exactly as follows:** \n
# #         [step1] \n
# #         [step2] \n
# #         Result: [Calculated Value]
# #         f" - **Note:** Please note that you should double check your finale answer to make sure get the accurate results\n"
# #         f" - **Note:** You should be careful about the keywords "percentage", "change" etc in the question"
# #         """
# #     },
# # ]
#
#
# #For SEC-NUM Extraction
# # user_inject = [
# #     {
# #         "role": "user",
# #         "content": """
# #             f"Step 3: Select the Top 4 Potential Candidates \n"
# #             f"- **From the relevant table or paragraph**, identify the key data points that answer the question. \n"
# #             f"- **List the top 4 potential candidates** that are most relevant to question, ranked in order of relevance (1 being the most relevant). \n"
# #             f" **Top 4 Potential Candidates:** \n"
# #             f"   1. [Candidate 1] \n  2. [Candidate 2] \n 3. [Candidate 3] \n 4. [Candidate 4] \n\n"
# #
# #         """
# #     },
# #     {
# #         "role": "user",
# #         "content": """
# #         **Instructions:**
# #          **Step4: Select the Most Relevant Candidate and Provide Its Values based on your previous answer to answer the question:** \n
# #          - You should carefully choose the only one candidate that best answers the question. \n
# #          - Provide the value for the selected candidate for each year mentioned in the question. \n \n
# #         """
# #     },
# #     {
# #         "role": "user",
# #         "content": """
# #                     f"Step 2: Select the Top 4 Potential Candidates \n"
# #             f"- From the provided data, list the top 4 items that are most relevant to answering the question. Before that, you should thinking this slowly\n"
# #             f"- If you cannot find the value, you should go back the check the paragraphs. This is text and table input \n"
# #             f"- Rank them in order of relevance (1 being the most relevant). \n"
# #             f"- Ensure that selected candidates are directly related to  and are not from unrelated sections"
# #             f"Step 3: Provide the Answer in This Format: \n "
# #             f" **Top 4 Potential Candidates:** \n"
# #             f"   1. [Candidate 1] \n  2. [Candidate 2] \n 3. [Candidate 3] \n 4. [Candidate 4] \n\n"""
# #     },
# # ]
#
#
# @dataclass
# class TaskInput:
#     """
#     Represents the input data for a task.
#     """
#     question: str
#     answer: Optional[str] = None
#     task: str = ""
#     context: str = ""
#     context_type: Optional[str] = None
#     options: Optional[List[str]] = None
#     program: Optional[str] = None
#
#
# @dataclass
# class ModuleResult:
#     """
#     Represents the output of a module.
#     """
#     module_name: str
#     output_data: Dict[str, Any] = field(default_factory=dict)
#     metadata: Optional[Dict[str, Any]] = None
#     success: bool = True
#
# @dataclass
# class ModuleCommunication:
#     """
#     Represents structured communication between modules.
#     """
#     task_name: str
#     requires_extract: bool = False
#     requires_reason: bool = False
#     requires_tool: bool = False
#     metadata: Optional[Any] = None
#     error_message: str = None
#
# @dataclass
# class EvaluationResult:
#     """
#     Represents the evaluation of a module's result.txt.
#     """
#     module_name: str
#     is_correct: bool
#     feedback: Optional[str] = None
#
# @dataclass
# class Message:
#     role: str
#     content: str
#
#     def to_dict(self) -> Dict[str, str]:
#         """Serializes the Message to a dictionary."""
#         return {"role": self.role, "content": self.content}
#
#     @staticmethod
#     def from_dict(data: Dict[str, str]) -> 'Message':
#         """Deserializes a dictionary to a Message."""
#         return Message(role=data['role'], content=data['content'])
#
# @dataclass
# class Conversation:
#     messages: List[Message] = field(default_factory=list)
#
#     def add_message(self, role: str, content: str) -> None:
#         self.messages.append(Message(role=role, content=content))
#
#     def get_messages(self) -> List[Message]:
#         """Retrieves all messages in the conversation."""
#         return self.messages
#
#     def get_conversation_str(self) -> str:
#         """Returns the conversation as a formatted string."""
#         return "\n".join([f"{msg.role}: {msg.content}" for msg in self.messages])
#
#     def to_json(self) -> str:
#         """Serializes the conversation to a JSON string."""
#         conversation_dict = {
#             "messages": [msg.to_dict() for msg in self.messages]
#         }
#         return json.dumps(conversation_dict, ensure_ascii=False, indent=4)
#
#     @staticmethod
#     def from_json(data: str) -> 'Conversation':
#         """Deserializes a JSON string to a Conversation object."""
#         try:
#             conversation_dict = json.loads(data)
#             messages = [Message.from_dict(msg) for msg in conversation_dict.get("messages", [])]
#             return Conversation(messages=messages)
#         except json.JSONDecodeError as e:
#             raise ValueError(f"Invalid JSON data for Conversation: {e}") from e
#
#
# @dataclass
# class TaskContext:
#     """
#     Represents the shared context across all tasks and modules.
#     """
#     input_data: TaskInput
#     module_results: Dict[str, ModuleResult] = field(default_factory=dict)
#     evaluation_results: List[EvaluationResult] = field(default_factory=list)
#     intermediate_data: Optional[Dict[str, Any]] = field(default_factory=dict)
#     executed_tasks: Set[str] = field(default_factory=set)
#     conversation: Optional[Conversation] = field(default=None)
#     metadata: Optional[Any] = field(default_factory=dict)
#
#
#     def clear_context(self) -> None:
#         """
#         Clears the task context by resetting executed tasks and any other relevant attributes.
#         """
#         self.input_data = None
#         self.intermediate_data = None
#         self.module_results = {}
#         self.evaluation_results = []
#         self.executed_tasks.clear()
#
#     def add_module_result(self, module_name: str, result: ModuleResult) -> None:
#         """
#         Adds the result.txt of a module to the context.
#         """
#         if not isinstance(result, ModuleResult):
#             raise TypeError(f"Expected ModuleResult, got {type(result)}")
#         self.module_results[module_name] = result
#
#     def get_module_result(self, module_name: str) -> Optional[ModuleResult]:
#         """
#         Retrieves the result.txt of a specific module by name.
#         """
#         return self.module_results.get(module_name)
#
#     def add_evaluation_result(self, evaluation: EvaluationResult) -> None:
#         """
#         Adds an evaluation result.txt to the context.
#         """
#         if not isinstance(evaluation, EvaluationResult):
#             raise TypeError(f"Expected EvaluationResult, got {type(evaluation)}")
#         self.evaluation_results.append(evaluation)
#
#     def all_successful(self) -> bool:
#         """
#         Checks if all module results indicate success.
#         """
#         return all(result.success for result in self.module_results.values())
#
#     def summarize(self) -> Dict[str, Any]:
#         """
#         Summarizes the results of the task execution.
#         """
#         return {
#             "task_name": self.input_data.task,
#             "success": self.all_successful(),
#             "evaluation_summary": [
#                 {"module": e.module_name, "is_correct": e.is_correct} for e in self.evaluation_results
#             ],
#         }
#
#     def fetch_history(self) -> Dict[str, Any]:
#         """
#         Fetches the history of all module results and evaluations.
#         """
#         return {
#             "module_results": {
#                 module_name: result.output_data for module_name, result in self.module_results.items()
#             },
#             "evaluation_results": [
#                 {
#                     "module": evaluation.module_name,
#                     "is_correct": evaluation.is_correct,
#                     "feedback": evaluation.feedback,
#                 }
#                 for evaluation in self.evaluation_results
#             ],
#         }
#
#
#     def update_intermediate_data(self, key: str, value: List) -> None:
#         """
#         Updates or adds to the intermediate data shared between tasks.
#         """
#         self.intermediate_data.update({key: value})
#
#
#     def get_intermediate_data(self, key: str) -> Optional[Any]:
#         """
#         Retrieves specific intermediate data by key.
#         """
#         return self.intermediate_data.get(key)
#
#     def get_all_intermediate_data(self) -> dict[str, Any]:
#         """
#         Retrieves all intermediate data.
#         """
#         return self.intermediate_data.copy()
#
#     def get_last_intermediate_key(self) -> Optional[str]:
#         """
#         Retrieves the last key from the intermediate_data dictionary.
#
#         """
#         if hasattr(self, 'intermediate_data') and self.intermediate_data:
#             return list(self.intermediate_data.keys())[-1]
#         return None
#
#
#     def get_conversation(self) -> Conversation:
#         """Retrieves the existing conversation or initializes a new one."""
#         if self.conversation is None:
#             self.conversation = Conversation()
#             self.conversation.add_message(role="system", content="")
#
#         return self.conversation
#
#     def add_message_to_conversation(self, role: str, content: str) -> None:
#         """Adds a message to the conversation within the context."""
#         conversation = self.get_conversation()
#         conversation.add_message(role, content)
#
#     def get_conversation_messages(self) -> List[Message]:
#         """Gets all messages from the conversation."""
#         conversation = self.get_conversation()
#         return conversation.get_messages()
#
#     def insert_system_prompt_if_not_exists(self, system_prompt: str) -> None:
#         """
#         Inserts a system prompt at the beginning of the conversation if no system prompt exists.
#         """
#         conversation = self.get_conversation()
#         # Check if any system message has non-empty content
#         has_system_prompt = any(
#             msg.role == "system" and msg.content.strip()
#             for msg in conversation.messages
#         )
#         if not has_system_prompt:
#             # Insert the system prompt at the beginning
#             conversation.messages.insert(0, Message(role="system", content=system_prompt))
#
