import os
import json
import re
import pdfplumber
from groq import Groq

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def inicializar_groq_local():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Error Crítico: No se encontró la variable de entorno 'GROQ_API_KEY'.")
    return Groq(api_key=api_key)

def escanear_y_extraer_inputs(carpeta_inputs="inputs"):
    if not os.path.exists(carpeta_inputs):
        os.makedirs(carpeta_inputs)
        print(f"-> Se creó la carpeta '{carpeta_inputs}'. Coloca tus PDFs ahí y vuelve a ejecutar.")
        return ""

    archivos = [f for f in os.listdir(carpeta_inputs) if f.lower().endswith('.pdf')]
    
    if not archivos:
        print(f"-> Advertencia: La carpeta '{carpeta_inputs}' no contiene archivos .pdf.")
        return ""

    print(f"\n[Fase 1 - Ingesta Multi-PDF] Se detectaron {len(archivos)} archivo(s) para procesamiento:")
    texto_consolidado = ""
    
    for archivo in archivos:
        ruta_completa = os.path.join(carpeta_inputs, archivo)
        print(f"  > Extrayendo semántica de: {archivo}...")
        try:
            with pdfplumber.open(ruta_completa) as pdf:
                for page in pdf.pages:
                    texto_consolidado += page.extract_text() or ""
                texto_consolidado += "\n\n"
        except Exception as e:
            print(f"  [!] Error al leer {archivo}: {e}")
            
    return texto_consolidado

def generar_ingenieria_prompts_12s(texto_base, instruccion_usuario):
    client = inicializar_groq_local()

    prompt_sistema = (
        "Actúas como un Orquestador Narrativo avanzado experto en Psicología del TDAH y Diseño de Interfaces (IHM). "
        "Tu objetivo es fusionar el conocimiento de múltiples PDFs con la petición en lenguaje natural del usuario. "
        "Debes expresar un guion técnico preciso para un video vertical (9:16) compuesto por exactamente 3 clips de 4 segundos cada uno (Total: 12s, cumpliendo la consigna de durar entre 8 y 15 segundos). "
        "Responde estructurando los datos estrictamente dentro de un objeto JSON estructurado."
    )

    prompt_usuario = f"""
    BASE DE CONOCIMIENTO (PDFs consolidados de la carpeta inputs):
    ---
    {texto_base[:6000]}
    ---

    PETICIÓN CREATIVA DEL USUARIO (Desde consola):
    "{instruccion_usuario}"

    TAREA DE INGENIERÍA:
    Diseñá el Shot List y la Scene Bible para un video de 12 segundos optimizado para TDAH, dividido en 3 bloques de 4 segundos.
    Debés crear de forma original el argumento del video basándote únicamente en el contexto provisto por la BASE DE CONOCIMIENTO (los PDFs) y la petición libre de la historia provista en "instruccion_usuario" por el usuario. Mapeá esta historia a la estructura de la curva de tensión atencional del TDAH y asegurá la continuidad de movimiento (raccord cinemático) para evitar teletransportaciones o inconsistencias de dirección física:
    
    - Clip 1 (0-4 segundos): Punción de Muerte (PM).
      Subtítulo de saliencia: Un gancho atencional en español neutro/estándar conjugado en segunda persona ("tú", ej. "¿pierdes el colectivo y no llegas a tiempo?") o tercera persona ("usted", ej. "¿pierde el colectivo de Paraná y se queda sin transporte?"), con una longitud de estrictamente 7 a 9 palabras. Debe ser directo y de alta tensión.
    - Clip 2 (4-8 segundos): Bloque Neutro (N).
      Subtítulo de saliencia: Mensaje de pausa y reorientación en español neutro/estándar conjugado en segunda persona ("tú") o tercera persona ("usted"), con una longitud de estrictamente 7 a 9 palabras (ej. "Descubre una alternativa digital inteligente para tu viaje").
    - Clip 3 (8-12 segundos): Punción de Vida (PV).
      Subtítulo de saliencia: Cierre y recompensa con la marca en español neutro/estándar conjugado en segunda persona ("tú") o tercera persona ("usted"), con una longitud de estrictamente 7 a 9 palabras (ej. "¡Viaja de forma más simple con UniPase hoy!").

    El contenido visual, acciones, personajes y locaciones de cada uno de los 3 clips deben ser generados libre y dinámicamente por vos basándote en la idea ingresada en "instruccion_usuario" y el contexto del PDF, sin asumir ni imponer ninguna acción predefinida o elemento fijo (como abrir celulares, subir a colectivos o mostrar credenciales) a menos que la historia elegida por el usuario así lo requiera.

    REQUISITO DE COHERENCIA VISUAL (Scene Bible) Y PROMPTS EXPERTOS:
    * La Scene Bible (campos: character_description, environment_setup, camera_style) debe contener únicamente características visuales ESTÁTICAS, físicas y permanentes (edad, rasgos físicos, ropa fija, locación general y estilo de cámara en INGLÉS). NO debe mencionar estados de ánimo cambiantes entre clips, punciones, transiciones, ni expresiones como "frustrated in the first clip" o "happy in the third". Esto es crítico para evitar que la IA genere imágenes divididas en 4 paneles (collages o grillas).
    * Para los 3 prompts de video en 'shot_list_12s', debés usar DIRECTIVAS DE CÁMARA Y PERSPECTIVA EXPERTAS en inglés para evitar alucinaciones físicas o anatómicas comunes en la IA de video (por ejemplo, que se vea la pantalla del celular desde atrás o que las manos se deformen).
    * Regla de control de continuidad de movimiento y espacial: Especificá la dirección de movimiento consistente (de izquierda a derecha) y la acción de abordar el vehículo para evitar saltos ilógicos.
    * Regla de control emocional y continuidad de estados de ánimo: Los estados de ánimo y expresiones cambiantes del personaje deben ser descritos ÚNICAMENTE en la acción del 'prompt_video' individual en 'shot_list_12s':
      - En el 'prompt_video' del Clip 1 (PM): Describir la acción física con una emoción de frustración, enojo, tensión o desilusión visible.
      - En el 'prompt_video' del Clip 2 (N): Describir la acción física con una emoción neutra, pensativa, curiosa o de alivio gradual.
      - En el 'prompt_video' del Clip 3 (PV): Describir la acción física con una emoción de felicidad, satisfacción, alivio completo y sonrisa sincera.
    * Los prompts resultantes deben describir una acción fluida de 4 segundos sin incluir textos legibles ni asumir audio.

    ESTRUCTURA JSON REQUERIDA (Genera el JSON limpio, sin Markdown alrededor si es posible, o bien delimitado):
    {{
      "idea_fuerza_comunicacional": "Idea central clara del video",
      "scene_bible_ingles": {{
        "character_description": "Detailed stable character look in English",
        "environment_setup": "Stable location setup and lighting in English",
        "camera_style": "9:16 vertical aspect ratio, 35mm lens, realistic cinematic look"
      }},
      "shot_list_12s": [
        {{ "clip": 1, "tiempo": "0-4s", "fase": "Punción de Muerte (PM)", "prompt_video": "Detailed visual action in English matching the Scene Bible.", "subtitulo_saliencia": "Spanish subtitle in standard grammar for Clip 1 (7-9 words)" }},
        {{ "clip": 2, "tiempo": "4-8s", "fase": "Neutro (N)", "prompt_video": "Detailed visual action in English matching the Scene Bible.", "subtitulo_saliencia": "Spanish subtitle in standard grammar for Clip 2 (7-9 words)" }},
        {{ "clip": 3, "tiempo": "8-12s", "fase": "Punción de Vida (PV)", "prompt_video": "Detailed visual action in English matching the Scene Bible.", "subtitulo_saliencia": "Spanish subtitle in standard grammar for Clip 3 (7-9 words)" }}
      ]
    }}
    """

    print("\n[Fases 2-4] Procesando el guion con Llama 3.3 en Groq Cloud...")
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": prompt_usuario}
        ],
        temperature=0.2
    )

    respuesta_raw = completion.choices[0].message.content

    # --- BLINDAJE ANTI-FALLOS: Extractor de JSON robusto ---
    try:
        match = re.search(r'\{.*\}', respuesta_raw, re.DOTALL)
        if match:
            json_limpio = match.group(0)
            return json.loads(json_limpio)
        else:
            raise ValueError("No se encontró una estructura JSON válida en la respuesta del modelo.")
    except json.JSONDecodeError:
        print("\n[!] Error de parseo. Contenido crudo devuelto por la IA para debug:")
        print(respuesta_raw)
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Orquestador Dinámico (3 Clips x 4 Segundos) para TDAH")
    parser.add_argument("--prompt", "-p", type=str, help="Historia o instrucción para darle al video (si no se provee, se solicitará de forma interactiva)")
    args = parser.parse_args()

    print("="*65)
    print("  ORQUESTADOR DINÁMICO (3 CLIPS X 4 SEGUNDOS) PARA TDAH ")
    print("="*65)
    
    texto_base = escanear_y_extraer_inputs("inputs")
    
    if not texto_base:
        print("\n[!] Error: No hay PDFs detectados en 'inputs'. Coloca tus archivos allí y reejecuta.")
    else:
        if args.prompt:
            mensaje_consola = args.prompt
            print(f"\nUsando instrucción CLI: \"{mensaje_consola}\"")
        else:
            mensaje_consola = input("\n¿Qué historia o instrucción querés darle al video?\n>> ")

        try:
            resultado = generar_ingenieria_prompts_12s(texto_base, mensaje_consola)
            
            with open("prompts_produccion.json", "w", encoding="utf-8") as f:
                json.dump(resultado, f, indent=4, ensure_ascii=False)
                
            print("\n" + "="*65)
            print(" ¡PROMPTS ADAPTADOS PARA 12 SEGUNDOS GENERADOS CON ÉXITO! ")
            print("="*65)
            print(f"Idea Fuerza: {resultado['idea_fuerza_comunicacional']}\n")
            
            for shot in resultado['shot_list_12s']:
                print(f"--- CLIP {shot['clip']} ({shot['tiempo']}) | FASE: {shot['fase']} ---")
                print(f"SUBTÍTULO DE SALIENCIA: {shot['subtitulo_saliencia']}")
                print(f"NARRACIÓN (LOCUCIÓN): {shot.get('narracion', 'N/A')}")
                print(f"PROMPT PARA PEGAR EN LA IA DE VIDEO:\n{shot['prompt_video']}")
                print("-"*65)
                
            print("\n[INFO] Pipeline finalizado. Datos guardados localmente en 'prompts_produccion.json'.")
            
        except Exception as e:
            print(f"\n[ERROR] El pipeline falló durante la generación: {e}")