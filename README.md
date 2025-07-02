# Minecraft Server Debugging Assistant

A Python PyGUI application for managing Minecraft servers through batch files. This tool provides an easy-to-use graphical interface for starting, stopping, and restarting your Minecraft server.

## Features

- **Start/Stop/Restart Server**: Control your Minecraft server with simple button clicks
- **Batch File Support**: Works with your existing server batch files
- **Real-time Status**: Shows current server status (Running/Stopped)
- **Output Monitoring**: Displays server output and manager logs
- **Process Management**: Safely handles server processes with graceful shutdown
- **User-friendly GUI**: Clean, modern interface using PySimpleGUI

## Requirements

- Python 3.7 or higher
- Windows operating system

## Installation

1. **Run the setup script** to install dependencies:
   ```bash
   setup.bat
   ```

   Or manually install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Launch the application**:
   ```bash
   python minecraft_server_manager.py
   ```
   
   Or use the provided batch file:
   ```bash
   run.bat
   ```

2. **Select your server batch file**:
   - Click "Browse" to select your Minecraft server's batch file
   - The batch file should be the one you normally use to start your server

3. **Control your server**:
   - **Start Server**: Launches your server using the selected batch file
   - **Stop Server**: Safely stops the running server
   - **Restart Server**: Stops and then starts the server
   - **Check Status**: Manually refreshes the server status

4. **Monitor output**:
   - View real-time logs and server status in the output area
   - Clear output when needed using the "Clear Output" button

## Files Structure

```
MinecraftServerDebuggingAssistant/
├── minecraft_server_manager.py    # Main application
├── requirements.txt               # Python dependencies
├── setup.bat                     # Setup script for Windows
├── run.bat                       # Quick launch script
└── README.md                     # This file
```

## Dependencies

- **PySimpleGUI**: For the graphical user interface
- **psutil**: For process management and monitoring

## Notes

- The application will open a new console window when starting your server
- Make sure your server batch file is properly configured and working
- The server status is monitored in real-time
- Closing the application will prompt you to stop the server if it's running

## Troubleshooting

1. **Import errors**: Make sure you've run `setup.bat` to install dependencies
2. **Server won't start**: Verify your batch file path and that it works when run manually
3. **Python not found**: Ensure Python is installed and added to your PATH

## License

This project is open source and available under the MIT License.
