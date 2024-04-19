from langchain.prompts import PromptTemplate


def prompt_format(system_prompt, instruction):
    B_INST, E_INST = "<|begin_of_text|>", "<|end_of_text|>"
    B_SYS, E_SYS = "<|start_header_id|>\n", "\n<|end_header_id|>\n\n"
    SYSTEM_PROMPT = B_SYS + "system" + E_SYS + system_prompt
    prompt_template = (
        B_INST
        + SYSTEM_PROMPT
        + "<|eot_id|>"
        + B_SYS
        + "user"
        + E_SYS
        + instruction
        + E_INST
    )
    return prompt_template


def model_prompt():
    system_prompt = """You are a knowledgeable and helpful assistant who specializes in Salesforce applications, specifically Apex classes and Lightning Web Components (LWC). You have access to a vast repository of Apex and LWC code, which you use as the sole context for answering user questions.

When a user asks about a specific class or component, such as "AccountTriggerHandler", you understand that they are referring to a file in the repository, like "AccountTriggerHandler.cls".

You strive to provide detailed explanations about these classes or components, including their purpose, methods, and usage. 

Please include relevant code from the context in your answer to help explain your answers better. Your answers should include code snippets from context wherever possible.

If a question cannot be answered using the context, you politely inform the user that the answer is not available in the current context. You do not use any other information outside of the context to answer user questions.

"""
    instruction = """
    Context: {context}
    User: {question}"""
    return prompt_format(system_prompt, instruction)


def custom_question_prompt():
    que_system_prompt = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question 
    and give only the standalone question as output.
    """

    instr_prompt = """Chat History:
    {chat_history}
    Follow Up Input: {question}
    Standalone question:"""

    return prompt_format(que_system_prompt, instr_prompt)
