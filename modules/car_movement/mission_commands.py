MISSION_MAP = {
    # Basic movement
    'f': lambda ctrl: ctrl.send_command('f'),   # Move forward
    'b': lambda ctrl: ctrl.send_command('b'),   # Move backward
    's': lambda ctrl: ctrl.send_command('s'),   # Stop

    # Turning (soft)
    'l': lambda ctrl: ctrl.send_command('l'),   # Turn left
    'r': lambda ctrl: ctrl.send_command('r'),   # Turn right

    # Rolling (pivot)
    'rl': lambda ctrl: ctrl.send_command('rl'), # Roll left
    'rr': lambda ctrl: ctrl.send_command('rr'), # Roll right

    # GPS mode toggle
    'g': lambda ctrl: ctrl.send_command('G'),

    # Speed control
    '+': lambda ctrl: ctrl.adjust_speed(10),    # Increase speed by +10
    '-': lambda ctrl: ctrl.adjust_speed(-10),   # Decrease speed by -10
}
