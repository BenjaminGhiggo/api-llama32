import streamlit as st
from backend_mercado import market_agent

st.title("Agente de Mercado 📊")
st.markdown("Realiza consultas sobre el mercado y obtén análisis especializados.")

# Inicializar la conversación en el estado de la sesión
if 'conversation_mercado' not in st.session_state:
    st.session_state.conversation_mercado = []

# Entrada del usuario
user_input = st.text_input("Escribe tu pregunta:", key="user_input_mercado")

# Variables para almacenar datos adicionales
categoria = None
ubicacion = None

# Mostrar campos adicionales si la pregunta lo requiere
if "precio promedio" in user_input.lower() and "producto similar" in user_input.lower():
    categoria = st.text_input("Ingresa la categoría de tu producto:", key="categoria_mercado")
if "competitivo" in user_input.lower() and "mi zona" in user_input.lower():
    ubicacion = st.text_input("Ingresa tu ubicación geográfica:", key="ubicacion_mercado")

if st.button("Enviar", key="send_button_mercado"):
    if user_input.strip():
        # Agregar la entrada del usuario a la conversación
        st.session_state.conversation_mercado.append({"role": "user", "content": user_input})
        # Obtener la respuesta del agente de mercado
        assistant_reply = market_agent(st.session_state.conversation_mercado, categoria, ubicacion)
        # Agregar la respuesta del agente a la conversación
        st.session_state.conversation_mercado.append({"role": "assistant", "content": assistant_reply})

# Mostrar la conversación
st.markdown("### Conversación:")
for msg in st.session_state.conversation_mercado:
    if msg['role'] == 'user':
        st.markdown(f"**Tú:** {msg['content']}")
    elif msg['role'] == 'assistant':
        st.markdown(f"**Agente de Mercado:** {msg['content']}")
