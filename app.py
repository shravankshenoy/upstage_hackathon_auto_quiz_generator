import gradio as gr
import random
import requests
import os
from dotenv import load_dotenv
import shutil
from typing import Dict, List

from haystack import component

import json
import json_repair
from haystack.dataclasses import Document
from haystack.components.converters import HTMLToDocument
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.generators import OpenAIGenerator
from haystack.components.builders import PromptBuilder
from haystack.utils import Secret
from haystack import Pipeline
from typing import Dict, Any, List, Tuple
import random

print("Environment variables are loaded:", load_dotenv())

if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_KEY")
if "UPSTAGE_API_KEY" not in os.environ:
    os.environ["UPSTAGE_API_KEY"] = os.getenv("UPSTAGE_API_KEY")

@component
class QuizParser:
    @component.output_types(quiz=Dict)
    def run(self, replies: List[str]):
        reply = replies[0]

        # even if prompted to respond with JSON only, sometimes the model returns a mix of JSON and text
        first_index = min(reply.find("{"), reply.find("["))
        last_index = max(reply.rfind("}"), reply.rfind("]")) + 1

        json_portion = reply[first_index:last_index]

        try:
            quiz = json.loads(json_portion)
        except json.JSONDecodeError:
            # if the JSON is not well-formed, try to repair it
            quiz = json_repair.loads(json_portion)

        # sometimes the JSON contains a list instead of a dictionary
        if isinstance(quiz, list):
            quiz = quiz[0]

        print(quiz)

        return {"quiz": quiz}


quiz_generation_template = """Given the following text, create 5 multiple choice quizzes in JSON format.
Each question should have 4 different options, and only one of them should be correct.
The options should be unambiguous.
Each option should begin with a letter followed by a period and a space (e.g., "a. option").
The question should also briefly mention the general topic of the text so that it can be understood in isolation.
Each question should not give hints to answer the other questions.
Include challenging questions, which require reasoning.

respond with JSON only, no markdown or descriptions.

example JSON format you should absolutely follow:
{"topic": "a sentence explaining the topic of the text",
 "questions":
  [
    {
      "question": "text of the question",
      "options": ["a. 1st option", "b. 2nd option", "c. 3rd option", "d. 4th option"],
      "right_option": "c. 3rd option"  # the right option
    }, ...
  ]
}

text:
{% for doc in documents %}{{ doc.content|truncate(5000) }}{% endfor %}
"""


quiz_generation_pipeline = Pipeline()
quiz_generation_pipeline.add_component("link_content_fetcher", LinkContentFetcher())
quiz_generation_pipeline.add_component("html_converter", HTMLToDocument())
quiz_generation_pipeline.add_component(
    "prompt_builder", PromptBuilder(template=quiz_generation_template)
)
quiz_generation_pipeline.add_component(
    "generator",
    OpenAIGenerator(
        api_key=Secret.from_env_var("GROQ_API_KEY"),
        api_base_url="https://api.groq.com/openai/v1",
        model="llama3-8b-8192",
        generation_kwargs={"max_tokens": 1000, "temperature": 0.5, "top_p": 1},
    ),
)
quiz_generation_pipeline.add_component("quiz_parser", QuizParser())

quiz_generation_pipeline.connect("link_content_fetcher", "html_converter")
quiz_generation_pipeline.connect("html_converter", "prompt_builder")
quiz_generation_pipeline.connect("prompt_builder", "generator")
quiz_generation_pipeline.connect("generator", "quiz_parser")


quiz_from_pdf_pipeline = Pipeline()
quiz_from_pdf_pipeline.add_component(
    "prompt_builder", PromptBuilder(template=quiz_generation_template)
)
quiz_from_pdf_pipeline.add_component(
    "generator",
    OpenAIGenerator(
        api_key=Secret.from_env_var("GROQ_API_KEY"),
        api_base_url="https://api.groq.com/openai/v1",
        model="llama3-8b-8192",
        generation_kwargs={"max_tokens": 1000, "temperature": 0.5, "top_p": 1},
    ),
)
quiz_from_pdf_pipeline.add_component("quiz_parser", QuizParser())
quiz_from_pdf_pipeline.connect("prompt_builder", "generator")
quiz_from_pdf_pipeline.connect("generator", "quiz_parser")



def generate_quiz(url: str) -> Dict[str, Any]:
    return quiz_generation_pipeline.run({"link_content_fetcher": {"urls": [url]}})[
        "quiz_parser"
    ]["quiz"]

def populate_quiz(url: str):
    quiz = generate_quiz(url)
    options = []
    answers = []
    for i in range(5):
        option = gr.Radio(
            choices = quiz['questions'][i]['options'],
            interactive=False,
            label=f"Question {i+1} : {quiz['questions'][i]['question']}",
            visible=True
        )
        options.append(option)
        answers.append(gr.Text(quiz['questions'][i]['right_option'], label=f"Question {i+1}", visible=True))
    print(answers)
    answersblock = gr.Markdown("## Answers", visible=True)
    return quiz, answersblock, *answers, *options

def extract_text_using_ocr(filename):
    url = "https://api.upstage.ai/v1/document-ai/ocr"
    headers = {"Authorization": f"Bearer {os.getenv('UPSTAGE_API_KEY')}"}
    files = {"document": open(filename, "rb")}
    response = requests.post(url, headers=headers, files=files)
    output = response.json()
    print(output)
    with open("extracted_text.json", "w") as f:
        json.dump(output, f, indent=4)

def populate_quiz_2(filename):
    extract_text_using_ocr(filename)
    with open("extracted_text.json", "r") as f:
        result = json.load(f)
    num_pages = len(result['metadata']['pages'])
    #https://stackoverflow.com/questions/4435169/how-do-i-append-one-string-to-another-in-python
    text = ""
    for i in range(num_pages):
        text += result['pages'][i]['text']

    quiz = quiz_from_pdf_pipeline.run({"prompt_builder": {"documents": [Document(content=text)]}})[
        "quiz_parser"
    ]["quiz"]
    print(quiz)
    options = []
    answers = []
    for i in range(5):
        option = gr.Radio(
            choices = quiz['questions'][i]['options'],
            interactive=False,
            label=f"Question {i+1} : {quiz['questions'][i]['question']}",
            visible=True
        )
        options.append(option)
        answers.append(gr.Text(quiz['questions'][i]['right_option'], label=f"Question {i+1}", visible=True))
    print(answers)
    answersblock = gr.Markdown("## Answers", visible=True)
    return quiz, answersblock, *answers, *options
    


def upload_file(files):
    #https://stackoverflow.com/questions/76083621/how-to-get-the-upload-file-location-in-gradio
    #file_paths = [file.name for file in files]
    for file in files:
        path = os.path.basename(file)
        print(path)
        shutil.copyfile(file.name, path) #copy file from temp dir to current dir
    print(files)
    return path



with gr.Blocks() as demo:
    output = gr.State({}) 
    quiz_header = gr.Markdown("## Quiz")
    with gr.Tabs() as tabs:
        with gr.TabItem("Generate quiz from url"):
            with gr.Row():
                url = gr.Textbox(
                    label="URL from which to generate a quiz",
                    value="",
                    interactive=True,
                    max_lines=1,
                )
            with gr.Row():    
                generate_quiz_from_url_btn = gr.Button(
                    value="Generate quiz", variant="primary", scale=0
                )
        with gr.TabItem("Generate quiz from pdf", id="llm_tab") as llm_tab:
            with gr.Row():
                file_output = gr.File()
                upload_button = gr.UploadButton("Click to Upload a File", file_count="multiple")
                upload_button.upload(upload_file, upload_button, file_output)
                print(file_output)
            with gr.Row():    
                generate_quiz_from_pdf_btn = gr.Button(
                    value="Generate quiz", variant="primary", scale=0
                )

    

    
    #output = gr.Textbox()
    
    with gr.Row():
        options0 = gr.Radio(visible=False)    
    with gr.Row():
        options1 = gr.Radio(visible=False)
    with gr.Row():
        options2 = gr.Radio(visible=False)
    with gr.Row():
        options3 = gr.Radio(visible=False)
    with gr.Row():
        options4 = gr.Radio(visible=False)
    
    answersblock = gr.Markdown(visible=False)

    with gr.Row():
        answers0 = gr.Text(visible=False)
    with gr.Row():
        answers1 = gr.Text(visible=False)
    with gr.Row():
        answers2 = gr.Text(visible=False)
    with gr.Row():
        answers3 = gr.Text(visible=False)
    with gr.Row():
        answers4 = gr.Text(visible=False)

    generate_quiz_from_url_btn.click(fn=populate_quiz, inputs=[url], outputs=[output, answersblock, answers0, answers1, answers2, answers3, answers4, options0, options1, options2, options3, options4])
    generate_quiz_from_pdf_btn.click(fn=populate_quiz_2, inputs=[file_output], outputs=[output, answersblock, answers0, answers1, answers2, answers3, answers4, options0, options1, options2, options3, options4])

demo.launch()

