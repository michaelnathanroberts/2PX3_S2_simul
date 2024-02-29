import math
import random
import enum

### ---- Constants --- ###
# Delays between recurrences (periods in s)
CAR_DELAY = 0.6
PEDESTRIAN_DELAY = 2
CYCLIST_DELAY = 10
RT_DELAY = 60 * 4

CAR_CLEAR = 1
RT_CLEAR = 2
CYCLIST_CLEAR = 5
PEDESTRIAN_CLEAR = 15

CAR_OVERLAP = 2
RT_OVERLAP = 1
CYCLIST_OVERLAP = 6
PEDESTRIAN_OVERLAP = 18

LIGHT_TIME = 30

# --- Enums --- #

class Direction(enum.Enum):
    NORTH, EAST, SOUTH, WEST = range(4)

class LightPhase(enum.Enum):
    NORTH_SOUTH, EAST_WEST = range(2)

class UserCategory(enum.Enum):
    CAR, RT, CYCLIST, PEDESTRIAN = range(4)

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
    def __init__(self, category):
        self.category = category
        self.intersection_time = 0
        self.cleared = False

    def wait_time(self):
        return self.intersection_time - self.category.clear_time


class Lane:
    def __init__(self, category):
        self.category = category
        self.users = []

    def add(self, user):
        if user.category != self.category:
            raise ValueError("incompatiable user")
        self.users.append(user)

    def discharge(self):
        for user in self.users:
            user.intersection_time += math.floor(self.category.clear_time / self.category.overlaps)
        if self.users:
            user = self.users.pop(0)
            user.cleared = True

    def hold(self):
        for user in self.users:
            user.intersection_time += LIGHT_TIME



class Source:
    def __init__(self, direction, lane_lookup):
        self.direction = direction
        self.lanes = []
        for category, num in lane_lookup.items():
            for i in range(num):
                self.lanes.append(Lane(category))
    
    def add(self, user):
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
        for lane in self.lanes:
            lane.hold()

    def discharge(self, category):
        for lane in self.lanes:
             if lane.category is category:
                lane.discharge()


class Simulation:
    def __init__(self, stop_time, direction_lane_lookup):
        self.stop_time = stop_time
        self.time = 0
        self.users = []
        self.sources = {}
        for direction in Direction:
            self.sources[direction] = Source(direction, direction_lane_lookup[direction])

    def light_session(self, phase):
        for source in self.sources.values():
            for category in UserCategory:
                expected = LIGHT_TIME / category.period
                number_added = 0
                if expected < 0.8:
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
            for source in (self.sources[Direction.NORTH], self.sources[Direction.SOUTH]):
                source.hold()
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
        while self.time < self.stop_time:
            self.time += (2 * LIGHT_TIME)
            self.light_session(LightPhase.NORTH_SOUTH)
            self.light_session(LightPhase.EAST_WEST)

    def category_intersection_times(self, category):
        l = []
        for user in self.users:
            if (not user.cleared) or user.category is not category:
                continue
            l.append(user.intersection_time)
        return l
    
    @staticmethod
    def average(iter):
        return sum(iter) / len(iter)

    def run(self):
        self.play()
        d = {}
        for category in UserCategory:  
            x = self.category_intersection_times(category)
            d[category] = (round(len(x), -3), round(self.average(x)) if x else -1)
        return d
    
if __name__ == '__main__':
    
    runtime = 12000
        
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


        
        







