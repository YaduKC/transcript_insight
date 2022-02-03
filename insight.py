from time import sleep
from elasticsearch import Elasticsearch
import openai
import streamlit as st
import nltk
import re
import requests
import os.path

openai.api_key = st.secrets["OPENAI_KEY"]
elasticsearch_key = st.secrets["ELASTICSEARCH_KEY"]
nltk.download('stopwords')

if 'submit_' not in st.session_state:
    st.session_state.submit_ = False

if 'insight_' not in st.session_state:
    st.session_state.insight_ = []

if 'curr_tool_' not in st.session_state:
    st.session_state.curr_tool_ = ""

if 'raw_transcript_' not in st.session_state:
    st.session_state.raw_transcript_ = ""

if 'data_prep_' not in st.session_state:
    st.session_state.data_prep_ = False

if 'upload_' not in st.session_state:
    st.session_state.upload_ = False

if 'elasticsearch_data_' not in st.session_state:
    st.session_state.elasticsearch_data_ = []

if 'es_' not in st.session_state:
    st.session_state.es_ = Elasticsearch(
                    ['https://insight-08476f.es.us-east4.gcp.elastic-cloud.com'],
                    http_auth=('elastic', elasticsearch_key),
                    scheme="https", port=9243,)

def summary(chunk):
    start_sequence = "The main topic of conversation in 6 words is:"
    response = openai.Completion.create(
        engine="text-davinci-001",
        prompt="\""+chunk+"\"" +"\n"+start_sequence,
        temperature=0.7,
        max_tokens=64,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    insight = response.choices[0].get("text")
    insight = insight.replace("\"", "")
    return insight

def local_css():
    with open("style.css") as f:
        st.markdown('<style>{}</style>'.format(f.read()), unsafe_allow_html=True)

def display_search(search_term, result, index):
    local_css()
    s = re.split(search_term.lower(), result.lower())
    html_str = "<div>"
    for count,i in enumerate(s):
        if count < len(s) - 1:
            html_str += i + "<span class='highlight blue'>"+search_term+ "</span>"
        else:
            html_str += i
    html_str = html_str+"</div>"
    with st.container():
        cols = st.columns([0.3,10])
        cols[0].write(str(index+1)+" :")
        cols[1].markdown(html_str, unsafe_allow_html=True)

    

def display_insight(data):
    with st.container():
        cols = st.columns([2,1,1])
        cols[0].header("Transcript")
        cols[1].header("Summary")
        cols[2].header("Timestamp")
    st.markdown("""---""")

    for count, i in enumerate(data):
        with st.container():
            cols = st.columns([2,1,1])
            with cols[0].container():
                with st.expander(label = "Transcript (Segment " + str(count+1) + ")"):
                    st.caption(i["transcript"])
                cols[1].caption(i["summary"])
                cols[2].caption(i["timestamp"])        
    st.markdown("""---""")



def insight_generate(transcript):
    if not st.session_state.insight_:
        tt = nltk.tokenize.TextTilingTokenizer(w=80,k=5,smoothing_width=3, smoothing_rounds=5)
        tiles = tt.tokenize(transcript)

        for chunk in tiles:
            timestamps = re.findall(r"\[\d\d\:\d\d:\d\d\]", chunk)
            if len(timestamps) >= 2:
                timestamps = timestamps[0] + "-" + timestamps[-1]
            elif len(timestamps) == 1:
                timestamps = timestamps[0] + "-" + "[-:-:-]"
            else:
                timestamps = "[-:-:-]-[-:-:-]"
            chunk = re.sub(r"\[\d\d\:\d\d:\d\d\]", "", chunk, flags=re.IGNORECASE)
            insight = summary(chunk)
            chunk_dict = {"transcript":chunk,
                        "summary":insight,
                        "timestamp":timestamps}
            st.session_state.insight_.append(chunk_dict)
    display_insight(st.session_state.insight_)

def jsonl_converter(transcript):
    with st.spinner("Parsing Transcript..."):
        elasticsearch_data = []
        if os.path.isfile("data.jsonl"):
            os.remove("data.jsonl")
        transcript_list = transcript.split("\n")
        file = open("data.jsonl", "w")
        for i in transcript_list:
            if i != "" and i[0:3] != "INT":
                i = i.strip()
                i = i.replace("\"", "")
                i = "{\"text\":" +  " \"" + i + "\"}"
                elasticsearch_data.append(i)
                file.write(i + "\n")
        file.close()
        if not st.session_state.elasticsearch_data_:
            st.session_state.elasticsearch_data_ = elasticsearch_data

def upload_files():
    if os.path.isfile("data.jsonl"):
        with st.spinner("Uploading Files..."):
            openai.File.create(file=open("data.jsonl"), purpose="search")
    else:
        st.error("Transcript JSONL File Not Found!!")

def list_curr_files():
    curr_files = []
    headers = {'Authorization': 'Bearer '+ openai.api_key}
    response_files = requests.get('https://api.openai.com/v1/files', headers=headers)
    files_metadata = response_files.json()["data"]
    for files in files_metadata:
        curr_files.append(files["id"])
    return curr_files

def delete_files():
    with st.spinner("Cleaning Workspace..."):
        headers = {'Authorization': 'Bearer '+ openai.api_key}
        response_files = requests.get('https://api.openai.com/v1/files', headers=headers)
        for i in response_files.json()["data"]:
            file_name = i["id"]
            headers = {'Authorization': 'Bearer '+ openai.api_key}
            delete_response = requests.delete('https://api.openai.com/v1/files/'+file_name, headers=headers)

    

def search():
    search_term = st.text_input(label="Enter Search Term")
    if st.button(label="Submit", key = 0):
        st.markdown("""---""")
        st.subheader("Search Results")
        res = st.session_state.es_.search(index="my-index", body={'query':{'match':{'text':search_term}}}, size=len(st.session_state.elasticsearch_data_))
        for count,hit in enumerate(res['hits']['hits']):
            display_search(search_term, hit["_source"]["text"], count)
    return None

def qna():
    st.info("Under Construction")
    # question = st.text_input(label="Enter Query")
    # if st.button(label="Submit", key = 1):
    #     curr_files = list_curr_files()
    #     answer = openai.Answer.create(
    #                         search_model="davinci", 
    #                         model="davinci", 
    #                         question=question, 
    #                         file=curr_files[0], 
    #                         examples_context=st.session_state.insight_[0]["summary"], 
    #                         examples=[["What is human life expectancy in the United States?", "78 years."]],
    #                         max_tokens=50,
    #                         stop=["\n", "<|endoftext|>"],
    #                         temperature=0.1
    #                     )
    #     st.caption(answer["answers"][0])

def prepare_workspace(transcript):
    if not st.session_state.data_prep_:
        jsonl_converter(transcript)
        delete_files()
        upload_files()
        curr_files = list_curr_files()
        with st.spinner("Processing OpenAI Files"):
            while not st.session_state.upload_:
                try:
                    output = openai.Engine("ada").search(
                                                search_model="ada", 
                                                query="Expert", 
                                                max_rerank=200,
                                                file=curr_files[0]
                                                )
                    st.session_state.upload_ = True
                except:
                    print("Processing")
                sleep(10)

        aliases = st.session_state.es_.indices.get_alias("*")
        if 'my-index' in aliases.keys():
            st.session_state.es_.indices.delete(index='my-index', ignore=[400, 404])
        with st.spinner("Processing ElasticSearch Files..."):
            for a_data in st.session_state.elasticsearch_data_:
                st.session_state.es_.index(index='my-index', body=a_data)
            sleep(5)        
        st.session_state.data_prep_ = True

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    st.title("Insight Demo")
    st.markdown("""---""")
    st.session_state.raw_transcript_ = st.text_area(label="Enter Transcript Here", height=300)
    submit = st.button(label="Submit")
    if st.session_state.submit_ == False:
        st.session_state.submit_ = submit
    st.markdown("""---""")
    if st.session_state.submit_:
        insight_generate(st.session_state.raw_transcript_)
        st.title("Tools")
        st.session_state.curr_tool_ = st.selectbox(label="Select Tool", options=("Search", "Question Answering"))
        if st.session_state.curr_tool_ == "Search":
            prepare_workspace(st.session_state.raw_transcript_)
            search()
        if st.session_state.curr_tool_ == "Question Answering":
            prepare_workspace(st.session_state.raw_transcript_)
            qna()
        st.markdown("""---""")
