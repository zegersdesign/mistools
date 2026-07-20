#!/usr/bin/env python3
"""
YouTube Transcript Downloader
Descarga transcripts de videos de YouTube y los guarda por idioma.

Uso:
    python youtube_transcripts.py <url_o_video_id> [url2] [url3] ...
    python youtube_transcripts.py --file lista.txt
    python youtube_transcripts.py --lista-idiomas <url>

Instalación de dependencias:
    pip install youtube-transcript-api yt-dlp
"""

import sys
import os
import re
import argparse
from pathlib import Path
from datetime import datetime


def instalar_dependencias():
    """Instala las dependencias necesarias si no están disponibles."""
    import subprocess
    print("Instalando dependencias...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "youtube-transcript-api", "yt-dlp"])


try:
    from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
    from youtube_transcript_api.formatters import TextFormatter
except ImportError:
    instalar_dependencias()
    from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
    from youtube_transcript_api.formatters import TextFormatter


IDIOMAS_NOMBRES = {
    "es": "Español",
    "en": "Inglés",
    "pt": "Portugués",
    "fr": "Francés",
    "de": "Alemán",
    "it": "Italiano",
    "ja": "Japonés",
    "ko": "Coreano",
    "zh": "Chino",
    "zh-Hans": "Chino Simplificado",
    "zh-Hant": "Chino Tradicional",
    "ar": "Árabe",
    "ru": "Ruso",
    "hi": "Hindi",
    "nl": "Holandés",
    "pl": "Polaco",
    "tr": "Turco",
    "sv": "Sueco",
    "da": "Danés",
    "fi": "Finlandés",
    "nb": "Noruego",
    "uk": "Ucraniano",
    "cs": "Checo",
    "ro": "Rumano",
    "hu": "Húngaro",
    "id": "Indonesio",
    "th": "Tailandés",
    "vi": "Vietnamita",
}

CARPETA_BASE = Path("transcripts")


def extraer_video_id(url_o_id: str) -> str:
    """Extrae el video ID de una URL de YouTube o lo devuelve si ya es un ID."""
    patrones = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for patron in patrones:
        match = re.search(patron, url_o_id)
        if match:
            return match.group(1)
    # Si tiene 11 caracteres, asumir que es un ID directo
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url_o_id.strip()):
        return url_o_id.strip()
    raise ValueError(f"No se pudo extraer el video ID de: {url_o_id}")


def obtener_titulo_video(video_id: str) -> str:
    """Intenta obtener el título del video usando yt-dlp."""
    try:
        import yt_dlp
        opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            return info.get("title", video_id)
    except Exception:
        return video_id


def nombre_archivo_seguro(nombre: str) -> str:
    """Convierte un string en un nombre de archivo seguro."""
    nombre = re.sub(r'[<>:"/\\|?*]', "_", nombre)
    nombre = nombre.strip(". ")
    return nombre[:100] if len(nombre) > 100 else nombre


def formatear_transcript(transcript_data, con_timestamps: bool = False) -> str:
    """Formatea los datos del transcript en texto limpio."""
    lineas = []
    for entrada in transcript_data:
        # Soporta tanto objetos (nueva API) como dicts (API antigua)
        texto = (entrada.text if hasattr(entrada, "text") else entrada["text"]).strip()
        inicio = entrada.start if hasattr(entrada, "start") else entrada["start"]
        if not texto:
            continue
        if con_timestamps:
            segundos = int(inicio)
            minutos, segs = divmod(segundos, 60)
            horas, minutos = divmod(minutos, 60)
            if horas > 0:
                ts = f"[{horas:02d}:{minutos:02d}:{segs:02d}]"
            else:
                ts = f"[{minutos:02d}:{segs:02d}]"
            lineas.append(f"{ts} {texto}")
        else:
            lineas.append(texto)
    return "\n".join(lineas)


def descargar_transcript(video_id: str, idiomas: list = None, con_timestamps: bool = False) -> dict:
    """
    Descarga el transcript de un video.
    Retorna dict con {idioma: texto} para cada transcript disponible.
    """
    resultados = {}
    api = YouTubeTranscriptApi()

    try:
        lista_transcripts = api.list(video_id)

        if idiomas:
            for idioma in idiomas:
                try:
                    t = lista_transcripts.find_transcript([idioma])
                    datos = t.fetch()
                    resultados[t.language_code] = {
                        "texto": formatear_transcript(datos, con_timestamps),
                        "nombre_idioma": t.language,
                        "es_generado": t.is_generated,
                    }
                    print(f"  [OK]Transcript en {t.language} ({t.language_code})")
                except NoTranscriptFound:
                    try:
                        t = lista_transcripts.find_generated_transcript([idioma])
                        datos = t.fetch()
                        resultados[t.language_code] = {
                            "texto": formatear_transcript(datos, con_timestamps),
                            "nombre_idioma": t.language,
                            "es_generado": True,
                        }
                        print(f"  [OK]Transcript generado en {t.language} ({t.language_code})")
                    except Exception:
                        print(f"  [X]No hay transcript en: {idioma}")
        else:
            for t in lista_transcripts:
                try:
                    datos = t.fetch()
                    resultados[t.language_code] = {
                        "texto": formatear_transcript(datos, con_timestamps),
                        "nombre_idioma": t.language,
                        "es_generado": t.is_generated,
                    }
                    tipo = "generado" if t.is_generated else "manual"
                    print(f"  [OK]Transcript en {t.language} ({t.language_code}) [{tipo}]")
                except Exception as e:
                    print(f"  [X]Error en {t.language_code}: {e}")

    except TranscriptsDisabled:
        print(f"  [X]Los transcripts están deshabilitados para este video.")
    except Exception as e:
        print(f"  [X]Error al obtener transcripts: {e}")

    return resultados


def guardar_transcripts(video_id: str, titulo: str, transcripts: dict, carpeta_base: Path):
    """Guarda los transcripts en carpetas por idioma."""
    titulo_seguro = nombre_archivo_seguro(titulo)
    fecha = datetime.now().strftime("%Y%m%d")
    archivos_guardados = []

    for codigo_idioma, datos in transcripts.items():
        # Nombre de carpeta: código de idioma + nombre en español si lo conocemos
        nombre_idioma = IDIOMAS_NOMBRES.get(codigo_idioma, datos["nombre_idioma"])
        nombre_carpeta = f"{codigo_idioma} - {nombre_idioma}"
        carpeta_idioma = carpeta_base / nombre_carpeta
        carpeta_idioma.mkdir(parents=True, exist_ok=True)

        # Nombre del archivo
        tipo = "auto" if datos["es_generado"] else "manual"
        nombre_archivo = f"{fecha}_{titulo_seguro}_{video_id}_{tipo}.txt"
        ruta_archivo = carpeta_idioma / nombre_archivo

        # Encabezado del archivo
        encabezado = (
            f"TRANSCRIPT DE YOUTUBE\n"
            f"{'='*60}\n"
            f"Título:    {titulo}\n"
            f"Video ID:  {video_id}\n"
            f"URL:       https://www.youtube.com/watch?v={video_id}\n"
            f"Idioma:    {datos['nombre_idioma']} ({codigo_idioma})\n"
            f"Tipo:      {'Generado automáticamente' if datos['es_generado'] else 'Subtítulos manuales'}\n"
            f"Descargado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{'='*60}\n\n"
        )

        contenido = encabezado + datos["texto"]
        ruta_archivo.write_text(contenido, encoding="utf-8")
        archivos_guardados.append(str(ruta_archivo))
        print(f"  Guardado: {ruta_archivo}")

    return archivos_guardados


def listar_idiomas_disponibles(video_id: str):
    """Muestra los idiomas disponibles para un video."""
    print(f"\nIdiomas disponibles para {video_id}:")
    print("-" * 50)
    api = YouTubeTranscriptApi()
    try:
        lista = api.list(video_id)
        manuales = [t for t in lista if not t.is_generated]
        generados = [t for t in lista if t.is_generated]
        if manuales:
            print("\nTranscripts MANUALES:")
            for t in manuales:
                print(f"  [{t.language_code}] {t.language}")
        if generados:
            print("\nTranscripts GENERADOS AUTOMÁTICAMENTE:")
            for t in generados:
                print(f"  [{t.language_code}] {t.language}")
    except Exception as e:
        print(f"Error: {e}")


def procesar_videos(urls: list, idiomas: list = None, con_timestamps: bool = False, solo_listar: bool = False):
    """Procesa una lista de videos."""
    carpeta_base = Path.cwd() / CARPETA_BASE
    carpeta_base.mkdir(exist_ok=True)

    exitosos = 0
    fallidos = 0

    for url in urls:
        url = url.strip()
        if not url:
            continue

        print(f"\n{'='*60}")
        print(f"Video: {url}")

        try:
            video_id = extraer_video_id(url)
        except ValueError as e:
            print(f"✗ {e}")
            fallidos += 1
            continue

        if solo_listar:
            listar_idiomas_disponibles(video_id)
            continue

        print(f"ID: {video_id}")
        print("Obteniendo título...")
        titulo = obtener_titulo_video(video_id)
        print(f"Título: {titulo}")
        print("Descargando transcripts...")

        transcripts = descargar_transcript(video_id, idiomas, con_timestamps)

        if transcripts:
            guardar_transcripts(video_id, titulo, transcripts, carpeta_base)
            exitosos += 1
        else:
            print("✗ No se encontraron transcripts.")
            fallidos += 1

    if not solo_listar:
        print(f"\n{'='*60}")
        print(f"Completado: {exitosos} exitosos, {fallidos} fallidos")
        print(f"Carpeta de salida: {carpeta_base.resolve()}")


def main():
    parser = argparse.ArgumentParser(
        description="Descarga transcripts de videos de YouTube organizados por idioma.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python youtube_transcripts.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
  python youtube_transcripts.py dQw4w9WgXcQ --idiomas es en
  python youtube_transcripts.py --file mis_videos.txt --idiomas es
  python youtube_transcripts.py dQw4w9WgXcQ --timestamps
  python youtube_transcripts.py --lista-idiomas dQw4w9WgXcQ
        """,
    )

    parser.add_argument(
        "urls",
        nargs="*",
        help="URLs o IDs de videos de YouTube",
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Archivo .txt con una URL/ID por línea",
    )
    parser.add_argument(
        "--idiomas", "-i",
        nargs="+",
        help="Idiomas a descargar (ej: es en pt). Sin este flag descarga todos.",
        metavar="CODIGO",
    )
    parser.add_argument(
        "--timestamps", "-t",
        action="store_true",
        help="Incluir marcas de tiempo en el texto",
    )
    parser.add_argument(
        "--lista-idiomas", "-l",
        action="store_true",
        help="Solo listar idiomas disponibles sin descargar",
    )

    args = parser.parse_args()

    # Recolectar todos los videos
    videos = list(args.urls)

    if args.file:
        archivo = Path(args.file)
        if not archivo.exists():
            print(f"Error: no se encontró el archivo {args.file}")
            sys.exit(1)
        videos += archivo.read_text(encoding="utf-8").splitlines()

    if not videos:
        parser.print_help()
        print("\nEjemplo rápido:")
        print("  python youtube_transcripts.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        sys.exit(0)

    procesar_videos(
        urls=videos,
        idiomas=args.idiomas,
        con_timestamps=args.timestamps,
        solo_listar=args.lista_idiomas,
    )


if __name__ == "__main__":
    main()
