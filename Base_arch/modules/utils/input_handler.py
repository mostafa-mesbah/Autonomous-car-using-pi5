import queue
import select
import sys
import termios
import threading
import time
import tty

class InputHandler:
    """Handles user input and terminal operations"""
    
    def __init__(self):
        self.original_term_settings = None
        self.input_queue = queue.Queue()
        self.listener_running = False
        self.listener_thread = None
    
    def get_single_key(self, prompt=None):
        """Get a single key press without waiting for Enter"""
        if prompt:
            sys.stdout.write(prompt)
            sys.stdout.flush()
        
        # Set terminal to raw mode temporarily
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        
        # Echo the key pressed and newline
        sys.stdout.write(key + '\n')
        sys.stdout.flush()
        
        return key
    
    def get_user_command_non_blocking(self):
        """Get user command without blocking (for main loop)"""
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.readline().strip().lower()
        return None
    
    def start_input_listener(self):
        """Start background thread to listen for user input"""
        self.listener_running = True
        self.listener_thread = threading.Thread(
            target=self._input_listener_loop,
            daemon=True,name="InputListenerThread"
        )
        self.listener_thread.start()
        print("[InputHandler] Input listener started")
    
    def stop_input_listener(self):
        """Stop the input listener thread"""
        self.listener_running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=1.0)
        print("[InputHandler] Input listener stopped")
    
    def _input_listener_loop(self):
        """Background thread that continuously listens for input"""
        while self.listener_running:
            cmd = self.get_user_command_non_blocking()
            if cmd:
                self.input_queue.put(cmd)
    
    def get_user_input(self, timeout=0.1):
        """Get user input from queue (non-blocking)"""
        try:
            return self.input_queue.get(timeout=timeout)
        except queue.Empty:
            return None