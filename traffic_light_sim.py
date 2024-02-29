import math
import random
import enum

### ---- Constants --- ###

# Delays between recurrences (i.e. periods in s)
CAR_DELAY = 1
PEDESTRIAN_DELAY = 2
CYCLIST_DELAY = 10
RT_DELAY = 60 * 4


# Clear times (in s)
CAR_CLEAR = 1
RT_CLEAR = 2
CYCLIST_CLEAR = 5
PEDESTRIAN_CLEAR = 15

# Overlaps (i.e. how many can safely cross the intersection simultaneously)
CAR_OVERLAP = 2
RT_OVERLAP = 1
CYCLIST_OVERLAP = 6
PEDESTRIAN_OVERLAP = 18

# The time to cross the light (from when it turns green until it turns red)
LIGHT_TIME = 30

# --- Enums --- #

class Direction(enum.Enum):
    "The four cardinal directions"
    NORTH, EAST, SOUTH, WEST = range(4)

class LightPhase(enum.Enum):
    """The two phases of the traffic light.
    Each phase permits two of four directions at the intersection to cross."""
    NORTH_SOUTH, EAST_WEST = range(2)

class UserCategory(enum.Enum):
    """The four categories of road users. 
    Cars and cyclists include similar vehicles 
    (e.g. trucks fall under cars, scooters under cyclists)"""
    CAR, RT, CYCLIST, PEDESTRIAN = range(4)

# Add clear time, delay period, and overlaps to each user category

UserCategory.CAR.clear_time = CAR_CLEAR
UserCategory.RT.clear_time = RT_CLEAR
UserCategory.CYCLIST.clear_time = CYCLIST_CLEAR
UserCategory.PEDESTRIAN.clear_time = PEDESTRIAN_CLEAR

UserCategory.CAR.period = CAR_DELAY
UserCategory.RT.period = RT_DELAY
UserCategory.CYCLIST.period = CYCLIST_DELAY
UserCategory.PEDESTRIAN.period = PEDESTRIAN_DELAY

UserCategory.CAR.overlaps = CAR_OVERLAP
UserCategory.RT.overlaps = RT_OVERLAP
UserCategory.CYCLIST.overlaps = CYCLIST_OVERLAP
UserCategory.PEDESTRIAN.overlaps = PEDESTRIAN_OVERLAP


### --- Helper classes --- ###

class User:
    "A road user."
    def __init__(self, category):
        self.category = category
        self.intersection_time = 0
        self.cleared = False

    def wait_time(self):
        "The total time spent waiting to cross the intersection"
        return self.intersection_time - self.category.clear_time


class Lane:
    "A lane in the intersection."
    def __init__(self, category):
        self.category = category # The category of user this lane supports
        self.users = []

    def add(self, user):
        "Add a road user to a lane"
        if user.category != self.category:
            raise ValueError("incompatiable user")
        self.users.append(user)

    def discharge(self):
        "Have the first user cross the intersection, removing them from the lane"
        for user in self.users:
            # This function is called once for every overlap, hence the division by the overlap count
            user.intersection_time += self.category.clear_time / self.category.overlaps
        # 
        if self.users:
            user = self.users.pop(0)
            user.intersection_time = round(user.intersection_time) # Round time for easy analysis
            user.cleared = True

    def hold(self):
        "Add the red-light waiting time to all vehicles"
        for user in self.users:
            user.intersection_time += LIGHT_TIME



class Source:
    """One of the four sources of inbound traffic for an intersection
    lane_lookup: a map mapping user categories to numbers, indicating how
        many lanes for that category of intersection user."""
    def __init__(self, direction, lane_lookup):
        self.direction = direction
        self.lanes = []
        for category, num in lane_lookup.items():
            for i in range(num):
                self.lanes.append(Lane(category))
    
    def add(self, user):
        "Add a user to a source."
        destination = None
        for lane in self.lanes:
            if lane.category is not user.category:
                continue
            if destination is None or len(lane.users) < len(destination.users):
                destination = lane
        if destination is None:
            return False
        destination.add(user)
        return True
    
    def hold(self):
        "Hold are road users in the source."
        for lane in self.lanes:
            lane.hold()

    def discharge(self, category):
        "Discharge one user from each lane."
        for lane in self.lanes:
             if lane.category is category:
                lane.discharge()


class Simulation:
    """A simulation.
    
    direction_lane_lookup: a map mapping direction to lane lookups 
        (see Source for doc about lane lookups)."""
    def __init__(self, stop_time, direction_lane_lookup):
        self.stop_time = stop_time # The stop time (in s)
        self.time = 0 # Current time; starts at zero
        self.users = [] # A list of all users in the simulation
        self.sources = {}
        for direction in Direction:
            self.sources[direction] = Source(direction, direction_lane_lookup[direction])

    def light_session(self, phase):
        "Define the order of events a single occurence of a traffic light phase"
        # Add vehicles. This simulation assumes all vehicles enter at the beginning of the phase.
        for source in self.sources.values():
            for category in UserCategory:
                expected = LIGHT_TIME / category.period
                number_added = 0
                if expected < 0.8:
                    # Ensure rare vehicles are added in proportion
                    if random.random() < expected:
                        number_added = 1
                    else:
                        number_added = 0
                else:
                    number_added = round(expected * 2 * random.random())
                for i in range(number_added):
                    user = User(category)
                    if source.add(user):
                        self.users.append(user)
        if phase == LightPhase.EAST_WEST:
            # Traffic facing red must hold
            for source in (self.sources[Direction.NORTH], self.sources[Direction.SOUTH]):
                source.hold()
            # Traffic facing green is discharged based on intersection availability
            for source in (self.sources[Direction.EAST], self.sources[Direction.WEST]):
                for category in UserCategory:
                    num_cleared = math.floor(LIGHT_TIME * category.overlaps / category.clear_time)
                    for i in range(num_cleared):
                        source.discharge(category)
        else:
            for source in (self.sources[Direction.EAST], self.sources[Direction.WEST]):
                source.hold()
            for source in (self.sources[Direction.NORTH], self.sources[Direction.SOUTH]):
                for category in UserCategory:
                    num_cleared = math.floor(LIGHT_TIME * category.overlaps / category.clear_time)
                    for i in range(num_cleared):
                        source.discharge(category)

    
    def play(self):
        "Define the order of events for all the simulation"
        while self.time < self.stop_time:
            self.time += (2 * LIGHT_TIME)
            self.light_session(LightPhase.NORTH_SOUTH)
            self.light_session(LightPhase.EAST_WEST)

    def category_intersection_times(self, category):
        "Get the intersection time for users of a certain category"
        l = []
        for user in self.users:
            if (not user.cleared) or user.category is not category:
                continue
            l.append(user.intersection_time)
        return l
    
    @staticmethod
    def average(iter):
        "Get the average of an iterable"
        l = list(iter)
        return sum(l) / len(l)

    def run(self):
        "Run the simulation. Return a map mapping user category to intersection times"
        self.play()
        d = {}
        for category in UserCategory:  
            x = self.category_intersection_times(category)
            d[category] = (round(len(x), -3), round(self.average(x)) if x else -1)
        return d
    
if __name__ == '__main__':
    
    runtime = 60 * 60 * 20 # The run time (in seconds)
        
    # 1st option (Standard)
    s1 = Simulation(runtime, {
        Direction.NORTH: {
            UserCategory.CAR: 3,
            UserCategory.PEDESTRIAN: 2
        },
        Direction.SOUTH: {
            UserCategory.CAR: 3,
            UserCategory.PEDESTRIAN: 2
        },
        Direction.EAST: {
            UserCategory.CAR: 3,
            UserCategory.PEDESTRIAN: 1
        },
        Direction.WEST: {
            UserCategory.CAR: 3,
            UserCategory.PEDESTRIAN: 1
        }
    })
    print(s1.run(), end='\n\n')
        
    # 2nd option
    s2 = Simulation(runtime, {
        Direction.NORTH: {
            UserCategory.CAR: 2,
            UserCategory.CYCLIST: 2,
            UserCategory.PEDESTRIAN: 2
        },
        Direction.SOUTH: {
            UserCategory.CAR: 2,
            UserCategory.CYCLIST: 2,
            UserCategory.PEDESTRIAN: 2
        },
        Direction.EAST: {
            UserCategory.CAR: 2,
            UserCategory.CYCLIST: 2,
            UserCategory.PEDESTRIAN: 1
        },
        Direction.WEST: {
            UserCategory.CAR: 2,
            UserCategory.CYCLIST: 2,
            UserCategory.PEDESTRIAN: 1
        }
    })
    print(s2.run(), end='\n\n')

    # 3rd option
    s3 = Simulation(runtime, {
        Direction.NORTH: {
            UserCategory.CAR: 2,
            UserCategory.CYCLIST: 2,
            UserCategory.RT: 1,
            UserCategory.PEDESTRIAN: 1
        },
        Direction.SOUTH: {
            UserCategory.CAR: 2,
            UserCategory.CYCLIST: 2,
            UserCategory.RT: 1,
            UserCategory.PEDESTRIAN: 1
        },
        Direction.EAST: {
            UserCategory.CAR: 2,
            UserCategory.CYCLIST: 2,
            UserCategory.PEDESTRIAN: 1
        },
        Direction.WEST: {
            UserCategory.CAR: 2,
            UserCategory.CYCLIST: 2,
            UserCategory.PEDESTRIAN: 1
        }
    })
    print(s3.run(), end='\n\n')


        
        







