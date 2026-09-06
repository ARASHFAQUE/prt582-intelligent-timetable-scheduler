"""Small CLI demo that prints a feasible timetable."""

from timetable import Course, IntelligentTimetableScheduler, Lecturer, Room


def main() -> None:
    rooms = [
        Room("Lab-A", 25),
        Room("Hall-B", 80),
    ]
    lecturers = [
        Lecturer(
            "Charles Yeo",
            ["Mon 09:00", "Mon 11:00", "Tue 09:00"],
            preferred_slots=["Mon 11:00"],
        ),
        Lecturer("Abdullah Al-Amoodi", ["Mon 09:00", "Tue 09:00", "Fri 09:00"]),
    ]
    courses = [
        Course("HIT140", "Charles Yeo", 20),
        Course("PRT582", "Abdullah Al-Amoodi", 60, prerequisites=["HIT140"]),
        Course("PRT575", "Charles Yeo", 18),
    ]
    slots = ["Mon 09:00", "Mon 11:00", "Tue 09:00", "Fri 09:00"]

    timetable = IntelligentTimetableScheduler().schedule(courses, rooms, lecturers, slots)
    print("Feasible timetable")
    print("-" * 72)
    print(f"{'Course':<10}{'Lecturer':<22}{'Room':<12}{'Slot'}")
    for course_id in sorted(timetable):
        placed = timetable[course_id]
        print(
            f"{placed.course_id:<10}{placed.lecturer_id:<22}"
            f"{placed.room_id:<12}{placed.time_slot}"
        )


if __name__ == "__main__":
    main()
