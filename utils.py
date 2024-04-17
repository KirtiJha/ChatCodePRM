from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import git
import os
from queue import Queue
from vectordb import create_vector_db
from prompts import model_prompt, custom_question_prompt

from genai import Client, Credentials
from genai.extensions.langchain import LangChainEmbeddingsInterface
from genai.schema import TextEmbeddingParameters
from genai.extensions.langchain.chat_llm import LangChainChatInterface
from genai.schema import (
    DecodingMethod,
    ModerationHAP,
    ModerationParameters,
    TextGenerationParameters,
    TextGenerationReturnOptions,
)

from langchain.vectorstores.faiss import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.vectorstores import Chroma
import chromadb

model_name = "sentence-transformers/all-MiniLM-L6-v2"
allowed_extensions = [".md", ".cls", ".html", ".js"]
persist_directory = "data/vectordb/chatcodeprm/chroma/"

from langchain.chains import ConversationalRetrievalChain


class Embedder:
    def __init__(self, repo_links) -> None:
        self.repo_links = repo_links
        # last_name = self.git_link.split("/")[-1]
        self.MyQueue = Queue(maxsize=2)

    def add_to_queue(self, value):
        if self.MyQueue.full():
            self.MyQueue.get()
        self.MyQueue.put(value)

    def clone_repo(self, repo_path, clone_path):
        if not os.path.exists(clone_path):
            # Clone the repository
            git.Repo.clone_from(repo_path, clone_path)

    def extract_all_files(self, clone_paths):
        self.docs = []
        for clone_path in clone_paths:
            root_dirs = []
            root_dir_classes = clone_path + "/force-app/main/default/classes"
            root_dir_lwc = clone_path + "/force-app/main/default/lwc"
            root_dirs.append(root_dir_classes)
            root_dirs.append(root_dir_lwc)
            print(f"root dirs - {root_dirs}")
            for root_dir in root_dirs:
                for dirpath, dirnames, filenames in os.walk(root_dir):
                    for file in filenames:
                        file_extension = os.path.splitext(file)[1]
                        if file_extension in allowed_extensions:
                            print(file)
                            try:
                                loader = TextLoader(
                                    os.path.join(dirpath, file), encoding="utf-8"
                                )
                                self.docs.extend(loader.load_and_split())
                            except Exception as e:
                                pass
        # self.delete_directory(self.clone_path)
        return self.docs

    def process_repo_files(self, github_access_token):
        base_url = f"https://{github_access_token}@github.ibm.com/IBMSC/"
        clone_paths = []
        for repo in self.repo_links:
            if repo == "Global Schema":
                repo_path = base_url + "global-schema.git"
            elif repo == "PRM":
                repo_path = base_url + "PRM.git"
            elif repo == "Sales":
                repo_path = base_url + "Sales.git"
            elif repo == "Global Core":
                repo_path = base_url + "global-core.git"
            last_name = repo_path.split("/")[-1]
            clone_path = last_name.split(".")[0]
            self.clone_repo(repo_path, clone_path)
            clone_paths.append(clone_path)
        return clone_paths

    def chunk_files(self, docs):
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " ", ""], chunk_size=1000, chunk_overlap=200
        )
        chunked_documents = text_splitter.split_documents(docs)
        print("Number of chunks:", len(chunked_documents), "\n\n")
        return chunked_documents

    def delete_directory(self, paths):
        for path in paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path, topdown=False):
                    for file in files:
                        file_path = os.path.join(root, file)
                        os.remove(file_path)
                    for dir in dirs:
                        dir_path = os.path.join(root, dir)
                        os.rmdir(dir_path)
                os.rmdir(path)

    def get_conversation_chain(self, gen_ai_key, clone_paths):
        # local_path = self.clone_path

        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)

        credentials = Credentials(api_key=gen_ai_key)
        client = Client(credentials=credentials)
        # Create vector db
        docs = self.extract_all_files(clone_paths)
        print(len(docs))
        chunked_documents = self.chunk_files(docs)
        print(len(chunked_documents))
        embeddings = LangChainEmbeddingsInterface(
            client=client,
            model_id="sentence-transformers/all-minilm-l6-v2",
            parameters=TextEmbeddingParameters(truncate_input_tokens=True),
        )

        vector_store = self.get_vector_db(
            embeddings=embeddings,
            chunked_documents=chunked_documents,
            persist_directory=persist_directory,
        )

        retriever = vector_store.as_retriever()
        search_kwargs = {"k": 8}

        retriever.search_kwargs.update(search_kwargs)

        #  Create conversation chain
        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )

        prompt_template = model_prompt()
        qa_chain_prompt = PromptTemplate(
            input_variables=["context", "question"], template=prompt_template
        )
        question_prompt = PromptTemplate.from_template(custom_question_prompt())

        print(question_prompt)

        credentials = Credentials(
            api_key=gen_ai_key,
            api_endpoint="https://bam-api.res.ibm.com/v2/text/chat?version=2024-01-10",
        )
        client = Client(credentials=credentials)

        llm = LangChainChatInterface(
            model_id="mistralai/mistral-7b-instruct-v0-2",
            client=client,
            parameters=TextGenerationParameters(
                decoding_method=DecodingMethod.GREEDY,
                max_new_tokens=8000,
                min_new_tokens=10,
                temperature=0.2,
                top_k=40,
                top_p=0.9,
                return_options=TextGenerationReturnOptions(
                    input_text=False, input_tokens=True
                ),
            ),
            moderations=ModerationParameters(
                # Threshold is set to very low level to flag everything (testing purposes)
                # or set to True to enable HAP with default settings
                hap=ModerationHAP(input=True, output=False, threshold=0.01)
            ),
        )

        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            chain_type="stuff",
            combine_docs_chain_kwargs={"prompt": qa_chain_prompt},
            condense_question_prompt=question_prompt,
            verbose=True,
        )
        self.delete_directory(clone_paths)
        return conversation_chain

    def retrieve_results(self, query, conversation_chain):
        chat_history = list(self.MyQueue.queue)
        # qa = self.get_conversation_chain(vector_store, gen_ai_key)
        result = conversation_chain({"question": query, "chat_history": chat_history})
        self.add_to_queue((query, result["answer"]))
        return result["answer"]

    def create_directory(self, directory_path):
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

    def get_vector_db(self, embeddings, chunked_documents, persist_directory):
        # if not os.path.exists(persist_directory):
        vector_store = create_vector_db(
            documents=chunked_documents,
            embeddings=embeddings,
            persist_directory=persist_directory,
        )
        # else:
        #     vector_store = Chroma(
        #         persist_directory=persist_directory, embedding_function=embeddings
        #     )
        return vector_store
