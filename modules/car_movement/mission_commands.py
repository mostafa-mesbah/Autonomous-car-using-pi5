MISSION_MAP = {
    'f': lambda ctrl: ctrl.forward(),
    'b': lambda ctrl: ctrl.backward(),
    'l': lambda ctrl: ctrl.left(),
    'r': lambda ctrl: ctrl.right(),
    's': lambda ctrl: ctrl.stop(),
    '+': lambda ctrl: ctrl.increase_speed(),
    '-': lambda ctrl: ctrl.decrease_speed(),
}
