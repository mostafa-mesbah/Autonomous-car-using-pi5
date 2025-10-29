MISSION_MAP = {
    # Basic movement
    'f': lambda ctrl: ctrl.send_command('f'),   # Move forward
    'b': lambda ctrl: ctrl.send_command('b'),   # Move backward
    's': lambda ctrl: ctrl.send_command('s'),   # Stop

    # Turning (soft) - default turns
    'l': lambda ctrl: ctrl.send_command('l'),   # Turn left (default speeds)
    'r': lambda ctrl: ctrl.send_command('r'),   # Turn right (default speeds)

    # Rolling (pivot)
    'rl': lambda ctrl: ctrl.send_command('rl'), # Roll left
    'rr': lambda ctrl: ctrl.send_command('rr'), # Roll right

    # GPS mode toggle
    'g': lambda ctrl: ctrl.send_command('g'),

}