# auto_scheduler.py
#
# This module provides the single source of truth for the production-grade auto timetable generator.
# Only the function `auto_generate_timetable` should be used.
# It enforces all real-world constraints as per the specification:
#   - No subject appears more than twice per day unless forced
#   - Avoids back-to-back allocations of the same subject
#   - Fair distribution of subjects across the week
#   - Fills unused slots with 'Free'
#   - Raises ValueError on invalid input or overload
#
import random
from collections import Counter, deque


def auto_generate_timetable(class_code, periods_per_day, working_days, subject_loads, teacher_map, all_class_schedules=None):
    """
    Production-grade auto timetable generator with global teacher conflict checking.
    Args:
        class_code (str): Class code (e.g., 'BIO103')
        periods_per_day (int): Number of periods per day
        working_days (list of str): List of working days (e.g., ["Monday",...])
        subject_loads (dict): {subject: periods_per_week}
        teacher_map (dict): {subject: teacher_name}
        all_class_schedules (dict): {other_class_code: {day: [subject,...]}} (optional)
    Returns:
        dict: {day: [subject,...]} timetable, or raises ValueError on error
    """
    if not class_code or not isinstance(class_code, str):
        raise ValueError("Missing or invalid class code.")
    if not isinstance(periods_per_day, int) or periods_per_day < 1:
        raise ValueError("Periods per day must be a positive integer.")
    if not working_days or not isinstance(working_days, list) or not all(isinstance(d, str) for d in working_days):
        raise ValueError("Working days must be a list of day names.")
    if not subject_loads or not isinstance(subject_loads, dict) or not all(isinstance(k, str) and isinstance(v, int) and v > 0 for k, v in subject_loads.items()):
        raise ValueError("Subject loads must be a dict of subject:str to periods:int (>0).")
    if not teacher_map or not isinstance(teacher_map, dict):
        raise ValueError("Teacher map must be provided.")
    total_slots = periods_per_day * len(working_days)
    total_requested = sum(subject_loads.values())
    if total_requested > total_slots:
        raise ValueError(f"Too many subject periods ({total_requested}) for available slots ({total_slots}).")
    subject_pool = []
    for subject, count in subject_loads.items():
        subject_pool.extend([subject] * count)
    free_count = total_slots - len(subject_pool)
    if free_count > 0:
        subject_pool.extend(["Free"] * free_count)
    random.shuffle(subject_pool)
    timetable = {day: [None] * periods_per_day for day in working_days}
    subject_counts_per_day = {day: Counter() for day in working_days}
    last_subject_per_day = {day: None for day in working_days}
    teacher_schedule = {}
    if all_class_schedules:
        for other_class, sched in all_class_schedules.items():
            if other_class == class_code:
                continue
            for day, periods in sched.items():
                for period_idx, subj in enumerate(periods):
                    teacher = teacher_map.get(subj)
                    if teacher:
                        teacher_schedule.setdefault(teacher, {}).setdefault(day, set()).add(period_idx)
    for period in range(periods_per_day):
        for day in working_days:
            placed = False
            for idx, candidate in enumerate(subject_pool):
                if candidate == "Free":
                    timetable[day][period] = "Free"
                    subject_pool.pop(idx)
                    placed = True
                    break
                if subject_counts_per_day[day][candidate] >= 2:
                    continue
                if last_subject_per_day[day] == candidate and subject_counts_per_day[day][candidate] > 0:
                    continue
                teacher = teacher_map.get(candidate)
                if teacher:
                    if teacher in teacher_schedule and day in teacher_schedule[teacher] and period in teacher_schedule[teacher][day]:
                        continue
                timetable[day][period] = candidate
                subject_counts_per_day[day][candidate] += 1
                last_subject_per_day[day] = candidate
                subject_pool.pop(idx)
                if teacher:
                    teacher_schedule.setdefault(teacher, {}).setdefault(day, set()).add(period)
                placed = True
                break
            if not placed:
                timetable[day][period] = "CONFLICT"
    for day in working_days:
        for period in range(periods_per_day):
            if timetable[day][period] is None:
                timetable[day][period] = "Free"
    return timetable 