import streamlit as st
from backend_financiero import financial_agent

# Inicializar conversación en el estado de la sesión
if "conversation_financiero" not in st.session_state:
    st.session_state.conversation_financiero = []

st.title("Agente Financiero 💰")
st.markdown("Haz tus preguntas financieras y recibe asesoramiento experto.")

# Entrada del usuario
user_input = st.text_input("Escribe tu pregunta:", key="user_input_financiero")

if st.button("Enviar", key="send_button_financiero"):
    if user_input.strip():
        st.session_state.conversation_financiero.append({"role": "user", "content": user_input})
        assistant_reply = financial_agent(st.session_state.conversation_financiero)
        st.session_state.conversation_financiero.append({"role": "assistant", "content": assistant_reply})

# Mostrar la conversación
st.markdown("### Conversación:")
for msg in st.session_state.conversation_financiero:
    if msg["role"] == "user":
        st.markdown(f"**Tú:** {msg['content']}")
    elif msg["role"] == "assistant":
        st.markdown(f"**Agente Financiero:** {msg['content']}")
