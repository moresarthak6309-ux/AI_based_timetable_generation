import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="AI Timetable Generator", layout="wide")

st.title("📚 AI-Based School Timetable Generator")
st.write("Generates a weekly timetable with class names, breaks, and lecture timings.")

# ---------------- CONFIG ----------------
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

st.sidebar.header("🔧 School Configuration")

num_classes = st.sidebar.number_input("Number of Classes", min_value=1, step=1)
lectures_per_day = st.sidebar.number_input("Lectures per Day", min_value=1, step=1)

st.sidebar.subheader("⏰ Time Configuration")

start_time_str = st.sidebar.time_input(
    "School / College Start Time",
    value=datetime.strptime("09:00", "%H:%M").time()
)

lecture_duration = st.sidebar.number_input(
    "Lecture Duration (minutes)",
    min_value=30,
    step=5
)

st.sidebar.subheader("☕ Break Configuration")

break_after = st.sidebar.number_input(
    "Break after how many lectures?",
    min_value=1,
    max_value=max(1, lectures_per_day - 1),
    step=1
)

break_duration = st.sidebar.number_input(
    "Break duration (minutes)",
    min_value=5,
    step=5
)

# ---------------- SUBJECT CONSTRAINTS ----------------
st.sidebar.subheader("📊 Subject Constraints")

max_subject_per_week = st.sidebar.number_input(
    "Maximum lectures per subject per week",
    min_value=1,
    value=3
)

# ---------------- CLASS NAMES ----------------
st.sidebar.subheader("🏫 Class Names")

class_names = []
for i in range(num_classes):
    name = st.sidebar.text_input(f"Name of Class {i+1}", key=f"class_{i}")
    class_names.append(name if name else f"Class {i+1}")

# ---------------- SUBJECTS & TEACHERS ----------------
st.sidebar.subheader("📘 Subjects & Teachers")

class_data = {}
lab_subjects = []

for idx, cls in enumerate(class_names):
    st.sidebar.markdown(f"### {cls}")
    subjects = []

    for s in range(lectures_per_day):
        subject = st.sidebar.text_input(
            f"Subject {s+1} ({cls})",
            key=f"sub_{idx}_{s}"
        )
        teacher = st.sidebar.text_input(
            f"Teacher ({cls}, Subject {s+1})",
            key=f"teach_{idx}_{s}"
        )

        if subject and teacher:
            subjects.append((subject, teacher))

    # Lab subjects input
    labs = st.sidebar.text_input(
        f"Lab subjects for {cls} (comma separated)",
        key=f"lab_{cls}"
    )

    if labs:
        for lab in labs.split(","):
            lab_subjects.append(lab.strip())

    class_data[cls] = subjects

# ---------------- AI TIMETABLE LOGIC ----------------
def generate_weekly_timetable():

    timetable = {}

    teacher_schedule = {
        day: {p: set() for p in range(lectures_per_day)}
        for day in days
    }

    for cls, subjects in class_data.items():

        weekly = {}

        weekly_subject_count = {s[0]: 0 for s in subjects}

        for day in days:

            daily = []
            used_today = set()

            current_time = datetime.combine(datetime.today(), start_time_str)

            lecture_no = 1
            period_index = 0
            break_added = False

            while lecture_no <= lectures_per_day:

                # ---------- BREAK ----------
                if lecture_no == break_after + 1 and not break_added:
                    break_end = current_time + timedelta(minutes=break_duration)

                    daily.append((
                        "BREAK",
                        f"{current_time.strftime('%H:%M')} - {break_end.strftime('%H:%M')}",
                        "BREAK",
                        "-"
                    ))

                    current_time = break_end
                    break_added = True
                    continue

                assigned = False
                random.shuffle(subjects)

                for subject, teacher in subjects:

                    if weekly_subject_count[subject] >= max_subject_per_week:
                        continue

                    if subject in used_today:
                        continue

                    if teacher in teacher_schedule[day][period_index]:
                        continue

                    # ---------- LAB DOUBLE PERIOD ----------
                    if subject in lab_subjects and lecture_no < lectures_per_day:

                        if teacher in teacher_schedule[day].get(period_index + 1, set()):
                            continue

                        start = current_time
                        mid = start + timedelta(minutes=lecture_duration)

                        daily.append((
                            lecture_no,
                            f"{start.strftime('%H:%M')} - {mid.strftime('%H:%M')}",
                            subject + " (Lab)",
                            teacher
                        ))

                        teacher_schedule[day][period_index].add(teacher)

                        end = mid + timedelta(minutes=lecture_duration)

                        daily.append((
                            lecture_no + 1,
                            f"{mid.strftime('%H:%M')} - {end.strftime('%H:%M')}",
                            subject + " (Lab)",
                            teacher
                        ))

                        teacher_schedule[day][period_index + 1].add(teacher)

                        weekly_subject_count[subject] += 2
                        used_today.add(subject)

                        current_time = end
                        lecture_no += 2
                        period_index += 2
                        assigned = True
                        break

                    # ---------- NORMAL SUBJECT ----------
                    else:

                        start = current_time
                        end = start + timedelta(minutes=lecture_duration)

                        daily.append((
                            lecture_no,
                            f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}",
                            subject,
                            teacher
                        ))

                        teacher_schedule[day][period_index].add(teacher)

                        weekly_subject_count[subject] += 1
                        used_today.add(subject)

                        current_time = end
                        lecture_no += 1
                        period_index += 1
                        assigned = True
                        break

                # ---------- FALLBACK ----------
                if not assigned:

                    end = current_time + timedelta(minutes=lecture_duration)

                    daily.append((
                        lecture_no,
                        f"{current_time.strftime('%H:%M')} - {end.strftime('%H:%M')}",
                        "FREE",
                        "-"
                    ))

                    current_time = end
                    lecture_no += 1
                    period_index += 1

            weekly[day] = daily

        timetable[cls] = weekly

    return timetable

# ---------------- WEEK TABLE CONVERSION ----------------
def convert_to_week_table(class_timetable):
    table = {}

    for day, periods in class_timetable.items():
        for p in periods:
            time = p[1]
            label = "BREAK" if p[0] == "BREAK" else f"{p[2]} ({p[3]})"

            if time not in table:
                table[time] = {}

            table[time][day] = label

    df = pd.DataFrame(table).T
    df = df.reindex(days, axis=1)
    df.insert(0, "Time", df.index)
    df.reset_index(drop=True, inplace=True)

    return df

# ---------------- GENERATE ----------------
if st.button("🚀 Generate Weekly Timetable"):

    timetable = generate_weekly_timetable()
    st.success("Timetable Generated Successfully!")

    for cls, week in timetable.items():

        st.header(f"🏫 {cls}")

        week_df = convert_to_week_table(week)
        st.dataframe(week_df, use_container_width=True)

        excel_file = f"{cls}_Weekly_Timetable.xlsx"
        week_df.to_excel(excel_file, index=False)

        with open(excel_file, "rb") as f:
            st.download_button(
                label=f"⬇ Download {cls} Timetable (Excel)",
                data=f,
                file_name=excel_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
