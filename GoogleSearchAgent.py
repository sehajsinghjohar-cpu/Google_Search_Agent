import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Live Search Agent", page_icon="🛰️")
st.title("🛰️ Gemini Live Search Agent")
st.caption("Powered by Google Search Grounding — every answer is real-time & verifiable.")

with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIza...")

if not api_key:
    st.warning("Enter your Gemini API Key in the sidebar.")
    st.stop()

# --- Init chat history only (no client stored in session state) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []

# --- Display chat history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("🔗 Sources"):
                for s in msg["sources"]:
                    st.markdown(f"- [{s['title']}]({s['uri']})")

# --- Chat input ---
if prompt := st.chat_input("Ask anything — news, trends, facts..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🌐 Searching Google live..."):
            # Recreate client fresh every time to avoid "client closed" error
            client = genai.Client(api_key=api_key)
            chat = client.chats.create(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.2
                ),
                history=st.session_state.history
            )
            response = chat.send_message(prompt)
            reply = response.text
            st.markdown(reply)

            # Extract sources
            sources = []
            try:
                chunks = response.candidates[0].grounding_metadata.grounding_chunks
                sources = [{"title": c.web.title, "uri": c.web.uri} for c in chunks if c.web]
                if sources:
                    with st.expander("🔗 Sources"):
                        for s in sources:
                            st.markdown(f"- [{s['title']}]({s['uri']})")
            except:
                pass

    # Save to display history and raw history for next turn
    st.session_state.messages.append({"role": "assistant", "content": reply, "sources": sources})
    st.session_state.history = chat.get_history()

