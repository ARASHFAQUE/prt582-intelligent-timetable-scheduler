"""Constraint-based timetable search with backtracking."""

from __future__ import annotations

from .models import Course, Lecturer, Room, SlotAssignment


class IntelligentTimetableScheduler:
    """Assigns each course to a feasible room and time slot.

    Search is deterministic: courses are tried in topological order (then
    course_id), candidate slots prefer lecturer preferences, and rooms are
    tried in sorted room_id order.
    """

    def schedule(
        self,
        courses: list[Course],
        rooms: list[Room],
        lecturers: list[Lecturer],
        time_slots: list[str],
    ) -> dict[str, SlotAssignment]:
        self._validate_inputs(courses, rooms, lecturers, time_slots)
        self._check_circular_prerequisites(courses)

        lecturer_by_id = {lec.lecturer_id: lec for lec in lecturers}
        room_by_id = {room.room_id: room for room in rooms}
        course_by_id = {c.course_id: c for c in courses}

        for course in courses:
            if course.lecturer_id not in lecturer_by_id:
                raise ValueError(
                    f"course {course.course_id} references unknown lecturer "
                    f"{course.lecturer_id}"
                )
            for prereq in course.prerequisites:
                if prereq not in course_by_id:
                    raise ValueError(
                        f"course {course.course_id} references unknown "
                        f"prerequisite {prereq}"
                    )
            if not any(room.capacity >= course.enrolled_students for room in rooms):
                raise ValueError(
                    f"no room can seat {course.enrolled_students} students "
                    f"for course {course.course_id}"
                )

        ordered_courses = self._topological_order(courses)
        slot_index = {slot: i for i, slot in enumerate(time_slots)}
        assignment: dict[str, SlotAssignment] = {}
        occupied_rooms: dict[tuple[str, str], str] = {}
        occupied_lecturers: dict[tuple[str, str], str] = {}

        if not self._backtrack(
            0,
            ordered_courses,
            rooms,
            lecturer_by_id,
            time_slots,
            slot_index,
            assignment,
            occupied_rooms,
            occupied_lecturers,
        ):
            raise ValueError("no feasible timetable exists for the given constraints")

        # Return assignments keyed in a stable course_id order for callers.
        return {cid: assignment[cid] for cid in sorted(assignment)}

    def _validate_inputs(
        self,
        courses: list[Course],
        rooms: list[Room],
        lecturers: list[Lecturer],
        time_slots: list[str],
    ) -> None:
        if not time_slots:
            raise ValueError("time_slots must not be empty")
        if len(set(time_slots)) != len(time_slots):
            raise ValueError("time_slots must be unique")
        if not courses:
            raise ValueError("courses must not be empty")
        if not rooms:
            raise ValueError("rooms must not be empty")
        if not lecturers:
            raise ValueError("lecturers must not be empty")

        course_ids = [c.course_id for c in courses]
        if len(set(course_ids)) != len(course_ids):
            raise ValueError("course_id values must be unique")
        room_ids = [r.room_id for r in rooms]
        if len(set(room_ids)) != len(room_ids):
            raise ValueError("room_id values must be unique")
        lecturer_ids = [lec.lecturer_id for lec in lecturers]
        if len(set(lecturer_ids)) != len(lecturer_ids):
            raise ValueError("lecturer_id values must be unique")

    def _check_circular_prerequisites(self, courses: list[Course]) -> None:
        adjacency = {c.course_id: list(c.prerequisites) for c in courses}
        visiting: set[str] = set()
        visited: set[str] = set()

        def dfs(node: str) -> None:
            if node in visited:
                return
            if node in visiting:
                raise ValueError(
                    f"circular prerequisite dependency involving {node}"
                )
            visiting.add(node)
            for neighbour in adjacency.get(node, []):
                if neighbour not in adjacency:
                    continue
                dfs(neighbour)
            visiting.remove(node)
            visited.add(node)

        for course_id in adjacency:
            dfs(course_id)

    def _topological_order(self, courses: list[Course]) -> list[Course]:
        by_id = {c.course_id: c for c in courses}
        incoming = {c.course_id: 0 for c in courses}
        outgoing: dict[str, list[str]] = {c.course_id: [] for c in courses}

        for course in courses:
            for prereq in course.prerequisites:
                incoming[course.course_id] += 1
                outgoing[prereq].append(course.course_id)

        ready = sorted(cid for cid, count in incoming.items() if count == 0)
        ordered: list[Course] = []
        while ready:
            current = ready.pop(0)
            ordered.append(by_id[current])
            nxt = []
            for dependent in outgoing[current]:
                incoming[dependent] -= 1
                if incoming[dependent] == 0:
                    nxt.append(dependent)
            ready.extend(sorted(nxt))
            ready.sort()
        return ordered

    def _backtrack(
        self,
        index: int,
        ordered_courses: list[Course],
        rooms: list[Room],
        lecturer_by_id: dict[str, Lecturer],
        time_slots: list[str],
        slot_index: dict[str, int],
        assignment: dict[str, SlotAssignment],
        occupied_rooms: dict[tuple[str, str], str],
        occupied_lecturers: dict[tuple[str, str], str],
    ) -> bool:
        if index == len(ordered_courses):
            return True

        course = ordered_courses[index]
        lecturer = lecturer_by_id[course.lecturer_id]
        candidate_slots = lecturer.ordered_candidate_slots(time_slots)
        suitable_rooms = sorted(
            (room for room in rooms if room.capacity >= course.enrolled_students),
            key=lambda r: (r.capacity, r.room_id),
        )

        for slot in candidate_slots:
            if not self._prerequisites_satisfied(course, slot, assignment, slot_index):
                continue
            if (lecturer.lecturer_id, slot) in occupied_lecturers:
                continue
            for room in suitable_rooms:
                if (room.room_id, slot) in occupied_rooms:
                    continue
                placed = SlotAssignment(
                    course_id=course.course_id,
                    room_id=room.room_id,
                    time_slot=slot,
                    lecturer_id=lecturer.lecturer_id,
                )
                assignment[course.course_id] = placed
                occupied_rooms[(room.room_id, slot)] = course.course_id
                occupied_lecturers[(lecturer.lecturer_id, slot)] = course.course_id
                if self._backtrack(
                    index + 1,
                    ordered_courses,
                    rooms,
                    lecturer_by_id,
                    time_slots,
                    slot_index,
                    assignment,
                    occupied_rooms,
                    occupied_lecturers,
                ):
                    return True
                del assignment[course.course_id]
                del occupied_rooms[(room.room_id, slot)]
                del occupied_lecturers[(lecturer.lecturer_id, slot)]
        return False

    def _prerequisites_satisfied(
        self,
        course: Course,
        slot: str,
        assignment: dict[str, SlotAssignment],
        slot_index: dict[str, int],
    ) -> bool:
        current_index = slot_index[slot]
        for prereq_id in course.prerequisites:
            placed = assignment.get(prereq_id)
            if placed is None:
                return False
            if slot_index[placed.time_slot] >= current_index:
                return False
        return True
