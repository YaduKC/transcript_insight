import streamlit as st
import openai
import nltk
import re


openai.api_key = st.secrets["OPENAI_KEY"]
nltk.download('stopwords')

if 'submit_' not in st.session_state:
    st.session_state.submit_ = False


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
    return insight

        

def texttiles(text):
    tt = nltk.tokenize.TextTilingTokenizer(w=80,k=5)
    tiles = tt.tokenize(text)
    with st.container():
        cols = st.columns([2,1,1])
        cols[0].header("Transcript")
        cols[1].header("Summary")
        cols[2].header("Timestamp")
    st.markdown("""---""")
    for count, chunk in enumerate(tiles):
        timestamps = re.findall(r"\[\d\d\:\d\d:\d\d\]", chunk)
        with st.container():
            cols = st.columns([2,1,1])
            with cols[0].container():
                with st.expander(label = "Transcript (Segment " + str(count+1) + ")"):
                    st.caption(chunk)

            #chunk = re.sub(r"analyst:", "", chunk, flags=re.IGNORECASE)
            #chunk = re.sub(r"expert:", "", chunk, flags=re.IGNORECASE)
            chunk = re.sub(r"\[\d\d\:\d\d:\d\d\]", "", chunk, flags=re.IGNORECASE)
            insight = summary(chunk)
            cols[1].caption(insight)
            cols[2].caption(timestamps[0] + "-" + timestamps[-1])
    st.markdown("""---""")

def technicals(transcript):
    st.header("Developer")
    tt = nltk.tokenize.TextTilingTokenizer(w=80,k=5, demo_mode=True)
    s, ss, d, b = tt.tokenize(transcript)

    cols = st.columns([1,1,1,1])

    cols[0].subheader("Gap Scores")
    cols[0].area_chart(s)

    cols[1].subheader("Smoothed Gap scores")
    cols[1].area_chart(ss)

    cols[2].subheader("Depth scores")
    cols[2].area_chart(d)

    cols[3].subheader("Cutoff Region")
    cols[3].area_chart(b)

    parameters = {
                "w":80,
                "k":5,
                "similarity_method":"BLOCK_COMPARISON",
                "stopwords":"NLTK",
                "smoothing_method": "DEFAULT_SMOOTHING",
                "smoothing_width": 2,
                "smoothing_rounds": 1,
                "cutoff_policy": "HC",
                "demo_mode": False
                }

    with cols[0].container():
        st.subheader("Current Parameters")
        st.write(parameters)

    with cols[1].container():
        st.subheader("Parameters")
        '''
        - w (int): Pseudosentence size
        - k (int): Size (in sentences) of the block used in the block comparison method
        - similarity_method (constant): The method used for determining similarity scores: BLOCK_COMPARISON (default) or VOCABULARY_INTRODUCTION.
        - stopwords (list(str)): A list of stopwords that are filtered out (defaults to NLTK’s stopwords corpus)
        - smoothing_method (constant): The method used for smoothing the score plot: DEFAULT_SMOOTHING (default)
        - smoothing_width (int): The width of the window used by the smoothing method
        - smoothing_rounds (int): The number of smoothing passes
        - cutoff_policy (constant): The policy used to determine the number of boundaries: HC (default) or LC
        '''
    st.markdown("""---""")

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    st.title("Insights")

    with st.container():
        st.header("Input Transcript")
        transcript = st.text_area(label="",height=800)
        if st.button(label="Submit"):
            st.session_state.submit_ = True
        if st.session_state.submit_:
            st.markdown("""---""")
            texttiles(transcript)
            technicals(transcript)
