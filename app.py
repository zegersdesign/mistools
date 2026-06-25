from flask import Flask, jsonify, Response, send_file, abort, request
import subprocess, json, os, re, webbrowser, threading

app = Flask(__name__, static_folder='.', static_url_path='')

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')

TOOLS = [
    {
        'id':       'cleaner',
        'name':     'ClaudeCleaner',
        'desc':     'Limpia temp, cache de browsers, prefetch y papelera',
        'icon':     'ti-trash',
        'color':    'purple',
        'category': 'sistema',
        'script':   os.path.join(SCRIPTS, 'ClaudeCleanerWeb.ps1'),
        'ready':    True,
    },
    {
        'id':       'antimalware',
        'name':     'Claude Antimalware',
        'desc':     'Escaneo rapido con Windows Defender integrado',
        'icon':     'ti-shield-check',
        'color':    'teal',
        'category': 'seguridad',
        'script':   os.path.join(SCRIPTS, 'AntimalwareWeb.ps1'),
        'ready':    True,
    },
    {
        'id':       'diskanalyzer',
        'name':     'Disk Analyzer',
        'desc':     'Que esta ocupando espacio en cada disco',
        'icon':     'ti-chart-pie',
        'color':    'amber',
        'category': 'archivos',
        'script':   os.path.join(SCRIPTS, 'DiskAnalyzerWeb.ps1'),
        'ready':    True,
    },
    {
        'id':       'startup',
        'name':     'Startup Manager',
        'desc':     'Ver todo lo que arranca con Windows',
        'icon':     'ti-player-play',
        'color':    'coral',
        'category': 'sistema',
        'script':   os.path.join(SCRIPTS, 'StartupWeb.ps1'),
        'ready':    True,
    },
    {
        'id':       'sysinfo',
        'name':     'System Info',
        'desc':     'CPU, RAM, GPU, discos, red y uptime de un vistazo',
        'icon':     'ti-cpu',
        'color':    'blue',
        'category': 'sistema',
        'script':   os.path.join(SCRIPTS, 'SysInfoWeb.ps1'),
        'ready':    True,
    },
    {
        'id':       'wallpaper',
        'name':     'Wallpaper Downloader',
        'desc':     'Descarga todos los wallpapers de cualquier sitio web',
        'icon':     'ti-photo-down',
        'color':    'green',
        'category': 'web',
        'script':   os.path.join(SCRIPTS, 'WallpaperDownloaderWeb.js'),
        'runner':   'node',
        'ready':    True,
    },
]

ANSI = re.compile(r'\x1b\[[0-9;]*[mGKHF]')

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/tools')
def get_tools():
    return jsonify(TOOLS)

@app.route('/drives')
def get_drives():
    import shutil
    drives = []
    for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
        path = f'{letter}:\\'
        if os.path.exists(path):
            try:
                total, used, free = shutil.disk_usage(path)
                def fmt(b):
                    if b >= 1e9: return f'{b/1e9:.1f} GB'
                    return f'{b/1e6:.0f} MB'
                drives.append({
                    'letter': letter,
                    'total': fmt(total),
                    'used':  fmt(used),
                    'free':  fmt(free),
                    'pct':   round(used / total * 100),
                })
            except: pass
    return jsonify(drives)

@app.route('/run/<tool_id>')
def run_tool(tool_id):
    tool = next((t for t in TOOLS if t['id'] == tool_id), None)
    if not tool:
        abort(404)

    script  = tool.get('script', '')
    ps_args = []
    if tool_id == 'cleaner':
        ps_args = ['-Zones', request.args.get('zones', 'all')]
    elif tool_id == 'antimalware':
        ps_args = ['-ScanType', request.args.get('scantype', 'QuickScan')]
        if request.args.get('custompath'):
            ps_args += ['-CustomPath', request.args.get('custompath')]
    elif tool_id == 'diskanalyzer':
        ps_args = ['-Drive', request.args.get('drive', 'C')]
    elif tool_id == 'startup':
        ps_args = ['-Filter', request.args.get('filter', 'all')]
    elif tool_id == 'sysinfo':
        ps_args = ['-Sections', request.args.get('sections', 'os,cpu,ram,gpu,disk,net,procs')]
    elif tool_id == 'wallpaper':
        ps_args = [request.args.get('url', '')]
        folder = request.args.get('folder', '')
        if folder:
            ps_args.append(folder)

    runner = tool.get('runner', 'powershell')

    def generate():
        try:
            if runner == 'node':
                cmd = ['node', script] + ps_args
            else:
                cmd = ['powershell', '-ExecutionPolicy', 'Bypass',
                       '-NonInteractive', '-File', script] + ps_args
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for raw in proc.stdout:
                line = ANSI.sub('', raw.rstrip())
                if not line:
                    continue
                parts = line.split('|')
                payload = {'type': parts[0], 'parts': parts[1:]}
                yield f"data: {json.dumps(payload)}\n\n"
            proc.wait()
        except Exception as e:
            yield f"data: {json.dumps({'type':'ERROR','parts':[str(e)]})}\n\n"
        finally:
            yield "data: __DONE__\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )

def open_browser():
    webbrowser.open('http://localhost:7777')

if __name__ == '__main__':
    PORT = int(os.environ.get('MISTOOLS_PORT', '7777'))
    if os.environ.get('MISTOOLS_NO_BROWSER') != '1':
        threading.Timer(1.2, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
    print(f"\n  MisTools corriendo en http://localhost:{PORT}")
    print("  Presiona Ctrl+C para detener\n")
    app.run(port=PORT, debug=False, use_reloader=False)
