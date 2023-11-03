import subprocess
import time
import os
from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)

# Set the path to your Minecraft server JAR file
MINECRAFT_SERVER_DIR = ""
MINECRAFT_JAR_PATH = "minecraft/server.jar"  # Assuming your server JAR file is in the server directory

# Initialize the Minecraft server process and log file
minecraft_process = None
log_file_path = os.path.join(MINECRAFT_SERVER_DIR, "logs", "latest.log")
# Initialize the Minecraft server process
minecraft_process = None
def get_console_output():
    try:
        with open(log_file_path, 'r') as log_file:
            lines = log_file.readlines()
            return lines[-10:]  # Display the last 10 lines of the log file
    except FileNotFoundError:
        return []
@app.route('/')
def index():
    server_status = get_server_status()
    console_output = get_console_output()
    return render_template('minecraft.html', server_status=server_status, console_output=console_output)

@app.route('/start', methods=['POST'])
def start_server():
    global minecraft_process
    if minecraft_process is None:
        minecraft_process = subprocess.Popen(['java', '-Xmx2G', '-jar', MINECRAFT_JAR_PATH, 'nogui'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return redirect(url_for('index'))
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop_server():
    global minecraft_process
    if minecraft_process is not None:
        minecraft_process.stdin.write('stop\n')
        minecraft_process.stdin.flush()
        minecraft_process.wait()
        minecraft_process = None
    return redirect(url_for('index'))

@app.route('/console', methods=['POST'])
def send_command():
    global minecraft_process
    command = request.form['command'] + '\n'
    if minecraft_process is not None:
        minecraft_process.stdin.write(command)
        minecraft_process.stdin.flush()
    return redirect(url_for('index'))

def get_server_status():
    global minecraft_process
    if minecraft_process is not None and minecraft_process.poll() is None:
        return 'Running'
    return 'Stopped'
@app.route('/console-output')
def get_console_output_ajax():
    console_output = get_console_output()
    return '\n'.join(console_output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
