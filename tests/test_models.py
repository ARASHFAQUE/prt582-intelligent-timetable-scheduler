"""Unit tests for domain-model validation (SB10 and related guards)."""

import unittest

from timetable.models import Course, Lecturer, Room


class RoomValidationTests(unittest.TestCase):
    def test_rejects_zero_or_negative_capacity(self) -> None:
        with self.assertRaises(ValueError):
            Room("R1", 0)
        with self.assertRaises(ValueError):
            Room("R1", -8)

    def test_rejects_empty_room_id(self) -> None:
        with self.assertRaises(ValueError):
            Room("", 20)

    def test_rejects_non_integer_capacity(self) -> None:
        with self.assertRaises(ValueError):
            Room("R1", True)  # type: ignore[arg-type]


class LecturerValidationTests(unittest.TestCase):
    def test_rejects_preferred_slots_outside_availability(self) -> None:
        with self.assertRaises(ValueError):
            Lecturer("Charles Yeo", ["Mon 09:00"], preferred_slots=["Tue 09:00"])

    def test_rejects_empty_availability(self) -> None:
        with self.assertRaises(ValueError):
            Lecturer("Charles Yeo", [])

    def test_rejects_empty_lecturer_id(self) -> None:
        with self.assertRaises(ValueError):
            Lecturer("", ["Mon 09:00"])

    def test_rejects_duplicate_slots(self) -> None:
        with self.assertRaises(ValueError):
            Lecturer("Charles Yeo", ["Mon 09:00", "Mon 09:00"])
        with self.assertRaises(ValueError):
            Lecturer("Charles Yeo", ["Mon 09:00", "Mon 11:00"], preferred_slots=["Mon 09:00", "Mon 09:00"])


class CourseValidationTests(unittest.TestCase):
    def test_rejects_negative_enrolment(self) -> None:
        with self.assertRaises(ValueError):
            Course("HIT140", "Charles Yeo", -1)

    def test_rejects_self_prerequisite(self) -> None:
        with self.assertRaises(ValueError):
            Course("HIT140", "Charles Yeo", 10, prerequisites=["HIT140"])

    def test_rejects_empty_ids_and_non_integer_enrolment(self) -> None:
        with self.assertRaises(ValueError):
            Course("", "Charles Yeo", 10)
        with self.assertRaises(ValueError):
            Course("HIT140", "", 10)
        with self.assertRaises(ValueError):
            Course("HIT140", "Charles Yeo", True)  # type: ignore[arg-type]

    def test_rejects_duplicate_prerequisites(self) -> None:
        with self.assertRaises(ValueError):
            Course("HIT140", "Charles Yeo", 10, prerequisites=["PRT575", "PRT575"])


if __name__ == "__main__":
    unittest.main()
