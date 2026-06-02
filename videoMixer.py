import os
import json
import asyncio
import edge_tts
# Importación adaptada a MoviePy v2.x para evitar el ModuleNotFoundError
from moviepy import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip, ColorClip

def cargar_datos_proyecto():
    try:
        with open("prompts_produccion.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("Error: No se encontró 'prompts_produccion.json'. Ejecutá primero el orquestador.")

async def generar_voces_por_segmento(shot_list, carpeta_clips="outputs1"):
    """
    Genera la locución de voz en off (edge-tts) en archivos de audio independientes
    para cada segmento de video en paralelo.
    """
    tareas = []
    for shot in shot_list:
        clip_num = shot.get("clip")
        # Usamos el subtítulo de saliencia como la locución corta para asegurar sincronía
        narracion = shot.get("subtitulo_saliencia", "").strip()
        ruta_audio = os.path.join(carpeta_clips, f"audio_clip{clip_num}.mp3")
        
        print(f"  > [Voz] Generando locución para Clip {clip_num}: '{narracion}'")
        communicate = edge_tts.Communicate(narracion, "es-MX-DaliaNeural")
        tareas.append(communicate.save(ruta_audio))
        
    await asyncio.gather(*tareas)

def ensamblar_reels_ihm():
    # 1. Cargar metadatos del JSON dinámico
    datos = cargar_datos_proyecto()
    shot_list = datos.get("shot_list_12s") if "shot_list_12s" in datos else datos.get("shot_list_6s", [])

    carpeta_clips = "outputs1"
    
    # Validar que la carpeta exista
    if not os.path.exists(carpeta_clips):
        os.makedirs(carpeta_clips)
        print(f"[!] Carpeta '{carpeta_clips}' creada. Colocá allí clip1.mp4, clip2.mp4 y clip3.mp4.")
        return

    print(f"\n[Fase 7 - Voces] Generando locuciones segmentadas de forma paralela...")
    asyncio.run(generar_voces_por_segmento(shot_list, carpeta_clips))

    print(f"\n[Fase 6 - Ensamblaje] Leyendo fragmentos y sincronizando con sus audios...")
    
    clips_procesados = []
    recursos_a_cerrar = []
    
    # Ruta estándar de Arial Bold en Windows para asegurar consistencia
    ruta_fuente_windows = r"C:\Windows\Fonts\arialbd.ttf"
    fuente_configurada = ruta_fuente_windows if os.path.exists(ruta_fuente_windows) else "Arial"
    color_fondo_seguro = (0, 0, 0, 180) # Transparencia adecuada para contraste figura-fondo

    for idx, shot in enumerate(shot_list, start=1):
        ruta_vid = os.path.join(carpeta_clips, f"clip{idx}.mp4")
        ruta_aud = os.path.join(carpeta_clips, f"audio_clip{idx}.mp3")
        
        if not os.path.exists(ruta_vid):
            print(f"  [!] Error: No se encuentra el video indispensable: '{ruta_vid}'")
            return
        if not os.path.exists(ruta_aud):
            print(f"  [!] Error: No se encuentra el audio generado: '{ruta_aud}'")
            return

        print(f"  > Procesando segmento {idx}...")
        clip_vid = VideoFileClip(ruta_vid)
        audio_clip = AudioFileClip(ruta_aud)
        recursos_a_cerrar.extend([clip_vid, audio_clip])

        # Sincronización exacta: forzar la duración del video de cada segmento a exactamente 4.0s
        dur_segmento = 4.0
        clip_vid = clip_vid.with_duration(dur_segmento)
        
        # Cargar audio de ambiente (SFX/música) respectivo para el momento de punción actual
        bg_nombres = ["muerte.mp3", "neutro.mp3", "vida.mp3"]
        ruta_bg = os.path.join("audios", bg_nombres[idx - 1])
        
        if os.path.exists(ruta_bg):
            print(f"    - Mezclando pista de ambiente: '{ruta_bg}'")
            bg_clip = AudioFileClip(ruta_bg).with_volume_scaled(0.3)
            recursos_a_cerrar.append(bg_clip)
            # Mezclar locución y música de fondo usando CompositeAudioClip
            audio_sincronizado = CompositeAudioClip([audio_clip, bg_clip]).with_duration(dur_segmento)
        else:
            print(f"    [!] Advertencia: No se encontró '{ruta_bg}', usando solo voz.")
            # Rellenar con silencio hasta llegar a los 4.0s y evitar desbordamientos
            audio_sincronizado = CompositeAudioClip([audio_clip]).with_duration(dur_segmento)
            
        clip_vid_sincronizado = clip_vid.with_audio(audio_sincronizado)

        # Preparar el subtítulo (mostrando el subtítulo corto de forma segura)
        sub_text = shot.get("subtitulo_saliencia", "").strip()
        print(f"    - Subtítulo de Clip {idx} ({dur_segmento:.2f}s): '{sub_text}'")

        try:
            # Quitamos bg_color para que la tipografía no se recorte por los límites ajustados de ImageMagick
            clip_texto = TextClip(
                text=sub_text, 
                font=fuente_configurada,
                font_size=32,         # Fuente reducida para evitar cortes y solapamientos
                color="white",
                bg_color=None,
                size=(clip_vid.w - 120, None), # Ancho restringido con márgenes amplios
                method="caption"
            )
        except Exception as e:
            print(f"    [!] Fallback de tipografía universal por: {e}")
            clip_texto = TextClip(
                text=sub_text,
                font_size=32,
                color="white",
                bg_color=None,
                size=(clip_vid.w - 120, None),
                method="caption"
            )

        # Caja de subtítulos ampliada con padding personalizado
        # Agregamos padding de 40px horizontales (20px cada lado) y 20px verticales (10px arriba/abajo)
        padding_x = 40
        padding_y = 20
        box_w = clip_texto.w + padding_x
        box_h = clip_texto.h + padding_y

        pos_y = clip_vid.h - 320

        # Crear fondo negro semi-transparente con el tamaño ampliado (70% de opacidad)
        bg_box = (ColorClip(size=(box_w, box_h), color=(0, 0, 0))
                  .with_opacity(0.7)
                  .with_start(0)
                  .with_duration(dur_segmento)
                  .with_position(('center', pos_y)))

        # Posicionar el texto centrado verticalmente dentro de la caja de fondo
        clip_texto = (clip_texto
                      .with_start(0)
                      .with_duration(dur_segmento)
                      .with_position(('center', pos_y + (padding_y // 2))))

        # Componer clip del segmento actual con el fondo y luego el texto
        clip_compuesto = CompositeVideoClip([clip_vid_sincronizado, bg_box, clip_texto])
        clips_procesados.append(clip_compuesto)

    # 2. Concatenación nativa de todos los segmentos ya sincronizados
    print("  > Concatenando los segmentos compuestos...")
    video_concatenado = concatenate_videoclips(clips_procesados, method="compose")

    # 3. Inyección de Barra de Progreso Dinámica (Visual Pacing para TDAH) sobre el video unificado
    print("[Fase 7 - Visual Pacing] Inyectando barra de progreso de alta saliencia...")
    duracion_total = video_concatenado.duration

    def filter_frame_progreso(get_frame, t):
        frame = get_frame(t).copy() # Copia del frame actual (RGB)
        h, w, c = frame.shape
        
        # Porcentaje del tiempo transcurrido
        progreso = min(1.0, max(0.0, t / duracion_total))
        barra_w = int(w * progreso)
        barra_h = 12 # Grosor de la barra
        
        # Color amarillo brillante (RGB: [255, 223, 0]) para contraste óptimo sobre la base
        frame[h - barra_h:h, 0:barra_w] = [255, 223, 0]
        return frame

    # Aplicamos el filtro de cuadro
    video_final = video_concatenado.transform(filter_frame_progreso)

    # 4. Renderizado de producción
    ruta_salida_final = "output_final/video_final_tdah.mp4"
    os.makedirs("output_final", exist_ok=True)
    
    print(f"\n[Exportación] Compilando reel definitivo ({duracion_total:.2f}s)...")
    video_final.write_videofile(
        ruta_salida_final,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )
    
    # Cerrar descriptores para liberar recursos de memoria en Windows
    video_final.close()
    video_concatenado.close()
    for cp in clips_procesados:
        cp.close()
    for r in recursos_a_cerrar:
        try:
            r.close()
        except:
            pass
            
    print(f"\n[ÉXITO TOTAL] Tu video final sincronizado y sin SFX está listo.")
    print(f"-> Ubicación del entregable: '{ruta_salida_final}'")

if __name__ == "__main__":
    try:
        ensamblar_reels_ihm()
    except Exception as e:
        print(f"\n[ERROR] Falló el proceso de compilación: {e}")