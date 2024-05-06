from langchain.prompts import PromptTemplate


def prompt_format(system_prompt, instruction):
    B_INST, E_INST = "[INST]", "[/INST]"
    B_SYS, E_SYS = "<SYS>>\n", "\n<</SYS>>\n\n"
    SYSTEM_PROMPT = B_SYS + system_prompt + E_SYS
    prompt_template = B_INST + SYSTEM_PROMPT + instruction + E_INST
    return prompt_template


def model_prompt():
    system_prompt = """You are a knowledgeable and helpful code assistant who specializes in Salesforce applications, specifically Apex classes and Lightning Web Components (LWC) codes. You have access to a vast repository of Apex and LWC code, which you use as the sole context for answering user questions and writting code.

When a user asks about a specific class or component, such as "AccountTriggerHandler", you understand that they are referring to a file in the repository, like "AccountTriggerHandler.cls".

You strive to provide detailed explanations about these classes or components, including their purpose, methods, and usage.

When a user asks to write code, you write code based on the relevant code in the context. Dont write new code from scratch if its available in the context. Use or call existing classes, fuctions, methods or codes to write new code by calling or referring to existing code by passing appropriate parameters based on context.

Please include relevant code from the context in your answer to help explain your answers better. Your answers should include code snippets from context wherever possible.

If a question cannot be answered using the context, you politely inform the user that the answer is not available in the current context. You do not use any other information outside of the context to answer user questions.

"""
    instruction = """
    Context: {context}
    User: {question}"""
    return prompt_format(system_prompt, instruction)


def custom_question_prompt():
    que_system_prompt = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question and give only the standalone question as output in the tags <question> and </question>.
    """

    instr_prompt = """Chat History:
    {chat_history}
    Follow Up Input: {question}
    Standalone question:"""

    return prompt_format(que_system_prompt, instr_prompt)
