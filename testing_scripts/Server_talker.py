import requests
import time
import random
import json
from datetime import datetime

# Configuration
SERVER_URL = "http://68.183.216.141:5001/"
CLIENT_NAME = "Mesba7 Autonoumous Car33"
DELAY_SECONDS = 5  # Time between temperature readings

def get_temperature():
    """
    Simulate getting temperature from Raspberry Pi sensor
    In a real scenario, this would read from actual GPIO pins or sensor libraries
    """
    # Simulate temperature between 20-40 degrees Celsius
    temperature = round(random.uniform(20.0, 40.0), 1)
    return temperature

def move_forward():
    """
    Function to execute when move_forward command is received
    In a real scenario, this would control GPIO pins or motor drivers
    """
    print("🚗 EXECUTING: Moving forward...")
    # Add your forward movement code here
    pass

def move_backward():
    """
    Function to execute when move_backward command is received
    In a real scenario, this would control GPIO pins or motor drivers
    """
    print("🚗 EXECUTING: Moving backward...")
    # Add your backward movement code here
    pass

def turn_left():
    """
    Function to execute when turn_left command is received
    """
    print("🚗 EXECUTING: Turning left...")
    # Add your left turn code here
    pass

def turn_right():
    """
    Function to execute when turn_right command is received
    """
    print("🚗 EXECUTING: Turning right...")
    # Add your right turn code here
    pass

def stop():
    """
    Function to execute when stop command is received
    """
    print("🚗 EXECUTING: Stopping...")
    # Add your stop code here
    pass

def status_check():
    """
    Function to execute when status_check command is received
    """
    print("🚗 EXECUTING: Status check...")
    print(f"   Client: {CLIENT_NAME}")
    print(f"   Status: Online and operational")
    print(f"   Server: {SERVER_URL}")
    pass

def execute_command(command):
    """
    Execute the appropriate function based on the received command
    """
    command_functions = {
        'move_forward': move_forward,
        'move_backward': move_backward,
        'turn_left': turn_left,
        'turn_right': turn_right,
        'stop': stop,
        'status_check': status_check
    }
    
    if command in command_functions:
        command_functions[command]()
        return True
    else:
        print(f"⚠️  Unknown command received: {command}")
        return False

def check_for_commands():
    """
    Check server for any pending commands for this client
    """
    try:
        response = requests.get(
            f"{SERVER_URL}client/{CLIENT_NAME}",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            messages = data.get('messages', [])
            
            if messages:
                print(f"📨 Received {len(messages)} command(s)")
                for msg in messages:
                    command = msg.get('command')
                    timestamp = msg.get('timestamp')
                    print(f"   Command: {command} (received at {timestamp})")
                    execute_command(command)
                return True
            return False
        else:
            print(f"✗ Failed to check commands. Status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Connection error: Cannot reach server for command check")
        return False
    except requests.exceptions.Timeout:
        print("✗ Timeout error: Server took too long to respond for command check")
        return False
    except Exception as e:
        print(f"✗ Error checking commands: {str(e)}")
        return False

def post_temperature_to_server(temperature):
    """
    Post temperature data to the Flask server
    """
    try:
        message = f"temperature = {temperature}"
        
        payload = {
            "name": CLIENT_NAME,
            "message": message
        }
        
        response = requests.post(
            f"{SERVER_URL}message",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 201:
            print(f"✓ Successfully posted temperature: {temperature}°C")
            return True
        else:
            print(f"✗ Failed to post temperature. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Connection error: Cannot connect to server. Is the Flask app running?")
        return False
    except requests.exceptions.Timeout:
        print("✗ Timeout error: Server took too long to respond")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        return False

def test_server_connection():
    """
    Test if the server is reachable
    """
    try:
        response = requests.get(f"{SERVER_URL}", timeout=5)
        if response.status_code == 200:
            print("✓ Server connection successful")
            return True
        else:
            print(f"✗ Server returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to server: {str(e)}")
        return False

def main():
    """
    Main function that runs the temperature monitoring and command polling loop
    """
    print("="*50)
    print(f"Raspberry Pi Temperature Client with Command Support")
    print(f"Client Name: {CLIENT_NAME}")
    print(f"Server URL: {SERVER_URL}")
    print(f"Update Interval: {DELAY_SECONDS} seconds")
    print("="*50)
    
    # Test server connection first
    if not test_server_connection():
        print("\nPlease start the Flask server first by running:")
        print("python app.py")
        return
    
    print(f"\nStarting temperature monitoring and command polling...")
    print("Features:")
    print("- Temperature monitoring every {DELAY_SECONDS} seconds")
    print("- Command polling for remote control")
    print("- Supported commands: move_forward, move_backward, turn_left, turn_right, stop, status_check")
    print("Press Ctrl+C to stop\n")
    
    try:
        cycle_count = 0
        while True:
            cycle_count += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Check for commands from server
            print(f"[{timestamp}] Cycle {cycle_count}: Checking for commands...")
            check_for_commands()
            
            # Get current temperature
            current_temp = get_temperature()
            print(f"[{timestamp}] Current temperature: {current_temp}°C")
            
            # Post to server
            success = post_temperature_to_server(current_temp)
            
            if not success:
                print("Retrying in next cycle...")
            
            print("-" * 40)
            
            # Wait before next reading            
    except KeyboardInterrupt:
        print("\n\nTemperature monitoring and command polling stopped by user")
        print("Goodbye!")
    except Exception as e:
        print(f"\nUnexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()