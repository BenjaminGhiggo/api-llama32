import ollama
import os
import psycopg2
from dotenv import load_dotenv
from typing import Optional  # Asegúrate de importar Optional

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de Ollama y el modelo
MODEL_NAME = "llama3.2:3b"

# Conexión a la base de datos PostgreSQL
def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("HOST"),
            user="postgres",
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
def market_agent(user_input: str, categoria: Optional[str] = None, ubicacion: Optional[str] = None) -> str:
    try:
        # Establecer conexión con la base de datos
        conn = get_db_connection()
        if not conn:
            return "Error al conectar con la base de datos."

        cursor = conn.cursor()

        # Obtener datos relevantes de la base de datos
        data = query_market_data(user_input, cursor, categoria, ubicacion)

        # Imprimir los datos obtenidos para depuración
        print(f"[DEBUG] Datos obtenidos de la base de datos: {data}")

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

        # Imprimir el prompt construido para depuración
        print(f"[DEBUG] Prompt construido:\n{prompt}")

        # Obtener respuesta del modelo
        assistant_reply = get_llama_response(prompt)
        return assistant_reply
    except Exception as e:
        print(f"[ERROR] Ocurrió una excepción en market_agent: {e}")
        return f"Error inesperado: {e}"

def query_market_data(question: str, cursor, categoria: Optional[str] = None, ubicacion: Optional[str] = None) -> Optional[str]:
    try:
        # Verificar si la pregunta contiene "precio promedio" y "producto similar"
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
                    print("[DEBUG] No se encontraron precios promedio para la categoría proporcionada.")
                    return None
            else:
                print("[DEBUG] 'categoria' no proporcionada en la solicitud.")
                return None
        # Verificar si la pregunta contiene "competitivo" y "mi zona"
        elif "competitivo" in question.lower() and "mi zona" in question.lower():
            if ubicacion:
                cursor.execute("""
                    SELECT COUNT(*) FROM agente_mercado
                    WHERE ubicacion_geografica = %s;
                """, (ubicacion,))
                competitors = cursor.fetchone()[0]
                return f"En tu zona ({ubicacion}), hay {competitors} competidores en tu categoría de producto."
            else:
                print("[DEBUG] 'ubicacion' no proporcionada en la solicitud.")
                return None
        # Verificar si la pregunta contiene "mercados internacionales" e "interesados"
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
                print("[DEBUG] No se encontraron mercados internacionales en la base de datos.")
                return None
        else:
            print("[DEBUG] La pregunta no coincide con ninguna consulta predefinida.")
            return None
    except Exception as e:
        print(f"[ERROR] Ocurrió una excepción en query_market_data: {e}")
        return None
