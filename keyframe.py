import os
import cv2

def extraer_ultimo_frame_automatico(video_arg=None):
    carpeta_clips = "outputs1"
    
    # 1. Asegurar robustez: si la carpeta no existe, la creamos
    if not os.path.exists(carpeta_clips):
        os.makedirs(carpeta_clips)
        print(f"[!] Se creó la carpeta '{carpeta_clips}'. Descargá ahí tus clips de Google Flow.")
        return

    # Escanear archivos mp4 en outputs1
    videos = [v for v in os.listdir(carpeta_clips) if v.lower().endswith('.mp4')]
    
    if not videos:
        print(f"\n[!] La carpeta '{carpeta_clips}' está vacía.")
        print("-> Bajate el primer clip de Google Flow y guardalo como 'clip1.mp4' adentro de esa carpeta.")
        return

    print("\n" + "="*60)
    print("   [KEYFRAME MANAGER] - SELECCIÓN DE ASSET DE VIDEO ")
    print("="*60)
    print(f"Videos detectados en '{carpeta_clips}':")
    for idx, v in enumerate(videos, start=1):
        print(f"  [{idx}] {v}")
        
    if video_arg:
        seleccion = str(video_arg)
        print(f"\nUsando video seleccionado por CLI: \"{seleccion}\"")
    else:
        seleccion = input("\nIntroduce el número o el nombre exacto del video (ej. clip1.mp4):\n>> ")
    
    # Resolver el archivo seleccionado
    video_elegido = ""
    if seleccion.isdigit() and 1 <= int(seleccion) <= len(videos):
        video_elegido = videos[int(seleccion) - 1]
    else:
        video_elegido = seleccion if seleccion in videos else ""

    if not video_elegido:
        print("[!] Selección inválida. Reintentá el proceso.")
        return

    ruta_completa_video = os.path.join(carpeta_clips, video_elegido)
    nombre_base = os.path.splitext(video_elegido)[0]
    
    # La imagen final se guarda en la raíz para que la encuentres rápido y la subas a la web
    ruta_salida_imagen = f"referencia_siguiente_de_{nombre_base}.png"

    print(f"\nProcesando fotogramas analíticos de: {ruta_completa_video}...")
    cap = cv2.VideoCapture(ruta_completa_video)
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    if total_frames <= 0:
        print("[!] Error: No se pudieron leer los fotogramas del video.")
        cap.release()
        return

    # Posicionamos OpenCV exactamente en el último frame (total - 1)
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
    exito, frame = cap.read()
    
    if exito:
        cv2.imwrite(ruta_salida_imagen, frame)
        print("\n" + "="*50)
        print("   ¡KEYFRAME EXTRAÍDO CON ÉXITO! ")
        print("="*50)
        print(f"-> Archivo guardado en la raíz como: '{ruta_salida_imagen}'")
        print(f"-> Total frames: {total_frames} | FPS: {fps:.2f}")
        print("Subí esta imagen como referencia (Image-to-Video) para tu siguiente prompt en Flow.")
        print("="*50)
    else:
        print("[!] Error crítico al renderizar el frame final.")
        
    cap.release()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extrae el último frame de un clip de video.")
    parser.add_argument("--video", "-v", type=str, help="Nombre o índice del video a procesar (ej. clip1.mp4 o 1)")
    args = parser.parse_args()
    
    try:
        extraer_ultimo_frame_automatico(args.video)
    except Exception as e:
        print(f"Error en el ejecutable: {e}")