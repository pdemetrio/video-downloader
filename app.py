# app.py
from flask import Flask, render_template, request, jsonify, Response
import os
import threading
import time
import yt_dlp
import json

app = Flask(__name__)

# Variáveis globais para monitorar o progresso e o controle do download
download_progress = {}
current_download_thread = None
stop_download = threading.Event()

def my_hook(d):
    if stop_download.is_set():
        raise Exception("Download cancelado pelo usuário")
        
    if d['status'] == 'downloading':
        download_id = d['filename']
        try:
            total = d.get('total_bytes', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                percentage = (downloaded / total) * 100
            else:
                percentage = float(d.get('_percent_str', '0%').replace('%', '').strip())
        except Exception:
            percentage = 0
            
        download_progress[download_id] = {
            'percentage': f"{percentage:.1f}%",
            'speed': d.get('_speed_str', 'N/A'),
            'eta': d.get('_eta_str', 'N/A'),
            'status': 'downloading'
        }
        print(f"Progresso: {download_progress[download_id]}")
    elif d['status'] == 'finished':
        download_id = d['filename']
        download_progress[download_id] = {
            'percentage': '100%',
            'status': 'Concluído'
        }
        print(f"Download concluído: {download_progress[download_id]}")

def get_best_format(formats, quality):
    if quality == 'best':
        return 'bestvideo+bestaudio/best'
    
    target_height = int(quality)
    best_format = None
    min_diff = float('inf')
    
    for f in formats:
        if 'height' in f:
            diff = abs(f['height'] - target_height)
            if diff < min_diff:
                min_diff = diff
                best_format = f['format_id']
    
    return best_format if best_format else 'bestvideo+bestaudio/best'

def download_video(url, platform, video_quality, extract_audio):
    try:
        output_template = os.path.join('downloads', f'%(title)s.%(ext)s')
        
        ydl_opts = {
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        },
            'outtmpl': output_template,
            'format': 'bestvideo+bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'progress_hooks': [my_hook],
        }
        
        if extract_audio:
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            })
        
        if platform == 'youtube':
            with yt_dlp.YoutubeDL() as ydl:
                info = ydl.extract_info(url, download=False)
                ydl_opts['format'] = get_best_format(info['formats'], video_quality)
        else:
            ydl_opts['format'] = 'best'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
    except Exception as e:
        if str(e) == "Download cancelado pelo usuário":
            for key in download_progress:
                download_progress[key] = {
                    'percentage': '0%',
                    'status': 'Cancelado',
                    'speed': '',
                    'eta': ''
                }
        else:
            print(f"Erro ao baixar o vídeo: {e}")
            for key in download_progress:
                download_progress[key] = {
                    'percentage': '0%',
                    'status': 'Erro',
                    'speed': '',
                    'eta': ''
                }

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        platform = request.form['platform']
        video_quality = request.form['video_quality']
        extract_audio = 'extract_audio' in request.form
        
        global download_progress, current_download_thread, stop_download
        download_progress.clear()
        stop_download.clear()
        
        current_download_thread = threading.Thread(
            target=download_video,
            args=(url, platform, video_quality, extract_audio)
        )
        current_download_thread.start()
        
        return jsonify({"status": "started"})
    
    return render_template('index.html')

@app.route('/progress')
def progress():
    def generate():
        while True:
            if download_progress:
                for key, value in download_progress.items():
                    yield f"data: {json.dumps(value)}\n\n"
            if not current_download_thread or not current_download_thread.is_alive():
                break
            time.sleep(0.5)  # Atualiza a cada 0.5 segundos
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/cancel_download', methods=['POST'])
def cancel_download():
    global stop_download
    stop_download.set()
    return jsonify({"status": "canceling"})

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    app.run(debug=True)