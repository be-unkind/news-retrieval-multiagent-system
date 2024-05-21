import os
from datetime import datetime, timedelta
from pprint import pprint

import tools
from configs import model_config

import gradio as gr

import autogen
import groq

TODAY_DATE = datetime.today().strftime('%d.%m.%Y')

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

config_list = [
    {
        "model": model_config.MODEL_NAME_GROQ,
        "base_url": model_config.BASE_URL_GROQ,
        "api_key": GROQ_API_KEY,
    }
]

LLAMA_CONFIG = {"config_list": config_list}


def initialize_agents():
    """
    Initialize agents that will be used in sequential chat
    """

    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        system_message="A proxy for the user for initiating chat with provided question.",
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
        human_input_mode="NEVER",
        code_execution_config={"use_docker": False},
    )
    user_proxy.register_for_execution(name="request_serper_api")(tools.request_serper_api)

    parse_question = autogen.ConversableAgent(
        name="Agent 1: Retrieve topic from the question",
        system_message="""
        You retrieve topic of the question from the question provided by the user.

        Examples:
        Question: What are the latest news about fashion?
        Topic: Fashion

        Question: Tell me about latest cryptocurrency trends.
        Topic: Cryptocurrency
        """,
        llm_config=LLAMA_CONFIG,
        human_input_mode="NEVER",
    )

    search_sources = autogen.ConversableAgent(
        name="Agent 2: Make a request with topic to the api to retieve top stories on the said topic.",
        system_message="""
        You make request to the Serper API to retrieve results.

        Return output in a format:

        {
            "top_stories": [
                {
                    "title": <title>,
                    "source": <link>,
                    "text": <text>
                },
                {
                    "title": <title>,
                    "source": <link>,
                    "text": <text>
                },
                {
                    "title": <title>,
                    "source": <link>,
                    "text": <text>
                }
                ...
            ]
        }

        when the task is done.
        """,
        llm_config=LLAMA_CONFIG,
        human_input_mode="NEVER",
    )
    search_sources.register_for_llm(name="request_serper_api", description="A tool for request to Serper API")(tools.request_serper_api)

    categorize_stories = autogen.ConversableAgent(
        name="Agent 3: Analyze top stories, divide them into categories and format text into needed style",
        system_message=f"""
        You analyze top stories texts, combine text with the title and summarize them into 1-2 sentences (these 1-2 sentences should contain the most representative information about the article and sound like a news title that summarizes the article)
        Then you divide them into 2-4 categories by theme
        If there is no titles in the category, do not include it in the returned result text
        Do not duplicate sources and include only valid links in the specified format

        Ensure all sources are valid URLs in the format www.source.com. Do not include any source with invalid URLs or that does not meet this format. Do not include links within the text; list them only in the sources section.

        Return output in the format (where topic is the topic that was questioned by the user), with no additional text or introduction:

        *Topic news {TODAY_DATE}:*

        Category Name:
        - Title
        - Title
        - ...

        Category Name:
        - Title
        - Title
        - ...

        Category Name:
        - ...

        Sources:
        - www.source.com
        - ...

        when the task is done.

        Respond only with the formatted text. Do not include any phrases like "Here is the formatted output" or any other introductory or concluding text.
        """,
        llm_config=LLAMA_CONFIG,
        human_input_mode="NEVER",
    )

    return [user_proxy, parse_question, search_sources, categorize_stories]


def news_digest(user_question: str):
    '''
    Return news dogest on the requested topic.
    '''
    agents = initialize_agents()

    chat_results = agents[0].initiate_chats(
        [
            {
                "recipient": agents[1],
                "message": user_question,
                "max_turns": 1,
                "summary_method": "last_msg",
                # "silent": True,
            },
            {
                "recipient": agents[2],
                "message": "This is the topic that you should retrieve information about from the Serper API",
                "max_turns": 2,
                "summary_method": "last_msg",
                # "silent": True,
            },
            {
                "recipient": agents[3],
                "message": "These are the top stories on asked topic that you shoud categorize and format",
                "max_turns": 1,
                "summary_method": "last_msg",
                # "silent": True,
            },
        ]
    )

    return chat_results[-1].chat_history[-1]['content']

def define_gradio_ui():
    iface = gr.Interface(
        fn=news_digest,
        inputs=[gr.Textbox("What is happening in the art world today?")],
        outputs="text",
        title="News digest on a given topic",
        description="Ask a question to receive a short news digest 💐️️️️️️"
        )

    iface.launch(share=True)


if __name__ == "__main__":
    define_gradio_ui()
