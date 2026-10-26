
from datetime import datetime, timedelta
import csv
import math


#CUSTOM EXCEPTIONS

class CarParkFullError(Exception):
    pass


class DuplicateVehicleError(Exception):
    pass


class InvalidExitError(Exception):
    pass


#VEHICLE CLASSES

class Vehicle:
    def __init__(self, plate, owner):
        self.plate = plate
        self.owner = owner

    def __str__(self):
        return f"[{self.__class__.__name__}] {self.plate} ({self.owner})"

    def hourly_rate(self):
        raise NotImplementedError

    def allowed_bays(self):
        raise NotImplementedError


class Car(Vehicle):
    def hourly_rate(self):
        return 4.00

    def allowed_bays(self):
        return ["standard"]


class ElectricCar(Car):
    def hourly_rate(self):
        return super().hourly_rate() * 0.5

    def allowed_bays(self):
        return ["ev", "standard"]


class Motorbike(Vehicle):
    def hourly_rate(self):
        return 1.50

    def allowed_bays(self):
        return ["small", "standard"]


class Truck(Vehicle):
    def hourly_rate(self):
        return 9.00

    def allowed_bays(self):
        return ["large"]


#TICKET CLASS

class Ticket:
    def __init__(self, vehicle, bay, entry_time, exit_time=None):
        self.vehicle = vehicle
        self.bay = bay
        self.entry_time = entry_time
        self.exit_time = exit_time

    def calculate_fee(self):
        if self.exit_time is None:
            raise InvalidExitError("Vehicle has not exited.")

        duration = (
            self.exit_time - self.entry_time
        ).total_seconds() / 3600

        if duration < 0:
            raise InvalidExitError("Exit precedes entry.")

        # Rule 1: Grace period, 15 minutes or less
        if duration <= 0.25:
            return 0.00

        # Rule 2: Overnight flat fee, except trucks
        next_day = self.entry_time.date() + timedelta(days=1)

        if (
            not isinstance(self.vehicle, Truck)
            and self.entry_time.hour >= 18
            and self.exit_time.date() == next_day
            and self.exit_time.hour < 7
        ):
            return 12.00

        # Rule 3: Each started hour counts as a full hour
        hours = math.ceil(duration)
        hourly_fee = hours * self.vehicle.hourly_rate()

        # Rule 4: Maximum 8 hourly rates per started 24 hours
        periods = math.ceil(duration / 24)
        daily_cap = periods * 8 * self.vehicle.hourly_rate()
        fee = min(hourly_fee, daily_cap)

        # Rule 5: Weekend surcharge based on entry day
        if self.entry_time.weekday() in (5, 6):
            fee *= 1.25

        return round(fee, 2)


#CAR PARK CLASS

class CarPark:
    def __init__(self, name, capacity):
        self.name = name
        self.capacity = capacity
        self.active_tickets = {}
        self.history = []
        self.revenue = 0.0

    def enter(self, vehicle, entry_time):
        plate = vehicle.plate

        # Check for duplicate active vehicles
        if plate in self.active_tickets:
            raise DuplicateVehicleError(
                f"{plate} is already parked."
            )

        # Find the first available allowed bay
        for bay in vehicle.allowed_bays():
            occupied = sum(
                1 for ticket in self.active_tickets.values()
                if ticket.bay == bay
            )

            if occupied < self.capacity.get(bay, 0):
                ticket = Ticket(vehicle, bay, entry_time)
                self.active_tickets[plate] = ticket
                return ticket

        raise CarParkFullError(
            f"No suitable bay available for {plate}."
        )

    def exit(self, plate, exit_time):
        if plate not in self.active_tickets:
            raise InvalidExitError(
                f"No active ticket for {plate}."
            )

        ticket = self.active_tickets[plate]
        ticket.exit_time = exit_time
        fee = ticket.calculate_fee()

        del self.active_tickets[plate]

        self.history.append(ticket)
        self.revenue += fee

        return fee

    def save_history(self, filename):
        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)

            writer.writerow([
                "plate", "owner", "vehicle_type",
                "bay", "entry", "exit", "fee"
            ])

            for ticket in self.history:
                writer.writerow([
                    ticket.vehicle.plate,
                    ticket.vehicle.owner,
                    type(ticket.vehicle).__name__,
                    ticket.bay,
                    ticket.entry_time.isoformat(),
                    ticket.exit_time.isoformat(),
                    f"{ticket.calculate_fee():.2f}"
                ])

    def load_history(self, filename):
        vehicle_types = {
            "Car": Car,
            "ElectricCar": ElectricCar,
            "Motorbike": Motorbike,
            "Truck": Truck
        }

        loaded = []
        total_revenue = 0.0

        with open(filename, "r", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                vehicle_class = vehicle_types[row["vehicle_type"]]

                vehicle = vehicle_class(
                    row["plate"],
                    row["owner"]
                )

                ticket = Ticket(
                    vehicle,
                    row["bay"],
                    datetime.fromisoformat(row["entry"]),
                    datetime.fromisoformat(row["exit"])
                )

                loaded.append(ticket)
                total_revenue += float(row["fee"])

        self.history = loaded
        self.revenue = total_revenue

    def top_customers(self, n):
        totals = {}

        for ticket in self.history:
            owner = ticket.vehicle.owner
            fee = ticket.calculate_fee()
            totals[owner] = totals.get(owner, 0.0) + fee

        ranked = sorted(
            totals.items(),
            key=lambda item: item[1],
            reverse=True
        )

        return ranked[:n]


#MAIN SCRIPT

if __name__ == "__main__":

    # REQUIREMENT 1: Create the car park
    park = CarPark(
        "Main Car Park",
        {
            "standard": 3,
            "ev": 1,
            "small": 1,
            "large": 1
        }
    )

    print("1. CAR PARK CREATED")
    print(park.name)
    print(park.capacity)

    # REQUIREMENT 2: Demonstrate all five fee rules
    examples = [
        (
            "Grace period",
            Car("A1", "Alice"),
            datetime(2026, 10, 26, 10, 0),
            datetime(2026, 10, 26, 10, 15)
        ),
        (
            "Overnight",
            Car("A2", "Bob"),
            datetime(2026, 10, 26, 19, 0),
            datetime(2026, 10, 27, 6, 0)
        ),
        (
            "Hourly fee",
            Car("A3", "Charlie"),
            datetime(2026, 10, 26, 10, 0),
            datetime(2026, 10, 26, 12, 10)
        ),
        (
            "Daily cap",
            Car("A4", "David"),
            datetime(2026, 10, 26, 8, 0),
            datetime(2026, 10, 27, 9, 0)
        ),
        (
            "Weekend surcharge",
            Car("A5", "Eva"),
            datetime(2026, 10, 31, 10, 0),
            datetime(2026, 10, 31, 12, 0)
        )
    ]

    print("\n2. PARKING FEE RULES")

    for rule, vehicle, entry, exit_time in examples:
        ticket = Ticket(vehicle, "standard", entry, exit_time)
        fee = ticket.calculate_fee()
        print(f"{rule}: {vehicle} -> ${fee:.2f}")

    # REQUIREMENT 3: Park two motorbikes
    print("\n3. MOTORBIKE BAY ALLOCATION")

    now = datetime(2026, 10, 26, 9, 0)

    bike1 = Motorbike("B1", "John")
    bike2 = Motorbike("B2", "Mary")

    ticket1 = park.enter(bike1, now)
    ticket2 = park.enter(bike2, now)

    print(f"Bike 1: {ticket1.bay}")
    print(f"Bike 2: {ticket2.bay}")

    # REQUIREMENT 4: Catch all three custom exceptions
    print("\n4. CUSTOM EXCEPTIONS")

    # Duplicate vehicle
    try:
        park.enter(bike1, now)
    except DuplicateVehicleError as error:
        print("DuplicateVehicleError caught:", error)

    # Fill the large bay, then try another truck
    try:
        park.enter(Truck("T1", "Tom"), now)
        park.enter(Truck("T2", "Jerry"), now)
    except CarParkFullError as error:
        print("CarParkFullError caught:", error)

    # Exit a vehicle that is not parked
    try:
        park.exit("UNKNOWN", now + timedelta(hours=1))
    except InvalidExitError as error:
        print("InvalidExitError caught:", error)

    # Complete the two motorbike tickets
    print("\nCOMPLETED PARKING")

    for plate in ("B1", "B2"):
        fee = park.exit(
            plate,
            now + timedelta(hours=2)
        )
        print(f"{plate}: ${fee:.2f}")

    # REQUIREMENT 5: Save history, reload and rank customers
    print("\n5. CSV HISTORY AND TOP CUSTOMERS")

    park.save_history("history.csv")
    print("History saved to history.csv")

    new_park = CarPark(
        "New Car Park",
        {
            "standard": 3,
            "ev": 1,
            "small": 1,
            "large": 1
        }
    )

    new_park.load_history("history.csv")
    print("History loaded into a new car park.")

    print("Top two customers:")

    for owner, amount in new_park.top_customers(2):
        print(f"{owner}: ${amount:.2f}")

    print(f"Total revenue: ${new_park.revenue:.2f}")
