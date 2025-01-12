from prompts import SYSTEM_PROMPTS
import autogen
import tempfile

from autogen import ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor

financial_task = """"
the goldman sachs group , inc . and subsidiaries notes to consolidated financial statements the firm is unable to develop an estimate of the maximum payout under these guarantees and indemnifications . however , management believes that it is unlikely the firm will have to make any material payments under these arrangements , and no material liabilities related to these guarantees and indemnifications have been recognized in the consolidated statements of financial condition as of both december 2017 and december 2016 . other representations , warranties and indemnifications . the firm provides representations and warranties to counterparties in connection with a variety of commercial transactions and occasionally indemnifies them against potential losses caused by the breach of those representations and warranties . the firm may also provide indemnifications protecting against changes in or adverse application of certain u.s . tax laws in connection with ordinary-course transactions such as securities issuances , borrowings or derivatives . in addition , the firm may provide indemnifications to some counterparties to protect them in the event additional taxes are owed or payments are withheld , due either to a change in or an adverse application of certain non-u.s . tax laws . these indemnifications generally are standard contractual terms and are entered into in the ordinary course of business . generally , there are no stated or notional amounts included in these indemnifications , and the contingencies triggering the obligation to indemnify are not expected to occur . the firm is unable to develop an estimate of the maximum payout under these guarantees and indemnifications . however , management believes that it is unlikely the firm will have to make any material payments under these arrangements , and no material liabilities related to these arrangements have been recognized in the consolidated statements of financial condition as of both december 2017 and december 2016 . guarantees of subsidiaries . group inc . fully and unconditionally guarantees the securities issued by gs finance corp. , a wholly-owned finance subsidiary of the firm . group inc . has guaranteed the payment obligations of goldman sachs & co . llc ( gs&co. ) and gs bank usa , subject to certain exceptions . in addition , group inc . guarantees many of the obligations of its other consolidated subsidiaries on a transaction-by-transaction basis , as negotiated with counterparties . group inc . is unable to develop an estimate of the maximum payout under its subsidiary guarantees ; however , because these guaranteed obligations are also obligations of consolidated subsidiaries , group inc . 2019s liabilities as guarantor are not separately disclosed . note 19 . shareholders 2019 equity common equity as of both december 2017 and december 2016 , the firm had 4.00 billion authorized shares of common stock and 200 million authorized shares of nonvoting common stock , each with a par value of $ 0.01 per share . dividends declared per common share were $ 2.90 in 2017 , $ 2.60 in 2016 and $ 2.55 in 2015 . on january 16 , 2018 , the board of directors of group inc . ( board ) declared a dividend of $ 0.75 per common share to be paid on march 29 , 2018 to common shareholders of record on march 1 , 2018 . the firm 2019s share repurchase program is intended to help maintain the appropriate level of common equity . the share repurchase program is effected primarily through regular open-market purchases ( which may include repurchase plans designed to comply with rule 10b5-1 ) , the amounts and timing of which are determined primarily by the firm 2019s current and projected capital position , but which may also be influenced by general market conditions and the prevailing price and trading volumes of the firm 2019s common stock . prior to repurchasing common stock , the firm must receive confirmation that the frb does not object to such capital action . the table below presents the amount of common stock repurchased by the firm under the share repurchase program. .

|  | Year Ended December |
| :--- | :--- |
| <i>in millions, except per share amounts</i> | 2017 | 2016 | 2015 |
| Common share repurchases | 29.0 | 36.6 | 22.1 |
| Average cost per share | $231.87 | $165.88 | $189.41 |
| Total cost of common share repurchases | $ 6,721 | $ 6,069 | $ 4,195 |

pursuant to the terms of certain share-based compensation plans , employees may remit shares to the firm or the firm may cancel rsus or stock options to satisfy minimum statutory employee tax withholding requirements and the exercise price of stock options . under these plans , during 2017 , 2016 and 2015 , 12165 shares , 49374 shares and 35217 shares were remitted with a total value of $ 3 million , $ 7 million and $ 6 million , and the firm cancelled 8.1 million , 6.1 million and 5.7 million of rsus with a total value of $ 1.94 billion , $ 921 million and $ 1.03 billion , respectively . under these plans , the firm also cancelled 4.6 million , 5.5 million and 2.0 million of stock options with a total value of $ 1.09 billion , $ 1.11 billion and $ 406 million during 2017 , 2016 and 2015 , respectively . 166 goldman sachs 2017 form 10-k .
Question: what is the total amount of stock options cancelled in millions during 2017 , 2016 and 2015?
"""

local_llm_config={
    "config_list": [
        {
            "model": "meta-llama/Llama-3.2-1B-Instruct", # Same as in vLLM command
            "api_key": "NotRequired",  # Not needed
            "base_url": "http://0.0.0.0:8000/v1"  # Your vLLM URL, with '/v1' added
        }
    ],
    "cache_seed": 42 # Turns off caching, useful for testing different models
}

extractor_prompt = SYSTEM_PROMPTS.get("extraction", "Extract system prompt.")
reasoner_prompt = SYSTEM_PROMPTS.get("reasoning", "Reasoning system prompt.")
verify_prompt = SYSTEM_PROMPTS.get("verify", "Verify system prompt.")
tool_prompt = ""

reasoner_assistant = autogen.AssistantAgent(
    name="Reasoner_assistant",
    llm_config=local_llm_config,
    system_message=reasoner_prompt,
)
extractor_assistant = autogen.AssistantAgent(
    name="Extractor",
    llm_config=local_llm_config,
    # system_message=extractor_prompt,
)
verify_assistant = autogen.AssistantAgent(
    name="Verify",
    llm_config=local_llm_config,
    # system_message=verify_prompt,
)

user_proxy_auto = autogen.UserProxyAgent(
    name="User_Proxy_Auto",
    human_input_mode="NEVER",
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "last_n_messages": 1,
        "work_dir": "tasks",
        "use_docker": False,
    },  # Please set use_docker=True if docker is available to run the generated code. Using docker is safer than running the generated code directly.
)

# Create a temporary directory to store the code files.
temp_dir = tempfile.TemporaryDirectory()

# Create a local command line code executor.
executor = LocalCommandLineCodeExecutor(
    timeout=10,  # Timeout for each code execution in seconds.
    work_dir=temp_dir.name,  # Use the temporary directory to store the code files.
)

# Create an agent with code executor configuration.
code_executor_agent = ConversableAgent(
    "code_executor_agent",
    llm_config=False,  # Turn off LLM for this agent.
    code_execution_config={"executor": executor},  # Use the local command line code executor.
)

chat_results = autogen.initiate_chats(
    [
        {
            "sender": user_proxy_auto,
            "recipient": reasoner_assistant,
            "message": financial_task,
            "clear_history": True,
            "silent": False,
            "summary_method": "last_msg",
            "max_turns": 5,
        },
        {
            "sender":  user_proxy_auto,
            "recipient": extractor_assistant,
            "message": extractor_prompt,
            "max_turns": 2,  # max number of turns for the conversation (added for demo purposes, generally not necessarily needed)
            "summary_method": "reflection_with_llm",
        },
        {
            "sender": user_proxy_auto,
            "recipient": verify_assistant,
            "message": verify_prompt,
            "max_turns": 5,
            # "carryover": "I want to include a figure or a table of data in the blogpost.",  # additional carryover to include to the conversation (added for demo purposes, generally not necessarily needed)
        },
        {
            "sender": user_proxy_auto,
            "recipient": code_executor_agent,
            # "message": verify_prompt,
            "max_turns": 5,
            # "carryover":"You n",  # additional carryover to include to the conversation (added for demo purposes, generally not necessarily needed)
        },
    ]
)

# print("Chat history:", chat_res.chat_history)
#
# print("Summary:", chat_res.summary)
# print("Cost info:", chat_res.cost)