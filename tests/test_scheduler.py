"""Automated tests derived from the ten specified system behaviours."""

import unittest

from timetable.models import Course, Lecturer, Room
from timetable.scheduler import IntelligentTimetableScheduler


SLOTS = ["Mon 09:00", "Mon 11:00", "Tue 09:00", "Fri 09:00"]
CHARLES = "Charles Yeo"
ABDULLAH = "Abdullah Al-Amoodi"


class SchedulerBehaviourTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = IntelligentTimetableScheduler()

    def test_normal_behaviour_successful_schedule(self) -> None:
        """SB01: Independent courses are placed without clashes."""
        rooms = [Room("R-small", 30), Room("R-large", 50)]
        lecturers = [
            Lecturer(CHARLES, ["Mon 09:00", "Mon 11:00"]),
            Lecturer(ABDULLAH, ["Tue 09:00", "Fri 09:00"]),
        ]
        courses = [
            Course("HIT140", CHARLES, 20),
            Course("PRT582", ABDULLAH, 40),
        ]
        result = self.scheduler.schedule(courses, rooms, lecturers, SLOTS)
        self.assertEqual(set(result), {"HIT140", "PRT582"})
        self.assertEqual(result["HIT140"].lecturer_id, CHARLES)
        self.assertEqual(result["PRT582"].lecturer_id, ABDULLAH)
        self.assertNotEqual(
            (result["HIT140"].room_id, result["HIT140"].time_slot),
            (result["PRT582"].room_id, result["PRT582"].time_slot),
        )
        self.assertIn(result["HIT140"].time_slot, lecturers[0].available_slots)
        self.assertIn(result["PRT582"].time_slot, lecturers[1].available_slots)

    def test_room_capacity_exact_fit_and_overflow(self) -> None:
        """SB02 & SB03: Exact capacity is allowed; overflow is rejected."""
        rooms = [Room("Tiny", 15), Room("Exact", 30)]
        lecturers = [Lecturer(CHARLES, ["Mon 09:00"])]
        exact = [Course("HIT140", CHARLES, 30)]
        result = self.scheduler.schedule(exact, rooms, lecturers, ["Mon 09:00"])
        self.assertEqual(result["HIT140"].room_id, "Exact")

        overflow = [Course("PRT582", CHARLES, 50)]
        with self.assertRaises(ValueError):
            self.scheduler.schedule(overflow, rooms, lecturers, ["Mon 09:00"])

    def test_lecturer_availability_constraint(self) -> None:
        """SB04: A course is only placed in the lecturer's available window."""
        rooms = [Room("R1", 40)]
        lecturers = [Lecturer(CHARLES, ["Fri 09:00"])]
        courses = [Course("HIT140", CHARLES, 20)]
        result = self.scheduler.schedule(courses, rooms, lecturers, SLOTS)
        self.assertEqual(result["HIT140"].time_slot, "Fri 09:00")

    def test_room_clash_prevention(self) -> None:
        """SB05: Two courses cannot occupy the same room in the same slot."""
        rooms = [Room("Only", 40)]
        lecturers = [
            Lecturer(CHARLES, ["Mon 09:00"]),
            Lecturer(ABDULLAH, ["Mon 09:00"]),
        ]
        courses = [
            Course("HIT140", CHARLES, 20),
            Course("PRT575", ABDULLAH, 20),
        ]
        with self.assertRaises(ValueError):
            self.scheduler.schedule(courses, rooms, lecturers, ["Mon 09:00"])

    def test_lecturer_clash_prevention(self) -> None:
        """SB06: One lecturer cannot teach two courses in the same slot."""
        rooms = [Room("R1", 40), Room("R2", 40)]
        lecturers = [Lecturer(CHARLES, ["Mon 09:00"])]
        courses = [
            Course("HIT140", CHARLES, 10),
            Course("PRT575", CHARLES, 10),
        ]
        with self.assertRaises(ValueError):
            self.scheduler.schedule(courses, rooms, lecturers, ["Mon 09:00"])

    def test_preferred_time_slots_prioritisation(self) -> None:
        """SB07: Preferred slots are chosen when they are still free."""
        rooms = [Room("R1", 40)]
        lecturers = [
            Lecturer(
                CHARLES,
                ["Mon 09:00", "Mon 11:00"],
                preferred_slots=["Mon 11:00"],
            )
        ]
        courses = [Course("HIT140", CHARLES, 12)]
        result = self.scheduler.schedule(courses, rooms, lecturers, SLOTS)
        self.assertEqual(result["HIT140"].time_slot, "Mon 11:00")

    def test_preferred_slots_fall_back_to_availability(self) -> None:
        """Preferred slots are a soft ranking, not a hard filter."""
        rooms = [Room("R1", 40)]
        lecturers = [
            Lecturer(CHARLES, ["Mon 09:00"], preferred_slots=["Mon 09:00"]),
            Lecturer(
                ABDULLAH,
                ["Mon 09:00", "Mon 11:00"],
                preferred_slots=["Mon 09:00"],
            ),
        ]
        courses = [
            Course("HIT140", CHARLES, 10),
            Course("PRT582", ABDULLAH, 10),
        ]
        result = self.scheduler.schedule(courses, rooms, lecturers, SLOTS)
        self.assertEqual(result["HIT140"].time_slot, "Mon 09:00")
        self.assertEqual(result["PRT582"].time_slot, "Mon 11:00")

    def test_prerequisite_ordering_constraint(self) -> None:
        """SB08: A prerequisite is always scheduled in an earlier slot."""
        rooms = [Room("R1", 40), Room("R2", 40)]
        lecturers = [
            Lecturer(CHARLES, ["Mon 09:00", "Mon 11:00", "Tue 09:00"]),
            Lecturer(ABDULLAH, ["Mon 09:00", "Mon 11:00", "Tue 09:00"]),
        ]
        courses = [
            Course("HIT140", CHARLES, 10),
            Course("PRT582", ABDULLAH, 10, prerequisites=["HIT140"]),
        ]
        result = self.scheduler.schedule(courses, rooms, lecturers, SLOTS)
        earlier = SLOTS.index(result["HIT140"].time_slot)
        later = SLOTS.index(result["PRT582"].time_slot)
        self.assertLess(earlier, later)

    def test_circular_prerequisite_detection(self) -> None:
        """SB09: Cyclic prerequisite graphs are rejected before search."""
        rooms = [Room("R1", 40)]
        lecturers = [
            Lecturer(CHARLES, ["Mon 09:00", "Mon 11:00"]),
            Lecturer(ABDULLAH, ["Mon 09:00", "Mon 11:00"]),
        ]
        courses = [
            Course("HIT140", CHARLES, 10, prerequisites=["PRT575"]),
            Course("PRT575", ABDULLAH, 10, prerequisites=["HIT140"]),
        ]
        with self.assertRaises(ValueError) as ctx:
            self.scheduler.schedule(courses, rooms, lecturers, SLOTS)
        self.assertIn("circular", str(ctx.exception).lower())

    def test_empty_time_slots_validation(self) -> None:
        """SB10: Scheduling with no time slots is rejected."""
        rooms = [Room("R1", 20)]
        lecturers = [Lecturer(CHARLES, ["Mon 09:00"])]
        courses = [Course("HIT140", CHARLES, 10)]
        with self.assertRaises(ValueError):
            self.scheduler.schedule(courses, rooms, lecturers, [])

    def test_unknown_lecturer_is_rejected(self) -> None:
        rooms = [Room("R1", 20)]
        lecturers = [Lecturer(CHARLES, ["Mon 09:00"])]
        courses = [Course("HIT140", "Unknown Lecturer", 10)]
        with self.assertRaises(ValueError):
            self.scheduler.schedule(courses, rooms, lecturers, ["Mon 09:00"])

    def test_unknown_prerequisite_is_rejected(self) -> None:
        rooms = [Room("R1", 20)]
        lecturers = [Lecturer(CHARLES, ["Mon 09:00"])]
        courses = [Course("PRT582", CHARLES, 10, prerequisites=["MISSING101"])]
        with self.assertRaises(ValueError):
            self.scheduler.schedule(courses, rooms, lecturers, ["Mon 09:00"])

    def test_duplicate_and_empty_collections_are_rejected(self) -> None:
        rooms = [Room("R1", 20)]
        lecturers = [Lecturer(CHARLES, ["Mon 09:00"])]
        courses = [Course("HIT140", CHARLES, 10)]
        with self.assertRaises(ValueError):
            self.scheduler.schedule(courses, rooms, lecturers, ["Mon 09:00", "Mon 09:00"])
        with self.assertRaises(ValueError):
            self.scheduler.schedule([], rooms, lecturers, ["Mon 09:00"])
        with self.assertRaises(ValueError):
            self.scheduler.schedule(courses, [], lecturers, ["Mon 09:00"])
        with self.assertRaises(ValueError):
            self.scheduler.schedule(courses, rooms, [], ["Mon 09:00"])
        with self.assertRaises(ValueError):
            self.scheduler.schedule(
                [Course("HIT140", CHARLES, 10), Course("HIT140", CHARLES, 12)],
                rooms,
                lecturers,
                ["Mon 09:00"],
            )
        with self.assertRaises(ValueError):
            self.scheduler.schedule(
                courses,
                [Room("R1", 20), Room("R1", 30)],
                lecturers,
                ["Mon 09:00"],
            )
        with self.assertRaises(ValueError):
            self.scheduler.schedule(
                courses,
                rooms,
                [Lecturer(CHARLES, ["Mon 09:00"]), Lecturer(CHARLES, ["Tue 09:00"])],
                ["Mon 09:00"],
            )

    def test_schedule_is_deterministic(self) -> None:
        rooms = [Room("R1", 30), Room("R2", 50)]
        lecturers = [
            Lecturer(CHARLES, ["Mon 09:00", "Mon 11:00"]),
            Lecturer(ABDULLAH, ["Mon 09:00", "Tue 09:00"]),
        ]
        courses = [
            Course("HIT140", CHARLES, 20),
            Course("PRT582", ABDULLAH, 25),
        ]
        first = self.scheduler.schedule(courses, rooms, lecturers, SLOTS)
        second = self.scheduler.schedule(courses, rooms, lecturers, SLOTS)
        self.assertEqual(first, second)

    def test_unplaced_prerequisite_is_not_satisfied(self) -> None:
        course = Course("PRT582", ABDULLAH, 10, prerequisites=["HIT140"])
        satisfied = self.scheduler._prerequisites_satisfied(
            course,
            "Mon 11:00",
            {},
            {"Mon 09:00": 0, "Mon 11:00": 1},
        )
        self.assertFalse(satisfied)


if __name__ == "__main__":
    unittest.main()
