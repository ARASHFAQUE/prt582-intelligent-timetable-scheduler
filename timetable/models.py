"""Domain models for the Intelligent Timetable Scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Room:
    """A physical teaching space with a fixed seating capacity."""

    room_id: str
    capacity: int

    def __post_init__(self) -> None:
        if not self.room_id or not str(self.room_id).strip():
            raise ValueError("room_id must be a non-empty string")
        if not isinstance(self.capacity, int) or isinstance(self.capacity, bool):
            raise ValueError("capacity must be an integer")
        if self.capacity <= 0:
            raise ValueError("room capacity must be greater than zero")


@dataclass(frozen=True)
class Lecturer:
    """An instructor with available (and optionally preferred) time slots."""

    lecturer_id: str
    available_slots: tuple[str, ...]
    preferred_slots: tuple[str, ...] = field(default_factory=tuple)

    def __init__(
        self,
        lecturer_id: str,
        available_slots: list[str] | tuple[str, ...],
        preferred_slots: list[str] | tuple[str, ...] | None = None,
    ) -> None:
        if not lecturer_id or not str(lecturer_id).strip():
            raise ValueError("lecturer_id must be a non-empty string")
        if not available_slots:
            raise ValueError("lecturer must have at least one available slot")

        available = tuple(available_slots)
        preferred = tuple(preferred_slots or ())

        if len(set(available)) != len(available):
            raise ValueError("lecturer available_slots must be unique")
        if len(set(preferred)) != len(preferred):
            raise ValueError("lecturer preferred_slots must be unique")

        extra = [slot for slot in preferred if slot not in available]
        if extra:
            raise ValueError(
                "preferred slots must be a subset of available slots; "
                f"invalid: {extra}"
            )

        object.__setattr__(self, "lecturer_id", lecturer_id)
        object.__setattr__(self, "available_slots", available)
        object.__setattr__(self, "preferred_slots", preferred)

    def ordered_candidate_slots(self, time_slots: list[str]) -> list[str]:
        """Preferred slots first, then remaining availability, in timetable order."""
        slot_index = {slot: i for i, slot in enumerate(time_slots)}
        in_horizon = [s for s in self.available_slots if s in slot_index]
        preferred = [s for s in in_horizon if s in self.preferred_slots]
        remainder = [s for s in in_horizon if s not in self.preferred_slots]
        preferred.sort(key=slot_index.get)
        remainder.sort(key=slot_index.get)
        return preferred + remainder


@dataclass(frozen=True)
class Course:
    """A course offering that must be placed in exactly one room and slot."""

    course_id: str
    lecturer_id: str
    enrolled_students: int
    prerequisites: tuple[str, ...] = field(default_factory=tuple)

    def __init__(
        self,
        course_id: str,
        lecturer_id: str,
        enrolled_students: int,
        prerequisites: list[str] | tuple[str, ...] | None = None,
    ) -> None:
        if not course_id or not str(course_id).strip():
            raise ValueError("course_id must be a non-empty string")
        if not lecturer_id or not str(lecturer_id).strip():
            raise ValueError("lecturer_id must be a non-empty string")
        if not isinstance(enrolled_students, int) or isinstance(enrolled_students, bool):
            raise ValueError("enrolled_students must be an integer")
        if enrolled_students < 0:
            raise ValueError("enrolled_students cannot be negative")

        prereqs = tuple(prerequisites or ())
        if course_id in prereqs:
            raise ValueError("a course cannot be a prerequisite of itself")
        if len(set(prereqs)) != len(prereqs):
            raise ValueError("prerequisites must be unique")

        object.__setattr__(self, "course_id", course_id)
        object.__setattr__(self, "lecturer_id", lecturer_id)
        object.__setattr__(self, "enrolled_students", enrolled_students)
        object.__setattr__(self, "prerequisites", prereqs)


@dataclass(frozen=True)
class SlotAssignment:
    """A single course placement in the finished timetable."""

    course_id: str
    room_id: str
    time_slot: str
    lecturer_id: str
