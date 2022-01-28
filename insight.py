import streamlit as st
import openai
import nltk
import re


openai.api_key = "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"

def summary(chunk):
    start_sequence = "A single line topic of the conversation:"
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

            analyst = ["temp"]
            expert = ["temp"]
            ts = ["temp"]
            openai_count = 0
            while analyst or expert or ts:
                insight = summary(chunk)
                analyst = re.findall(r"analyst:", insight, flags=re.IGNORECASE)
                expert = re.findall(r"expert:", insight, flags=re.IGNORECASE)
                ts = re.findall(r"\[\d\d\:\d\d:\d\d\]", insight)
                openai_count += 1
            cols[1].caption(insight)
            cols[2].caption(timestamps[0] + "-" + timestamps[-1])
    st.markdown("""---""")

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    st.title("Insights")

    with st.container():
        st.header("Input Transcript")
        transcript = st.text_area(label="",height=800)
        if st.button(label="Submit"):
            st.markdown("""---""")
            texttiles(transcript)