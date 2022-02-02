from cProfile import label
from time import sleep
import openai
import streamlit as st
import nltk
import re
import requests
import os.path

openai.api_key = st.secrets["OPENAI_KEY"]
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

def summary(chunk):
    # start_sequence = "The main topic of conversation in 6 words is:"
    # response = openai.Completion.create(
    #     engine="text-davinci-001",
    #     prompt="\""+chunk+"\"" +"\n"+start_sequence,
    #     temperature=0.7,
    #     max_tokens=64,
    #     top_p=1,
    #     frequency_penalty=0,
    #     presence_penalty=0
    # )
    # insight = response.choices[0].get("text")
    # return insight
    return "Test"

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
        if os.path.isfile("data.jsonl"):
            os.remove("data.jsonl")
        transcript_list = transcript.split("\n")
        file = open("data.jsonl", "w")
        for i in transcript_list:
            if i != "" and i[0:3] != "INT":
                i = i.strip()
                i = i.replace("\"", "")
                i = "{\"text\":" +  " \"" + i + "\"}"
                file.write(i + "\n")
        file.close()

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
        curr_files = list_curr_files()
        output = openai.Engine("ada").search(
                                    search_model="ada", 
                                    query=search_term, 
                                    max_rerank=200,
                                    file=curr_files[0]
                                    )
        st.markdown("""---""")
        st.title("Results")
        for data in output["data"]:
            st.caption(data["text"])
    return None

def qna():
    st.info("Under Construction...")

def prepare_workspace(transcript):
    if not st.session_state.data_prep_:
        jsonl_converter(transcript)
        delete_files()
        upload_files()
        curr_files = list_curr_files()
        with st.spinner("Processing Files"):
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
