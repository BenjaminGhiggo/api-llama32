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

# Función para manejar la lógica del agente de mercado
def market_agent(conversation, categoria=None, ubicacion=None):
    try:
        # Establecer conexión con la base de datos
        conn = get_db_connection()
        if not conn:
            return "Error al conectar con la base de datos."

        cursor = conn.cursor()

        user_input = conversation[-1]['content']

        # Obtener datos relevantes de la base de datos
        data = query_market_data(user_input, cursor, categoria, ubicacion)

        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()

        # Determinar si se encontró información en la base de datos
        if data:
            # Construir el prompt con datos
            prompt = f"""Eres un analista de mercado experto que proporciona insights basados en datos.

Datos relevantes:
{data}

Pregunta del usuario:
{user_input}

Proporciona una respuesta concisa y práctica, limitada a un máximo de 3 párrafos. No incluyas ninguna metadata ni información adicional.

Respuesta del analista:
"""
        else:
            # Construir el prompt sin datos, indicando que uses tu conocimiento
            prompt = f"""Eres un analista de mercado experto. Proporciona una respuesta concisa y práctica a la siguiente pregunta, basada en tu conocimiento. No incluyas ninguna metadata ni información adicional.

Pregunta del usuario:
{user_input}

Proporciona una respuesta concisa y práctica, limitada a un máximo de 3 párrafos.

Respuesta del analista:
"""

        # Obtener respuesta del modelo
        assistant_reply = get_llama_response(prompt)
        return assistant_reply
    except Exception as e:
        print(f"[ERROR] Ocurrió una excepción en market_agent: {e}")
        return f"Error inesperado: {e}"

def query_market_data(question, cursor, categoria=None, ubicacion=None):
    try:
        if "precio promedio" in question.lower() and "producto similar" in question.lower():
            if categoria:
                cursor.execute("""
                    SELECT AVG(precio) FROM agente_mercado
                    WHERE categoria = %s;
                """, (categoria,))
                avg_price = cursor.fetchone()[0]
                if avg_price:
                    return f"El precio promedio de productos similares en la categoría '{categoria}' es ${avg_price:.2f}."
                else:
                    return None
            else:
                return None
        elif "competitivo" in question.lower() and "mi zona" in question.lower():
            if ubicacion:
                cursor.execute("""
                    SELECT COUNT(*) FROM agente_mercado
                    WHERE ubicacion_geografica = %s;
                """, (ubicacion,))
                competitors = cursor.fetchone()[0]
                return f"En tu zona ({ubicacion}), hay {competitors} competidores en tu categoría de producto."
            else:
                return None
        elif "mercados internacionales" in question.lower() and "interesados" in question.lower():
            cursor.execute("""
                SELECT mercados_internacionales FROM agente_mercado;
            """)
            rows = cursor.fetchall()
            if rows:
                mercados = set()
                for row in rows:
                    mercados.update(map(str.strip, row[0].split(",")))
                return f"Mercados internacionales potenciales: {', '.join(mercados)}."
            else:
                return None
        else:
            return None
    except Exception as e:
        print(f"[ERROR] Ocurrió una excepción en query_market_data: {e}")
        return None

if __name__ == "__main__":
    # Interacción en la terminal para depuración
    conversation = []
    print("Agente de Mercado 📊")
    print("Escribe 'salir' para terminar la conversación.")
    while True:
        user_input = input("Tú: ")
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("Agente de Mercado: ¡Hasta luego!")
            break

        # Variables adicionales
        categoria = None
        ubicacion = None

        if "precio promedio" in user_input.lower() and "producto similar" in user_input.lower():
            categoria = input("Ingresa la categoría de tu producto: ")
        if "competitivo" in user_input.lower() and "mi zona" in user_input.lower():
            ubicacion = input("Ingresa tu ubicación geográfica: ")

        conversation.append({"role": "user", "content": user_input})
        assistant_reply = market_agent(conversation, categoria, ubicacion)
        print(f"Agente de Mercado: {assistant_reply}")
        conversation.append({"role": "assistant", "content": assistant_reply})
