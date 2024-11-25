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

# Función para manejar la lógica del agente de marketing
def marketing_agent(conversation, producto=None, objetivo=None, presupuesto=None):
    try:
        # Establecer conexión con la base de datos
        conn = get_db_connection()
        if not conn:
            return "Error al conectar con la base de datos."

        cursor = conn.cursor()

        user_input = conversation[-1]['content']

        # Obtener datos relevantes de la base de datos
        data = query_marketing_data(user_input, cursor, producto, objetivo, presupuesto)

        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()

        # Determinar si se encontró información en la base de datos
        if data:
            # Construir el prompt con datos
            prompt = f"""Eres un experto en marketing que proporciona consejos y estrategias basadas en datos.

Datos relevantes:
{data}

Pregunta del usuario:
{user_input}

Proporciona una respuesta concisa y práctica, limitada a un máximo de 3 párrafos. No incluyas ninguna metadata ni información adicional.

Respuesta del experto:
"""
        else:
            # Construir el prompt sin datos, indicando que uses tu conocimiento
            prompt = f"""Eres un experto en marketing. Proporciona una respuesta concisa y práctica a la siguiente pregunta, basada en tu conocimiento. No incluyas ninguna metadata ni información adicional.

Pregunta del usuario:
{user_input}

Proporciona una respuesta concisa y práctica, limitada a un máximo de 3 párrafos.

Respuesta del experto:
"""

        # Obtener respuesta del modelo
        assistant_reply = get_llama_response(prompt)
        return assistant_reply
    except Exception as e:
        print(f"[ERROR] Ocurrió una excepción en marketing_agent: {e}")
        return f"Error inesperado: {e}"

def query_marketing_data(question, cursor, producto=None, objetivo=None, presupuesto=None):
    try:
        if "crear" in question.lower() and "campaña de marketing" in question.lower():
            if producto and objetivo and presupuesto is not None:
                cursor.execute("""
                    SELECT plataformas_utilizadas, tipo_anuncio, estrategias_utilizadas, presupuesto
                    FROM agente_marketing
                    ORDER BY ABS(presupuesto - %s) ASC, presupuesto DESC, rendimiento DESC
                    LIMIT 1;
                """, (presupuesto,))
                row = cursor.fetchone()
                if row:
                    data = (
                        f"Para tu producto '{producto}' con el objetivo '{objetivo}' y presupuesto ${presupuesto:.2f}, "
                        f"se recomienda usar plataformas '{row[0]}', tipo de anuncio '{row[1]}' y estrategias '{row[2]}'."
                    )
                else:
                    data = None
                return data
            else:
                return None
        else:
            return None
    except Exception as e:
        print(f"[ERROR] Ocurrió una excepción en query_marketing_data: {e}")
        return None

if __name__ == "__main__":
    # Interacción en la terminal para depuración
    conversation = []
    print("Agente de Marketing 📣")
    print("Escribe 'salir' para terminar la conversación.")
    while True:
        user_input = input("Tú: ")
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("Agente de Marketing: ¡Hasta luego!")
            break

        # Variables adicionales
        producto = None
        objetivo = None
        presupuesto = None

        if "crear" in user_input.lower() and "campaña de marketing" in user_input.lower():
            producto = input("Ingresa el nombre de tu producto: ")
            objetivo = input("Ingresa el objetivo de tu campaña: ")
            while True:
                presupuesto_input = input("Ingresa tu presupuesto: ")
                try:
                    presupuesto = float(presupuesto_input)
                    break
                except ValueError:
                    print("Por favor, ingresa un valor numérico válido para el presupuesto.")

        conversation.append({"role": "user", "content": user_input})
        assistant_reply = marketing_agent(conversation, producto, objetivo, presupuesto)
        print(f"Agente de Marketing: {assistant_reply}")
        conversation.append({"role": "assistant", "content": assistant_reply})
