import ollama
import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de Ollama y el modelo
MODEL_NAME = "llama3.2:3b"

# Conexión a la base de datos PostgreSQL
def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("HOST"),
            user=os.getenv("USER"),
            password=os.getenv("PASSWORD"),
            dbname=os.getenv("DATABASE"),
            port=os.getenv("PORT")
        )
    except Exception as e:
        print(f"[ERROR] Error al conectar a la base de datos: {e}")
        return None

# Función para obtener respuesta del modelo Llama 3.2 utilizando Ollama
def get_llama_response(prompt):
    try:
        # Imprimir el prompt para depuración
        print("\n[DEBUG] Prompt enviado al modelo:")
        print(prompt)
        print("\n[DEBUG] Generando respuesta...\n")

        response = ''
        for chunk in ollama.generate(model=MODEL_NAME, prompt=prompt):
            # Agregar declaración de depuración
            print(f"[DEBUG] Chunk recibido: {repr(chunk)}")
            # Manejar diferentes tipos de 'chunk'
            if isinstance(chunk, tuple):
                if chunk[0] == 'response':
                    # Asegurarse de que chunk[1] es una cadena de texto
                    response += str(chunk[1])
            elif isinstance(chunk, dict):
                if 'response' in chunk:
                    response += str(chunk['response'])
            elif isinstance(chunk, str):
                # Ignorar strings que no están bajo 'response'
                pass

        # Limpiar la respuesta
        response = response.strip()

        # Si la respuesta está vacía, informar
        if not response:
            print("[DEBUG] La respuesta del modelo está vacía.")
            return "Lo siento, no pude generar una respuesta adecuada. Por favor, intenta con otra pregunta."

        # Limitar la respuesta a los primeros 3 párrafos
        paragraphs = response.split('\n\n')
        limited_response = '\n\n'.join(paragraphs[:3])

        return limited_response
    except Exception as e:
        print(f"[ERROR] Ocurrió una excepción en get_llama_response: {e}")
        return f"Error inesperado: {e}"

# Función para manejar la lógica del agente financiero
def financial_agent(conversation):
    try:
        # Establecer conexión con la base de datos
        conn = get_db_connection()
        if not conn:
            return "Error al conectar con la base de datos."

        cursor = conn.cursor()

        user_input = conversation[-1]['content']

        # Obtener datos relevantes de la base de datos
        data = query_financial_data(user_input, cursor)

        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()

        # Determinar si se encontró información en la base de datos
        if data:
            # Construir el prompt con datos
            prompt = f"""Eres un asesor financiero experto que proporciona respuestas detalladas basadas en los datos proporcionados.

Datos relevantes:
{data}

Pregunta del usuario:
{user_input}

Proporciona una respuesta concisa y práctica, limitada a un máximo de 3 párrafos. No incluyas ninguna metadata ni información adicional.

Respuesta del asesor:
"""
        else:
            # Construir el prompt sin datos, indicando que uses tu conocimiento
            prompt = f"""Eres un asesor financiero experto. Proporciona una respuesta concisa y práctica a la siguiente pregunta, basada en tu conocimiento. No incluyas ninguna metadata ni información adicional.

Pregunta del usuario:
{user_input}

Proporciona una respuesta concisa y práctica, limitada a un máximo de 3 párrafos.

Respuesta del asesor:
"""

        # Obtener respuesta del modelo
        assistant_reply = get_llama_response(prompt)
        return assistant_reply
    except Exception as e:
        print(f"[ERROR] Ocurrió una excepción en financial_agent: {e}")
        return f"Error inesperado: {e}"

def query_financial_data(question, cursor):
    try:
        if "financiamiento" in question.lower() and "negocio pequeño" in question.lower():
            cursor.execute("""
                SELECT opciones_financiamiento FROM agente_financiero
                WHERE tipo_negocio = 'Pequeño';
            """)
            rows = cursor.fetchall()
            if rows:
                opciones = set()
                for row in rows:
                    opciones.update(map(str.strip, row[0].split(",")))
                return f"Opciones de financiamiento para negocios pequeños: {', '.join(opciones)}"
            else:
                return None
        elif "califico para un préstamo" in question.lower():
            cursor.execute("""
                SELECT nivel_endeudamiento, ingresos_mensuales FROM agente_financiero;
            """)
            rows = cursor.fetchall()
            if rows:
                niveles = [row[0] for row in rows]
                ingresos = [row[1] for row in rows]
                if len(ingresos) == 0:
                    promedio_ingresos = 0
                else:
                    promedio_ingresos = sum(ingresos) / len(ingresos)
                return f"El nivel de endeudamiento promedio es {niveles.count('Bajo') / len(niveles) * 100:.2f}% bajo. Los ingresos mensuales promedio son ${promedio_ingresos:.2f}."
            else:
                return None
        elif "documentos necesito" in question.lower() and "préstamo" in question.lower():
            cursor.execute("""
                SELECT DISTINCT documentos_necesarios FROM agente_financiero;
            """)
            rows = cursor.fetchall()
            if rows:
                documentos = set()
                for row in rows:
                    documentos.update(map(str.strip, row[0].split(",")))
                return f"Documentos necesarios para pedir un préstamo: {', '.join(documentos)}"
            else:
                return None
        else:
            return None
    except Exception as e:
        print(f"[ERROR] Ocurrió una excepción en query_financial_data: {e}")
        return None

if __name__ == "__main__":
    # Interacción en la terminal para depuración
    conversation = []
    print("Agente Financiero 💰")
    print("Escribe 'salir' para terminar la conversación.")
    while True:
        user_input = input("Tú: ")
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("Agente Financiero: ¡Hasta luego!")
            break
        conversation.append({"role": "user", "content": user_input})
        assistant_reply = financial_agent(conversation)
        print(f"Agente Financiero: {assistant_reply}")
        conversation.append({"role": "assistant", "content": assistant_reply})
