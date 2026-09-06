# Intelligent Timetable Scheduler (PRT582)

Constraint-based university timetable search written with an AI-assisted test-driven workflow for **PRT582 Software Engineering: Process and Tools**.

## What it does

Given courses, rooms, lecturers, and an ordered list of time slots, the scheduler either returns a feasible assignment or raises `ValueError`. Hard constraints:

- room capacity vs enrolment
- lecturer availability
- no room double-booking
- no lecturer double-booking
- prerequisite courses occupy an **earlier** slot index
- circular prerequisite graphs are rejected
- invalid model data is rejected at construction time

Lecturer **preferred** slots are ranked first during search, then remaining availability (soft constraint).

## Run tests

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m coverage run --source=timetable -m unittest discover -s tests -v
python -m coverage report -m
```

## Demo

```bash
python demo.py
```

## Layout

| Path | Role |
|------|------|
| `timetable/models.py` | `Room`, `Lecturer`, `Course`, `SlotAssignment` |
| `timetable/scheduler.py` | backtracking search + cycle detection |
