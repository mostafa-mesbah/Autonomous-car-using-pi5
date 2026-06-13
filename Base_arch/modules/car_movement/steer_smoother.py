class SteeringSmoother:
    def __init__(self, max_step=15):
        """
        max_step: maximum change per step (degrees)
        If difference > 20 degrees, send intermediate values one by one
        """
        self.max_step = max_step
        self.last_steer = 104  # start at center
        
    def update(self, desired_steer):
        """
        Returns a list of steering values to send.
        If difference <= 20: returns [desired_steer]
        If difference > 20: returns list of intermediate steps
        """
        diff = desired_steer - self.last_steer
        
        # If difference is small, just return the desired value
        if abs(diff) <= 10:
            self.last_steer = desired_steer
            return [desired_steer]
        
        # Otherwise, generate intermediate steps
        steps = []
        current = self.last_steer
        
        if diff > 0:  # Need to increase
            while current < desired_steer:
                current = min(current + self.max_step, desired_steer)
                steps.append(current)
        else:  # Need to decrease
            while current > desired_steer:
                current = max(current - self.max_step, desired_steer)
                steps.append(current)
        
        self.last_steer = desired_steer
        return steps
