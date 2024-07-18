from flask import Flask, render_template, request, jsonify
import os
import psutil
import subprocess
import threading
import time
import datetime
import subprocess
import time
import os
import ngrok
from flask import Flask, render_template, request, redirect, url_for
ngrok.set_auth_token("")
websites = (
    "bigtopia.suorsa.se",
    "google.com",
    "facebook.com",
    "1.1.1.1",
    "suorsa.se",
    "amazon.com",
    "microsoft.com",
    "apple.com",
    "twitter.com",
    "instagram.com",
    "reddit.com",
    "github.com",
    "stackoverflow.com",
    "wikipedia.org",
    "youtube.com",
    "roblox.com",
    "discord.com",
    "172.16.0.1"
)
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
status_log = []
def process_raw_temperatures(raw_temperatures):
    cleaned_temperatures = []
    adapter_name = None

    for line in raw_temperatures.splitlines():
        line = line.strip()

        if line.startswith("Adapter:"):
            adapter_name = line.split("Adapter:")[1].strip()
        elif line.startswith("temp") and "Virtual device" not in line:
            parts = line.split(":")
            temperature_name = "Temp"
            temperature_value = parts[1].strip()
            cleaned_temperatures.append({'adapter': adapter_name, 'name': temperature_name, 'value': temperature_value})

    return cleaned_temperatures



app = Flask(__name__)
@app.route('/get_usage_data')
def get_usage_data():
    # Get CPU, RAM, and HDD usage data
    cpu_percent = psutil.cpu_percent()
    ram_percent = psutil.virtual_memory().percent
    hdd_percent = psutil.disk_usage('/').percent

    # Return data as JSON
    return jsonify(cpu_percent=cpu_percent, ram_percent=ram_percent, hdd_percent=hdd_percent)
@app.route('/')
def dashboard():
    # Get CPU, RAM, and HDD usage data
    cpu_percent = psutil.cpu_percent()
    ram_percent = psutil.virtual_memory().percent
    hdd_percent = psutil.disk_usage('/').percent

    return render_template('index.html', cpu_percent=cpu_percent, ram_percent=ram_percent, hdd_percent=hdd_percent)
@app.route('/minecraft')
def minecraft():
    server_status = get_server_status()
    console_output = get_console_output()
    tunnel_url = request.args.get('tunnel_url')  # Get the tunnel_url parameter from the request
    
    return render_template('minecraft.html', server_status=server_status, console_output=console_output, tunnel_url=tunnel_url)
@app.route('/start', methods=['POST'])
def start_server():
    global minecraft_process
    tunnel_url = None  # Initialize with None
    
    try:
        if minecraft_process is None:
            minecraft_process = subprocess.Popen(['java', '-Xmx2G', '-jar', MINECRAFT_JAR_PATH, 'nogui'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            tunnel = ngrok.connect(25565, "tcp")
            tunnel_url = tunnel.url()  # Get the tunnel URL
            print(f"Ingress established at {tunnel_url}")
        else:
            print("Minecraft server is already running.")
    except Exception as e:
        print(f"Error starting Minecraft server: {str(e)}")

    return redirect(url_for('minecraft', tunnel_url=tunnel_url))


@app.route('/stop', methods=['POST'])
def stop_server():
    global minecraft_process
    if minecraft_process is not None:
        minecraft_process.stdin.write('stop\n')
        minecraft_process.stdin.flush()
        minecraft_process.wait()
        minecraft_process = None
    return redirect(url_for('minecraft'))

@app.route('/minecraft-console', methods=['POST'])
def send_command():
    global minecraft_process
    command = request.form['command'] + '\n'
    if minecraft_process is not None:
        minecraft_process.stdin.write(command)
        minecraft_process.stdin.flush()
    return redirect(url_for('minecraft'))

def get_server_status():
    global minecraft_process
    if minecraft_process is not None and minecraft_process.poll() is None:
        return 'Running'
    return 'Stopped'
@app.route('/console-output')
def get_console_output_ajax():
    console_output = get_console_output()
    return '\n'.join(console_output)

@app.route('/terminate_process/<int:pid>', methods=['POST'])
def terminate_process(pid):
    try:
        process = psutil.Process(pid)
        process.terminate()
        return "Process terminated successfully."
    except psutil.NoSuchProcess:
        return "Process not found."

@app.route('/processes')
def processes():
    # Get running processes
    processes = [{'name': process.info['name'], 'pid': process.info['pid']} for process in psutil.process_iter(attrs=['name', 'pid'])]
    return render_template('processes.html', processes=processes)

@app.route('/temperatures')
def temperatures():
    # Get temperature information using subprocess
    raw_temperatures = subprocess.check_output(['sensors']).decode('utf-8')
    cleaned_temperatures = process_raw_temperatures(raw_temperatures)
    return render_template('temperatures.html', cleaned_temperatures=cleaned_temperatures)
@app.route('/power', methods=['GET', 'POST'])
def power():
    
    if request.method == 'GET':
        return render_template('power.html')
    if request.method == 'POST':
        password = ""
        if request.form.get('Shutdown') == 'Shutdown':
            print("shutdown")
            # Shutdown the system
            sudo_command = f'echo {password} | sudo -S shutdown -h 5'
            subprocess.run(sudo_command, shell=True)
            return render_template('power.html', message="Shutdown initiated 5 minutes from now")
        
        elif request.form.get('Restart') == 'Restart':
            print("restart")
            # Restart the system
            sudo_command = f'echo {password} | sudo -S reboot -h 5'
            subprocess.run(sudo_command, shell=True)
            return render_template('power.html', message="Restart initiated 5 minutes from now")
        
        elif request.form.get('Sleep') == 'Sleep':
            print("sleep")
            # Put the system to sleep (suspend)
            sudo_command = f'echo {password} | sudo -S systemctl suspend'
            subprocess.run(sudo_command, shell=True)
            return render_template('power.html', message="Sleep initiated")

    
@app.route('/console', methods=['GET', 'POST'])
def console():
    if request.method == 'POST':
        data = request.get_json()
        command = data.get('command', '')
        # Now you can use the command and password variables with sudo
        output = execute_command_with_sudo(command)
        return jsonify({'output': output})
    return render_template('console.html')

def execute_command_with_sudo(command):
    if "sudo" in command:
        # Use the 'echo' command to pass the password to sudo
        # Make sure to handle security implications and validation appropriately
        # This is a simple example and may not be secure for production use
        sudo_command = f"echo 'Masbo124' | sudo -S {command}"
        result = subprocess.run(sudo_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout + result.stderr
        return output
    else:
        return "Error: 'sudo' not found in the command."
def ping_website(website):
    previous_status = None  # Initialize the previous status as None
    while True:
        try:
            # Use os.system to ping the website
            response = os.system(f"ping -c 1 {website}")

            if response == 0:
                current_status = f"{website} is UP"
            else:
                current_status = f"{website} is DOWN"

            # Check if the status has changed
            if current_status != previous_status:
                # Log the status and timestamp
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status_log.append(f"[{timestamp}] {current_status}")
                previous_status = current_status  # Update the previous status
        except Exception as e:
            status = f"Error pinging {website}: {str(e)}"

        # Sleep for 60 seconds before pinging again (adjust as needed)
        time.sleep(60)
        
        
        
@app.route('/ping')
def ping():
    return render_template('status_log.html', status_log=status_log)
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
if __name__ == '__main__':
    for website in websites:
        threading.Thread(target=ping_website, args=(website,), daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)
