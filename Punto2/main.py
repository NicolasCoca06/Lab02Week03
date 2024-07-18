import os
from newsapi import NewsApiClient
from dotenv import load_dotenv, find_dotenv
import autogen
from autogen import ConversableAgent, AssistantAgent
# Init
newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))

# /v2/top-headlines


# /v2/everything
all_articles = newsapi.get_everything(q='Italian Food',
                                         
                                          language='en')
article_info = ""
for article in all_articles['articles']:
    article_info += article['content']

# /v2/top-headlines/sources
sources = newsapi.get_sources()
#print(article_info)

load_dotenv(find_dotenv())
gemini_api_key = os.getenv("API_KEY")
llm_config = {
  "model": "gemini-1.5-flash-latest",
  "api_key": gemini_api_key,
  "api_type": "google"
}

task = "Write an article summarizing all the retrieved information from the latest news for the topic: Italian Food."

writer = AssistantAgent(
    name="Writer",
    system_message="You are a writer. You write engaging and concise "
        "articles (with title) on the topic 'Italian Food'. You must polish your "
        "writing based on the feedback you receive and give a refined "
        "version. Only return your final work without additional comments. The information you need is: " + article_info,
    llm_config=llm_config,
)

critic = AssistantAgent(
    name="Critic",
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    llm_config=llm_config,
    system_message="You are a critic. You review the work of "
                "the writer and provide constructive "
                "feedback to help improve the quality of the content.",
)

user_proxy = autogen.UserProxyAgent(
    name="Admin",
    system_message="Give the task, and send. instructions to writer to refine the article.",
    code_execution_config=False,
    llm_config=llm_config,
    human_input_mode="ALWAYS",
)

planner = autogen.ConversableAgent(
    name="Planner",
    system_message="Given a task, and the information from the articles please determine "
    "what information is key to complete the task. "
    "After each step is done by others, check the progress and "
    "more importantly, the feedback given by the critic."
    "If the feedback is not satisfactory, try to workaround. "
    "Instruct the writer to refine the article based on the given feedback. "
    "this is the information you need: " + article_info,
    description="Planner. Given a task, determine what "
    "information is needed to complete the task. "
    "After each step is done by others, check the progress and feedbakc and "
    "instruct the remaining steps",
    llm_config=llm_config,
)

groupchat = autogen.GroupChat(
    agents=[user_proxy, critic, writer, planner],
    messages=[],
    max_round=15,
    allowed_or_disallowed_speaker_transitions={
        user_proxy: [planner, critic, writer],
        critic: [planner],
        planner: [writer],
        writer: [critic]
    },
    speaker_transitions_type="allowed",
)

manager = autogen.GroupChatManager(
    groupchat=groupchat, llm_config=llm_config
)

groupchat_result = user_proxy.initiate_chat(
    manager,
    message=task,
)
