import requests
import pandas as pd
import json
from bs4 import BeautifulSoup

def get_hidden_fields(soup):
    return {
        tag["name"]: tag.get("value", "")
        for tag in soup.select("input[type=hidden]")
    }


BASE_URL = "https://stds.eng.cu.edu.eg/ClassList.aspx?s=1"

session = requests.Session()
resp = session.get(BASE_URL)
soup = BeautifulSoup(resp.text, "html.parser")

students = {}

for row in soup.select("#GridView1 tr"):
    cols = [c.get_text(strip=True) for c in row.find_all("td")]
    if len(cols) != 9:
        continue

    print(cols)

    code, course_name, place, session_type, day, begin, end, _, _ = cols
    course_id = f"{code} {course_name} -- {session_type} - {day} {begin}-{end}"

    # 2. Define the requested JSON format (CourseCode_CourseName)
    json_course_format = f"{code}_{course_name}"

    link = row.find("a")
    if not link:
        continue

    href = link["href"]

    if (not href.startswith("javascript:__doPostBack")):
            # or ( not code.startswith("CMPS") and not code.startswith("EECS") and not code.startswith(
            # "MTHS") and not code.startswith("GENS"))):
        continue

    # Extract EVENTTARGET
    event_target = href.split("'")[1]

    # Re-fetch page to keep fresh VIEWSTATE
    page = session.get(BASE_URL)
    soup = BeautifulSoup(page.text, "html.parser")
    payload = get_hidden_fields(soup)

    payload.update({
        "__EVENTTARGET": event_target,
        "__EVENTARGUMENT": ""
    })

    # Correct POST request
    xls_resp = session.post(BASE_URL, data=payload)

    with open("temp.xlsx", "wb") as f:
        f.write(xls_resp.content)

    df = pd.read_excel("temp.xlsx")

    for _, r in df.iterrows():
        seat_no = str(r["Code"]).strip()
        students.setdefault(seat_no, {
            "seat_no": seat_no,
            "arabic_name": r["Student Name"],
            "english_name": r["English Name"],
            "courses": [],
            "json_courses": []  # 3. Initialize list for JSON output
        })
        students[seat_no]["courses"].append(course_id)

        # 4. Add to JSON list (avoiding duplicates if the student is in multiple sessions of the same course)
        if json_course_format not in students[seat_no]["json_courses"]:
            students[seat_no]["json_courses"].append(json_course_format)

# Save result
pd.DataFrame([
    {
        "seat_no": s["seat_no"],
        "arabic_name": s["arabic_name"],
        "english_name": s["english_name"],
        "courses": ";".join(s["courses"])
    }
    for s in students.values()
]).to_excel("students_database_fall26.xlsx", index=False)

# Output the JSON file
json_output = {
    s["seat_no"]: {"courses": s["json_courses"]}
    for s in students.values()
}

with open("Fall26/students_courses.json", "w", encoding="utf-8") as f:
    json.dump(json_output, f, ensure_ascii=False, indent=4)