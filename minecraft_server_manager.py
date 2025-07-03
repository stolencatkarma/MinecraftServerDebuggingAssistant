import sys
import subprocess
import os
import threading
import time
import psutil
import json
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QFileDialog, QMessageBox,
                              QGroupBox, QCheckBox)
from PySide6.QtCore import Qt, QTimer, Signal


# Qt6 version
class MinecraftServerManager(QWidget):
    output_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.server_process = None
        self.settings_file = "settings.json"
        self.server_jar_file = ""
        self.java_path = "java"
        self.min_ram = "1G"
        self.max_ram = "4G"
        self.extra_args = "-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200"
        self.nogui = True
        self.init_ui()
        self.monitor_thread = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_buttons)
        self.timer.start(1000)
        self.output_signal.connect(self._append_output_gui)
        self.load_settings()

    def init_ui(self):
        self.setWindowTitle("Minecraft Server Manager")
        # Set default window size
        self.resize(800, 600)
        main_layout = QVBoxLayout()
        self.setup_ui(main_layout)
        self.setLayout(main_layout)
        self.update_buttons()
    
    def setup_ui(self, main_layout):
        # Title
        title = QLabel("Minecraft Server Control Panel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title)
        
        # Server JAR file selection
        jar_layout = QHBoxLayout()
        jar_label = QLabel("Server JAR File:")
        self.jar_input = QLineEdit()
        self.jar_input.setReadOnly(True)
        browse_jar_btn = QPushButton("Browse")
        browse_jar_btn.clicked.connect(self.browse_jar_file)
        jar_layout.addWidget(jar_label)
        jar_layout.addWidget(self.jar_input)
        jar_layout.addWidget(browse_jar_btn)
        main_layout.addLayout(jar_layout)
        
        # Java settings
        java_settings = QGroupBox("Java Settings")
        java_layout = QVBoxLayout()
        
        # Java path
        java_path_layout = QHBoxLayout()
        java_path_label = QLabel("Java Path:")
        self.java_path_input = QLineEdit(self.java_path)
        java_path_layout.addWidget(java_path_label)
        java_path_layout.addWidget(self.java_path_input)
        java_layout.addLayout(java_path_layout)
        
        # Memory settings
        memory_layout = QHBoxLayout()
        min_ram_label = QLabel("Min RAM:")
        self.min_ram_input = QLineEdit(self.min_ram)
        max_ram_label = QLabel("Max RAM:")
        self.max_ram_input = QLineEdit(self.max_ram)
        memory_layout.addWidget(min_ram_label)
        memory_layout.addWidget(self.min_ram_input)
        memory_layout.addWidget(max_ram_label)
        memory_layout.addWidget(self.max_ram_input)
        java_layout.addLayout(memory_layout)
        
        # Extra arguments
        args_layout = QHBoxLayout()
        args_label = QLabel("Extra JVM Args:")
        self.args_input = QLineEdit(self.extra_args)
        args_layout.addWidget(args_label)
        args_layout.addWidget(self.args_input)
        java_layout.addLayout(args_layout)
        
        # GUI option
        gui_layout = QHBoxLayout()
        self.nogui_checkbox = QCheckBox("Run with --nogui")
        self.nogui_checkbox.setChecked(self.nogui)
        gui_layout.addWidget(self.nogui_checkbox)
        java_layout.addLayout(gui_layout)
        
        java_settings.setLayout(java_layout)
        main_layout.addWidget(java_settings)

        # Server status
        status_layout = QHBoxLayout()
        status_label = QLabel("Server Status:")
        self.status_value = QLabel("Stopped")
        self.status_value.setStyleSheet("color: red;")
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_value)
        main_layout.addLayout(status_layout)

        # Control buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Server")
        self.stop_btn = QPushButton("Stop Server")
        self.restart_btn = QPushButton("Restart Server")
        self.check_btn = QPushButton("Check Status")
        self.start_btn.clicked.connect(self.start_server)
        self.stop_btn.clicked.connect(self.stop_server)
        self.restart_btn.clicked.connect(self.restart_server)
        self.check_btn.clicked.connect(self.check_status)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.restart_btn)
        btn_layout.addWidget(self.check_btn)
        main_layout.addLayout(btn_layout)

        # Output area
        output_label = QLabel("Server Output:")
        main_layout.addWidget(output_label)
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        main_layout.addWidget(self.output_area)
        
        # Command input
        cmd_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Type server command here...")
        self.cmd_input.returnPressed.connect(self.send_command_from_input)
        send_cmd_btn = QPushButton("Send")
        send_cmd_btn.clicked.connect(self.send_command_from_input)
        cmd_layout.addWidget(self.cmd_input)
        cmd_layout.addWidget(send_cmd_btn)
        main_layout.addLayout(cmd_layout)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        clear_btn = QPushButton("Clear Output")
        exit_btn = QPushButton("Exit")
        clear_btn.clicked.connect(self.clear_output)
        exit_btn.clicked.connect(self.close)
        bottom_layout.addWidget(clear_btn)
        bottom_layout.addWidget(exit_btn)
        main_layout.addLayout(bottom_layout)

    def closeEvent(self, event):
        """Override close event to save settings before exiting."""
        self.save_settings()
        event.accept()

    def load_settings(self):
        """Load settings from the settings file."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.server_jar_file = settings.get("server_jar_file", "")
                    self.java_path = settings.get("java_path", "java")
                    self.min_ram = settings.get("min_ram", "1G")
                    self.max_ram = settings.get("max_ram", "4G")
                    self.extra_args = settings.get("extra_args", "-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200")
                    self.nogui = settings.get("nogui", True)

                    # Update UI elements with loaded settings
                    self.jar_input.setText(self.server_jar_file)
                    self.java_path_input.setText(self.java_path)
                    self.min_ram_input.setText(self.min_ram)
                    self.max_ram_input.setText(self.max_ram)
                    self.args_input.setText(self.extra_args)
                    self.nogui_checkbox.setChecked(self.nogui)
                    self.log_output("Settings loaded.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.log_output(f"Could not load settings: {e}")

    def save_settings(self):
        """Save current settings to the settings file."""
        settings = {
            "server_jar_file": self.jar_input.text(),
            "java_path": self.java_path_input.text(),
            "min_ram": self.min_ram_input.text(),
            "max_ram": self.max_ram_input.text(),
            "extra_args": self.args_input.text(),
            "nogui": self.nogui_checkbox.isChecked()
        }
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            self.log_output("Settings saved.")
        except IOError as e:
            self.log_output(f"Error saving settings: {e}")

    def is_server_running(self):
        if self.server_process is None:
            return False
        try:
            return self.server_process.poll() is None
        except Exception:
            return False

    def update_status(self, status_text, color):
        self.status_value.setText(status_text)
        self.status_value.setStyleSheet(f"color: {color};")

    def update_buttons(self):
        is_running = self.is_server_running()
        jar_file_selected = bool(self.server_jar_file and os.path.exists(self.server_jar_file))
        self.start_btn.setEnabled(not is_running and jar_file_selected)
        self.stop_btn.setEnabled(is_running)
        self.restart_btn.setEnabled(jar_file_selected)
        
        # Disable configuration fields while the server is running
        self.java_path_input.setEnabled(not is_running)
        self.min_ram_input.setEnabled(not is_running)
        self.max_ram_input.setEnabled(not is_running)
        self.args_input.setEnabled(not is_running)
        self.nogui_checkbox.setEnabled(not is_running)
        
        # Enable/disable command input based on server status
        if hasattr(self, 'cmd_input'):
            self.cmd_input.setEnabled(is_running)

    def log_output(self, message):
        # Use the same append_output method for consistent output handling
        self.append_output(message)

    def browse_jar_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("JAR Files (*.jar)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.server_jar_file = selected_files[0]
                self.jar_input.setText(self.server_jar_file)
                self.log_output(f"Selected server JAR: {self.server_jar_file}")
                self.save_settings()
        self.update_buttons()

    def start_server(self):
        if not self.server_jar_file or not os.path.exists(self.server_jar_file):
            QMessageBox.critical(self, "Error", "Please select a valid JAR file first!")
            return
        if self.is_server_running():
            self.log_output("Server is already running!")
            return
        try:
            # Clear output before starting
            self.clear_output()
            
            # Get settings from UI
            self.java_path = self.java_path_input.text().strip()
            self.min_ram = self.min_ram_input.text().strip()
            self.max_ram = self.max_ram_input.text().strip()
            self.extra_args = self.args_input.text().strip()
            self.nogui = self.nogui_checkbox.isChecked()
            
            # Save settings on start
            self.save_settings()
            
            # Build the command
            server_dir = os.path.dirname(self.server_jar_file)
            jar_filename = os.path.basename(self.server_jar_file)
            command = [
                self.java_path,
                f"-Xms{self.min_ram}",
                f"-Xmx{self.max_ram}"
            ]
            
            # Add extra args if specified
            if self.extra_args:
                command.extend(self.extra_args.split())
                
            # Add jar and nogui if needed
            command.extend(["-jar", jar_filename])
            if self.nogui:
                command.append("--nogui")
                
            self.log_output(f"Command: {' '.join(command)}")
            
            # CRITICAL FIX: Use specific settings known to work reliably with Minecraft servers
            # Set working directory explicitly - required for Minecraft server to find its files
            os.chdir(server_dir)
            
            # Start the server process with settings for reliable output capture
            self.server_process = subprocess.Popen(
                command,
                cwd=server_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,                # More reliable than universal_newlines
                bufsize=1,                # Line buffered for immediate feedback
                shell=False,
                # Don't create a window on Windows
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            self.log_output(f"Starting server: {self.server_jar_file}")
            self.update_status("Starting...", "orange")
            self.monitor_thread = threading.Thread(target=self.monitor_server, daemon=True)
            self.monitor_thread.start()
            self.output_thread = threading.Thread(target=self.read_server_output, daemon=True)
            self.output_thread.start()
        except Exception as e:
            self.log_output(f"Error starting server: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to start server: {str(e)}")
    def read_server_output(self):
        try:
            # Add a debug message to verify the thread is running
            self.append_output("*** Server output thread started ***")
            
            if self.server_process and self.server_process.stdout:
                # Simplified loop for more reliable output capture
                for line in iter(self.server_process.stdout.readline, ''):
                    if not self.is_server_running():
                        break
                        
                    # Only process non-empty lines
                    line = line.rstrip()
                    if line:
                        self.append_output(line)
                    
                    # Let other threads run
                    time.sleep(0.01)
                        
            self.append_output("*** Server output thread ended ***")
        except Exception as e:
            self.append_output(f"[ERROR] Output thread crashed: {e}")
            # Try to restart the output thread if it crashes
            if self.is_server_running():
                time.sleep(1)
                thread = threading.Thread(target=self.read_server_output, daemon=True)
                thread.start()

    def append_output(self, text):
        # Print to terminal console as well as GUI
        print(text)
        self.output_signal.emit(text)

    def _append_output_gui(self, text):
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {text}"
        self.output_area.blockSignals(True)
        self.output_area.append(formatted_message)
        self.output_area.blockSignals(False)
        self.output_area.ensureCursorVisible()
        scrollbar = self.output_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        QApplication.processEvents()

    def stop_server(self):
        if not self.is_server_running():
            self.log_output("Server is not running!")
            return
        try:
            if self.server_process:
                self.update_status("Stopping...", "orange")
                # Try to gracefully stop the server by sending "stop" command to stdin
                try:
                    self.log_output("Sending 'stop' command to server...")
                    if self.server_process.stdin:
                        self.server_process.stdin.write("stop\n")
                        self.server_process.stdin.flush()
                        
                        # Give it some time to shut down gracefully
                        for _ in range(20):  # Wait up to 10 seconds (20 * 0.5s)
                            if not self.is_server_running():
                                break
                            time.sleep(0.5)
                        
                        # If still running, wait more aggressively
                        if self.is_server_running():
                            try:
                                self.server_process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                raise  # Go to the timeout handler
                
                except (subprocess.TimeoutExpired, BrokenPipeError, Exception) as e:
                    # If graceful stop fails, try to terminate the process
                    self.log_output(f"Graceful stop failed: {str(e)}. Forcing termination...")
                    
                    # Use appropriate termination method based on OS
                    if os.name == 'nt':
                        import signal
                        try:
                            self.server_process.send_signal(signal.CTRL_BREAK_EVENT)
                            time.sleep(2)
                        except:
                            pass
                            
                        if self.is_server_running():
                            self.server_process.terminate()
                    else:
                        self.server_process.terminate()
                    
                    # Final kill if needed
                    try:
                        self.server_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.log_output("Force killing server process...")
                        self.server_process.kill()
                        
            # Make sure we clean up process resources
            if hasattr(self, 'server_process') and self.server_process:
                self.server_process = None
            
            self.log_output("Server stopped")
            self.update_status("Stopped", "red")
            
        except Exception as e:
            self.log_output(f"Error stopping server: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to stop server: {str(e)}")
            # Make sure the server process is cleared even if there was an error
            self.server_process = None

    def restart_server(self):
        self.log_output("Restarting server...")
        if self.is_server_running():
            self.stop_server()
            time.sleep(2)
        self.start_server()

    def monitor_server(self):
        server_running_message_shown = False
        
        while self.server_process and self.is_server_running():
            # Only update status to Running once we've confirmed it's actually running
            # and the message hasn't been shown yet
            if not server_running_message_shown:
                self.update_status("Running", "green")
                self.log_output("Server is now running")
                server_running_message_shown = True
            
            # Check if process is still alive
            time.sleep(1)
        
        # Server has stopped - handle cleanup
        if hasattr(self, 'server_process') and self.server_process:
            exit_code = self.server_process.poll()
            self.update_status("Stopped", "red")
            self.log_output(f"Server process has ended with exit code: {exit_code}")
            
            # Show popup only if server ended unexpectedly (not through the stop button)
            # We need to use QTimer to safely interact with the GUI from a non-GUI thread
            QTimer.singleShot(0, lambda: QMessageBox.warning(self, "Server Ended", 
                f"The Minecraft server process has ended with exit code {exit_code}. Check the output for details."))
            
            # Clear the server process reference
            self.server_process = None

    def check_status(self):
        if self.is_server_running():
            self.log_output("Server is currently running")
            self.update_status("Running", "green")
            
            # Send help command to test console output
            self.send_command("help")
        else:
            self.log_output("Server is not running")
            self.update_status("Stopped", "red")

    def send_command(self, command):
        """Send a command to the running server"""
        if not self.is_server_running():
            self.log_output("Server is not running! Cannot send command.")
            return False
        
        try:
            if self.server_process and self.server_process.stdin:
                self.server_process.stdin.write(f"{command}\n")
                self.server_process.stdin.flush()
                self.log_output(f"Sent command: {command}")
                return True
        except Exception as e:
            self.log_output(f"Error sending command: {e}")
            return False

    def clear_output(self):
        self.output_area.clear()

    def send_command_from_input(self):
        """Send command from the input box to the server"""
        command = self.cmd_input.text().strip()
        if command:
            success = self.send_command(command)
            if success:
                self.cmd_input.clear()  # Clear input box after sending

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MinecraftServerManager()
    window.show()
    sys.exit(app.exec())
