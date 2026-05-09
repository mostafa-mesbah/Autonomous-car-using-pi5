MISSION_MAP = {
    # Basic movement
    'f': lambda ctrl: ctrl.send_command('f'),   # Move forward
    'b': lambda ctrl: ctrl.send_command('b'),   # Move backward
    's': lambda ctrl: ctrl.send_command('s'),   # Stop
    'rl': lambda ctrl: ctrl.send_command('rl'), # Roll left
    'rr': lambda ctrl: ctrl.send_command('rr'), # Roll right
}