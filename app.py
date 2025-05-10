from flask import Flask, request, send_file, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp, os, shutil, time
from tqdm import tqdm

client_id = '7aab9b2e83ea49059947132ca381273e'
client_secret = '486735a5873942a19aa50a5d8c3382a4'
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

app = Flask(__name__)

def extraer_playlist_id(link):
    if "playlist" in link:
        return link.split("playlist/")[-1].split("?")[0]
    return None

def obtener_canciones_playlist(playlist_id):
    canciones = []
    offset = 0
    limit = 100
    while True:
        resultado = sp.playlist_tracks(playlist_id, offset=offset, limit=limit)
        canciones.extend(resultado['items'])
        if resultado['next']:
            offset += limit
        else:
            break
    return canciones

def buscar_enlace_youtube(query):
    ydl_opts = {'quiet': True, 'extract_flat': True, 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(f"ytsearch1:{query}", download=False)
        if result and result.get('entries'):
            return result['entries'][0]['url']
    return None

def descargar_audio_youtube(enlace, carpeta):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{carpeta}/%(title)s.%(ext)s',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([enlace])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        link_playlist = request.form.get('playlist')
        carpeta = "descargas"
        playlist_id = extraer_playlist_id(link_playlist)

        if not playlist_id:
            return "❌ Enlace inválido. Intenta de nuevo."

        canciones_data = obtener_canciones_playlist(playlist_id)
        metadatos = []
        for c in canciones_data:
            track = c.get('track')
            if track:
                nombre = track.get('name', '')
                artista = track['artists'][0]['name'] if track.get('artists') else ''
                metadatos.append(f"{nombre} {artista}")

        enlaces = []
        for cancion in tqdm(metadatos):
            enlace = buscar_enlace_youtube(cancion)
            enlaces.append(enlace)

        os.makedirs(carpeta, exist_ok=True)

        for i, enlace in enumerate(enlaces):
            if enlace:
                try:
                    descargar_audio_youtube(enlace, carpeta)
                except Exception as e:
                    print(f"❗ Error al descargar {metadatos[i]}: {e}")

        zip_path = shutil.make_archive(carpeta, 'zip', carpeta)
        return send_file(zip_path, as_attachment=True)

    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head><title>Descargar Playlist</title></head>
        <body>
            <h2>🎵 Pega el enlace de tu playlist de Spotify</h2>
            <form method="post">
                <input name="playlist" style="width: 400px;" required>
                <button type="submit">Descargar canciones</button>
            </form>
        </body>
        </html>
    ''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)