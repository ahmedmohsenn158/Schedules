import pandas as pd
import re
from collections import defaultdict


def parse_time_to_minutes(time_str):
    """Converts a time string like '9:00' or '2:00' into minutes since midnight."""
    # Split handling potential spaces
    time_str = time_str.strip()
    hours, minutes = map(int, time_str.split(':'))

    # Assuming university hours (8:00 AM to roughly 8:00 PM)
    # If the hour is between 1 and 7, it's likely a PM time.
    if hours < 8:
        hours += 12

    return hours * 60 + minutes


def check_time_overlap(time_range1, time_range2):
    """Checks if two time ranges (e.g., '9:00-10:50' and '10:00-11:50') overlap."""
    start1_str, end1_str = time_range1.split('-')
    start2_str, end2_str = time_range2.split('-')

    start1 = parse_time_to_minutes(start1_str)
    end1 = parse_time_to_minutes(end1_str)
    start2 = parse_time_to_minutes(start2_str)
    end2 = parse_time_to_minutes(end2_str)

    # Overlap occurs if the latest start time is strictly before the earliest end time
    return max(start1, start2) < min(end1, end2)


def find_schedule_clashes(excel_path, target_course_code, target_day, target_time):
    # Read the Excel file
    df = pd.read_excel(excel_path, header=None, names=['id', 'arabic_name', 'english_name', 'courses'])

    # Regex to parse a course line: Code Name -- Type - Day Time
    course_pattern = re.compile(
        r"(?P<code>[A-Z0-9]+)\s+(?P<name>.*?)\s*--\s*(?P<type>.*?)\s*-\s*(?P<day>[A-Za-z]+)\s+(?P<time>\d{1,2}:\d{2}-\d{1,2}:\d{2})"
    )

    # Use a defaultdict to group students by the specific clash
    grouped_clashes = defaultdict(list)
    total_clashes = 0

    for index, row in df.iterrows():
        # Skip empty rows
        if pd.isna(row['courses']):
            continue

        student_id = str(row['id']).strip()  # Ensure ID is treated as a clean string
        english_name = str(row['english_name']).strip()
        courses_str = str(row['courses']).splitlines()

        parsed_courses = []
        takes_target_course = False

        # Parse all courses for the current student
        for course_line in courses_str:
            course_line = course_line.strip()
            if not course_line:
                continue

            match = course_pattern.search(course_line)
            if match:
                course_data = match.groupdict()
                parsed_courses.append(course_data)
                if course_data['code'] == target_course_code:
                    takes_target_course = True

        # Check for overlaps if the student is taking the target course
        if takes_target_course:
            for course in parsed_courses:
                # Don't check the target course against itself
                if course['code'] != target_course_code:
                    if course['day'].lower() == target_day.lower():
                        if check_time_overlap(course['time'], target_time):
                            # Create a formatted string for the specific clash group
                            clash_key = f"{course['code']} ({course['type'].strip()}) at {course['day']} {course['time']}"

                            grouped_clashes[clash_key].append({
                                'id': student_id,
                                'name': english_name
                            })
                            total_clashes += 1

    return grouped_clashes, total_clashes


# --- Execution ---
if __name__ == "__main__":
    excel_file = 'students_database_fall26.xlsx'

    # Inputs matching your example
    course_input = 'EECS100'
    day_input = 'Sunday'
    time_input = '11:00-12:00'

    try:
        clashes_dict, clash_count = find_schedule_clashes(excel_file, course_input, day_input, time_input)

        # Print the exact requested format
        print(f"Total Clashes for {course_input} on {day_input} {time_input}: {clash_count}\n")

        # Sort keys so the output is consistent and organized
        for clash_info in sorted(clashes_dict.keys()):
            students = clashes_dict[clash_info]
            print(f"Clash: {clash_info}: {len(students)}")
            for student in students:
                print(f"ID: {student['id']} | Name: {student['name']}")
            print()  # Add an empty line between clash blocks

    except FileNotFoundError:
        print(f"Error: Could not find the file '{excel_file}'.")
    except Exception as e:
        print(f"An error occurred: {e}")