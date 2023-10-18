import streamlit as st
from llama_index import VectorStoreIndex, ServiceContext, Document
from llama_index.llms import OpenAI
import openai
from llama_index import SimpleDirectoryReader
import requests
from llama_index.response_synthesizers import get_response_synthesizer

import pathlib as p
import pandas as pd
import polars as pl
import json

openai.api_key = "sk-VOTRE_CLE_API_OPENAPI_ICI"
st.header("Chat with RF")

if "messages" not in st.session_state.keys(): # Initialize the chat message history
    st.session_state.messages = [
        {"role": "assistant", "content": "Posez des questions à propos du contenu de l'émission."}
    ]

ds = p.Path("dataset")
df_pd = pd.read_csv(
    ds / "transcripts" / "whisper.csv",
    index_col="magnetothequeId", # Nécessaire pour .loc[]
    nrows=3000
)
df_pl = pl.scan_csv(ds / "transcripts" / "whisper.csv", low_memory=True)

def fetch_pd(mid: str) -> dict | None:
    return df.loc[mid].segments if mid in df.index else []

def fetch_pl(mid: str) -> dict | None:
    seg = df_pl.filter(pl.col("magnetothequeId") == mid).select("segments")
    return seg.collect().to_dict(as_series=False)["segments"][0]


def load_data(document_text):
    with st.spinner(text="Loading and indexing"):
        service_context = ServiceContext.from_defaults(llm=OpenAI(model="gpt-3.5-turbo", temperature=0.2, system_prompt="Tu es un journaliste et ton travail est de répondre à des questions à partir de la transcription d'une émission. Réponds uniquement avec des faits venant des transcriptions et n'hallucine pas."))
        index = VectorStoreIndex.from_documents([Document(text=document_text)], service_context=service_context)
        return index

with st.form("Ask transcript"):
    mid = st.text_input("mID", key="mid")
    submitted = st.form_submit_button("Submit")
    if submitted:
        segments = fetch_pl(mid)
        if segments:
            transcript = "".join([segment['text'] for segment in json.loads(segments)])
            print(transcript)

            index = load_data(transcript)

            # response_synthesizer = get_response_synthesizer(response_mode='tree_summarize')
            # t = index.as_query_engine(response_synthesizer=response_synthesizer)
            # print(t.query("Résume en français"))

            st.session_state.chat_engine = index.as_chat_engine(chat_mode="condense_question", verbose=True)
            print('a')
            st.session_state.messages = [
                {"role": "assistant", "content": "Posez des questions à propos du contenu de l'émission :)"}
            ]

if prompt := st.chat_input("Your question"): # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages: # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chat_engine.chat(prompt)
            st.write(response.response)
            message = {"role": "assistant", "content": response.response}
            st.session_state.messages.append(message) # Add response to message history
