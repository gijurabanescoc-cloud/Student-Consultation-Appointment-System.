from datetime import datetime, timedelta

students = []
instructors = []
appointments = []
time_slots = []
BACK = "__BACK__"

def get_input(prompt):
    """Read input and make B a consistent back command."""
    value = input(f"{prompt} (B = Back to previous step): ").strip()
    return BACK if value.upper() == "B" else value

def parse_date(date_text):
    """Parse dates in MM/DD/YY format, allowing years up to 2026 only."""
    try:
        parsed_date = datetime.strptime(date_text, "%m/%d/%y").date()

        # Do not allow dates after December 31, 2026.
        if parsed_date.year > 2026:
            return None

        return parsed_date
    except ValueError:
        return None

def validate_date(date_text):
    return parse_date(date_text) is not None

def validate_student_id(student_id):
    parts = student_id.split("-")
    return (
        len(parts) == 3
        and len(parts[0]) == 2
        and len(parts[1]) == 4
        and len(parts[2]) == 6
        and all(part.isdigit() for part in parts)
    )

def validate_section(section):
    # Example: COC-FC1-BSIT1-01
    import re
    return bool(re.fullmatch(r"COC-[A-Z0-9]+-BSIT[1-4]-\d{2}", section.upper()))

def validate_time(time_text):
    try:
        datetime.strptime(time_text.upper(), "%I:%M %p")
        return True
    except ValueError:
        return False

def convert_time(time_text):
    return datetime.strptime(time_text.upper(), "%I:%M %p")

def format_time(value):
    return value.strftime("%I:%M %p")

def get_number(prompt):
    while True:
        value = get_input(prompt)
        if value == BACK:
            return BACK
        try:
            number = int(value)
            if number > 0:
                return number
        except ValueError:
            pass
        print("Please enter a whole number greater than 0.")

def select_item(items, prompt):
    while True:
        value = get_input(prompt)
        if value == BACK:
            return None
        try:
            number = int(value)
            if 1 <= number <= len(items):
                return items[number - 1]
        except ValueError:
            pass
        print("Invalid selection. Choose one of the listed numbers.")

def print_table(headers, rows):
    """Print all rows in one readable ASCII table."""
    if not rows:
        print("No records to display.")
        return
    rows = [[str(value) for value in row] for row in rows]
    widths = [len(str(header)) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))
    border = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    print(border)
    print("| " + " | ".join(str(header).ljust(widths[i]) for i, header in enumerate(headers)) + " |")
    print(border)
    for row in rows:
        print("| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(headers))) + " |")
    print(border)

def collect_fields(fields):
    """
    Collect form values. Pressing B moves to the previous field;
    pressing B at the first field returns to the calling menu.
    Each field is (key, prompt, validator, error_message, transform).
    """
    values = {}
    index = 0
    while index < len(fields):
        key, prompt, validator, error_message, transform = fields[index]
        value = get_input(prompt)
        if value == BACK:
            if index == 0:
                return None
            index -= 1
            continue
        if validator and not validator(value):
            print(error_message)
            continue
        values[key] = transform(value) if transform else value
        index += 1
    return values

def register_student():
    print("\n--- STUDENT REGISTRATION ---")
    year_options = {"1": "1st Year", "2": "2nd Year", "3": "3rd Year", "4": "4th Year"}
    print("Year level options: 1. 1st Year  2. 2nd Year  3. 3rd Year  4. 4th Year")
    fields = [
        ("name", "Enter your full name: ", lambda x: bool(x), "Name cannot be blank.", None),
        ("year", "Enter year level (1-4): ",
         lambda x: x in year_options, "Enter 1, 2, 3, or 4 for the year level.",
         lambda x: year_options[x]),
        ("section", "Enter section (e.g., COC-FC1-BSIT1-01): ",
         lambda x: validate_section(x), "Invalid section. Use the format COC-FC1-BSIT1-01.",
         lambda x: x.upper()),
        ("student_id", "Enter Student ID (00-0000-000000): ",
         validate_student_id, "Invalid Student ID. Use the format 00-0000-000000.", None),
        ("password", "Create password: ", lambda x: bool(x), "Password cannot be1 blank.", None),
    ]
    data = collect_fields(fields)
    if data is None:
        print("Registration cancelled. Returning to the previous menu.")
        return
    if any(s["student_id"] == data["student_id"] for s in students):
        print("Student ID already registered.")
        return
    students.append(data)
    print("Student registration successful!")

def register_instructor():
    print("\n--- INSTRUCTOR REGISTRATION ---")
    fields = [
        ("name", "Enter your full name: ", lambda x: bool(x), "Name cannot be blank.", None),
        ("username", "Create username: ", lambda x: bool(x), "Username cannot be blank.", None),
        ("password", "Create password: ", lambda x: bool(x), "Password cannot be blank.", None),
    ]
    data = collect_fields(fields)
    if data is None:
        print("Registration cancelled. Returning to the previous menu.")
        return
    if any(i["username"] == data["username"] for i in instructors):
        print("Username already exists.")
        return
    instructors.append(data)
    print("Instructor registration successful!")

def login(accounts, title, menu):
    print(f"\n--- {title} LOGIN ---")
    identity_key = "student_id" if title == "STUDENT" else "username"
    identity_label = "Student ID" if title == "STUDENT" else "Username"
    identity = get_input(f"{identity_label}: ")
    if identity == BACK:
        return
    password = get_input("Password: ")
    if password == BACK:
        # Return to the identity prompt rather than restarting the login process.
        identity = get_input(f"{identity_label}: ")
        if identity == BACK:
            return
        password = get_input("Password: ")
        if password == BACK:
            return
    for account in accounts:
        if account[identity_key] == identity and account["password"] == password:
            print(f"Welcome, {account['name']}!")
            return menu(account)
    print("Invalid username or password.")

def student_login():
    return login(students, "STUDENT", student_menu)

def instructor_login():
    return login(instructors, "INSTRUCTOR", instructor_menu)

def get_used_slots(slot, exclude=None):
    return sum(
        1 for appointment in appointments
        if appointment is not exclude
        and appointment["status"] in ("Pending", "Accepted")
        and appointment["instructor"] == slot["instructor"]
        and appointment["date"] == slot["date"]
        and appointment["time"] == slot["time"]
    )

def get_remaining_slots(slot, exclude=None):
    return slot["slots"] - get_used_slots(slot, exclude)

def find_slot(appointment):
    for slot in time_slots:
        if (
            slot["instructor"] == appointment["instructor"]
            and slot["date"] == appointment["date"]
            and slot["time"] == appointment["time"]
        ):
            return slot
    return None

def show_time_slots(slots=None, exclude=None):
    """Let students choose an instructor first, then view that instructor's available days."""
    if slots is not None:
        available = [slot for slot in slots if get_remaining_slots(slot, exclude) > 0]
        print("\n--- AVAILABLE TIME BLOCKS ---")
        if not available:
            print("No available time blocks.")
            return []
        available.sort(key=lambda slot: (
            datetime.strptime(slot["date"], "%m/%d/%y"),
            convert_time(slot["time"].split(" - ")[0]),
            slot["instructor"]
        ))
        rows = []
        for number, slot in enumerate(available, 1):
            day = slot.get("weekday", datetime.strptime(slot["date"], "%m/%d/%y").strftime("%A"))
            rows.append([
                number, day, slot["date"], slot["time"],
                get_remaining_slots(slot, exclude)
            ])
        print_table(["No.", "Day", "Date", "Available Time Block", "Remaining Capacity"], rows)
        return available

    instructor_names = sorted({
        slot["instructor"] for slot in time_slots
        if get_remaining_slots(slot, exclude) > 0
    })
    while True:
        print("\n--- CHOOSE AN INSTRUCTOR ---")
        if not instructor_names:
            print("No instructors currently have available consultation blocks.")
            return []
        for number, name in enumerate(instructor_names, 1):
            print(f"{number}. {name}")
        selected = select_item(instructor_names, "Select an instructor number")
        if selected is None:
            return []
        instructor_slots = [
            slot for slot in time_slots
            if slot["instructor"] == selected
            and get_remaining_slots(slot, exclude) > 0
        ]
        available = show_time_slots(instructor_slots, exclude)
        if available:
            return available
        # If the selected instructor has no remaining blocks, return to the instructor list.

def add_time_slot(instructor):
    print("\n--- SET SEMESTER AVAILABILITY ---")
    print("Choose recurring weekdays and a date range for the semester.")
    print("Each selected day will have ONE appointment block, not hourly slots.")
    weekdays = {
        "1": ("Monday", 0), "2": ("Tuesday", 1), "3": ("Wednesday", 2),
        "4": ("Thursday", 3), "5": ("Friday", 4), "6": ("Saturday", 5),
        "7": ("Sunday", 6),
    }
    print("1. Monday  2. Tuesday  3. Wednesday  4. Thursday")
    print("5. Friday  6. Saturday  7. Sunday")

    fields = [
        ("selected", "Enter weekday numbers separated by commas (e.g., 1,2,5): ",
         lambda x: bool(x.split(",")) and all(part.strip() in weekdays for part in x.split(",")),
         "Enter weekday numbers from 1 to 7, separated by commas.",
         lambda x: sorted(set(int(part.strip()) for part in x.split(",")))),
        ("start_date", "Enter first available date (MM/DD/YY): ",
         validate_date, "Invalid date. Use a real date in MM/DD/YY format.", None),
        ("end_date", "Enter last day of the semester (MM/DD/YY): ",
         validate_date, "Invalid date. Use a real date in MM/DD/YY format.", None),
        ("start_time", "Enter block start time (e.g., 08:00 AM): ",
         validate_time, "Invalid time. Use HH:MM AM/PM, such as 08:00 AM.",
         lambda x: format_time(convert_time(x))),
        ("end_time", "Enter block end time (e.g., 12:00 PM): ",
         validate_time, "Invalid time. Use HH:MM AM/PM, such as 12:00 PM.",
         lambda x: format_time(convert_time(x))),
        ("capacity", "Maximum students for each selected day/time block: ",
         lambda x: x.isdigit() and int(x) > 0,
         "Enter a whole number greater than 0.", int),
    ]
    data = collect_fields(fields)
    if data is None:
        print("Availability setup cancelled. Returning to the previous step.")
        return

    start_day = parse_date(data["start_date"])
    end_day = parse_date(data["end_date"])
    if start_day < datetime.now().date():
        print("The first available date must be today or in the future.")
        return
    if end_day < start_day:
        print("The semester end date must be on or after the first available date.")
        return

    start_clock = convert_time(data["start_time"])
    end_clock = convert_time(data["end_time"])
    if end_clock <= start_clock:
        print("The end time must be later than the start time.")
        return

    selected_weekdays = {weekdays[str(number)][1] for number in data["selected"]}
    created = 0
    current_day = start_day
    while current_day <= end_day:
        if current_day.weekday() in selected_weekdays:
            date_text = current_day.strftime("%m/%d/%y")
            time_text = f"{data['start_time']} - {data['end_time']}"
            duplicate = any(
                slot["instructor"] == instructor["name"]
                and slot["date"] == date_text
                and slot["time"] == time_text
                for slot in time_slots
            )
            slot_start = datetime.combine(current_day, start_clock.time())
            if slot_start >= datetime.now() and not duplicate:
                time_slots.append({
                    "instructor": instructor["name"],
                    "date": date_text,
                    "time": time_text,
                    "slots": data["capacity"],
                    "weekday": current_day.strftime("%A"),
                })
                created += 1
        current_day += timedelta(days=1)

    if created:
        print(f"Successfully created {created} day-based appointment block(s) through {end_day.strftime('%m/%d/%y')}.")
    else:
        print("No new appointment blocks were added. Check the dates, weekdays, time range, or existing blocks.")

def view_my_time_slots(instructor):
    print("\n--- MY SEMESTER TIME SLOTS ---")
    mine = [slot for slot in time_slots if slot["instructor"] == instructor["name"]]
    if not mine:
        print("You have no available time slots.")
        return
    mine.sort(key=lambda slot: (
        datetime.strptime(slot["date"], "%m/%d/%y"),
        convert_time(slot["time"].split(" - ")[0])
    ))
    rows = []
    for number, slot in enumerate(mine, 1):
        used = get_used_slots(slot)
        rows.append([
            number, slot.get("weekday", datetime.strptime(slot["date"], "%m/%d/%y").strftime("%A")),
            slot["date"], slot["time"], slot["slots"], used, slot["slots"] - used
        ])
    # One consolidated table for all of the instructor's semester slots.
    print_table(["No.", "Day", "Date", "Time", "Capacity", "Used", "Remaining"], rows)

def student_appointments(student, active=False):
    return [
        appointment for appointment in appointments
        if appointment["student"] == student["name"]
        and (not active or appointment["status"] in ("Pending", "Accepted"))
    ]

def set_appointment(student):
    instructor_names = sorted({
        slot["instructor"] for slot in time_slots
        if get_remaining_slots(slot) > 0
    })
    print("\n--- CHOOSE AN INSTRUCTOR ---")
    if not instructor_names:
        print("No instructors currently have available consultation blocks.")
        return

    for number, name in enumerate(instructor_names, 1):
        print(f"{number}. {name}")
    selected_instructor = select_item(instructor_names, "Select an instructor number")
    if selected_instructor is None:
        return

    while True:
        instructor_slots = [
            slot for slot in time_slots
            if slot["instructor"] == selected_instructor
            and get_remaining_slots(slot) > 0
        ]
        instructor_slots.sort(key=lambda slot: (
            datetime.strptime(slot["date"], "%m/%d/%y"),
            convert_time(slot["time"].split(" - ")[0])
        ))

        print(f"\n--- AVAILABLE DAYS: {selected_instructor} ---")
        if not instructor_slots:
            print("This instructor has no available days/time blocks.")
            return

        rows = []
        for number, slot in enumerate(instructor_slots, 1):
            day = slot.get("weekday", datetime.strptime(slot["date"], "%m/%d/%y").strftime("%A"))
            rows.append([
                number, day, slot["date"], slot["time"],
                get_remaining_slots(slot)
            ])
        print_table(["No.", "Day", "Date", "Available Time Block", "Remaining Capacity"], rows)

        slot = select_item(instructor_slots, "Select an available day number")
        if slot is None:
            # Go back one step to the instructor list.
            available_instructors = sorted({
                item["instructor"] for item in time_slots
                if get_remaining_slots(item) > 0
            })
            print("\n--- CHOOSE AN INSTRUCTOR ---")
            if not available_instructors:
                print("No instructors currently have available consultation blocks.")
                return
            for number, name in enumerate(available_instructors, 1):
                print(f"{number}. {name}")
            selected_instructor = select_item(available_instructors, "Select an instructor number")
            if selected_instructor is None:
                return
            continue

        purpose = get_input("Enter purpose of consultation")
        if purpose == BACK:
            # B returns to choosing the available day.
            continue

        duplicate = any(
            appointment["student"] == student["name"]
            and appointment["status"] in ("Pending", "Accepted")
            and appointment["date"] == slot["date"]
            and appointment["time"] == slot["time"]
            for appointment in appointments
        )
        if duplicate:
            print("You already have an active appointment for this day/time block.")
            continue
        if get_remaining_slots(slot) <= 0:
            print("Sorry, this day/time block has just become full.")
            continue

        appointments.append({
            "student": student["name"],
            "year": student["year"],
            "section": student["section"],
            "instructor": slot["instructor"],
            "date": slot["date"],
            "time": slot["time"],
            "purpose": purpose,
            "status": "Pending",
        })
        print(
            f"Consultation request sent to {selected_instructor} successfully!\n"
            "Status: Pending"
        )
        return

def view_student_appointments(student):
    records = student_appointments(student)
    print("\n--- MY CONSULTATION APPOINTMENTS ---")
    if not records:
        print("You have no consultation appointments.")
        return
    rows = [
        [i, a["instructor"], a["year"], a["section"], a["date"], a["time"], a["purpose"], a["status"]]
        for i, a in enumerate(records, 1)
    ]
    print_table(["No.", "Instructor", "Year", "Section", "Date", "Time", "Purpose", "Status"], rows)

def change_appointment(student):
    records = student_appointments(student, True)
    if not records:
        print("\nYou have no appointments that can be changed.")
        return
    print("\n--- CHANGE CONSULTATION APPOINTMENT ---")
    print_table(
        ["No.", "Instructor", "Date", "Time", "Status"],
        [[i, a["instructor"], a["date"], a["time"], a["status"]] for i, a in enumerate(records, 1)]
    )
    current = select_item(records, "Select appointment to change")
    if current is None:
        return
    while True:
        available = show_time_slots(exclude=current)
        if not available:
            return
        slot = select_item(available, "Select new time slot")
        if slot is None:
            return
        current.update({
            "instructor": slot["instructor"], "date": slot["date"],
            "time": slot["time"], "status": "Pending",
        })
        print("Consultation appointment changed successfully!\nStatus has been reset to Pending.")
        return

def cancel_appointment(student):
    records = student_appointments(student, True)
    if not records:
        print("\nYou have no appointments that can be cancelled.")
        return
    print("\n--- CANCEL CONSULTATION APPOINTMENT ---")
    print_table(
        ["No.", "Instructor", "Date", "Time", "Status"],
        [[i, a["instructor"], a["date"], a["time"], a["status"]] for i, a in enumerate(records, 1)]
    )
    appointment = select_item(records, "Select appointment to cancel")
    if appointment is None:
        return
    appointment["status"] = "Cancelled"
    print("Consultation appointment cancelled successfully.")

def instructor_requests(instructor, pending=False):
    return [
        appointment for appointment in appointments
        if appointment["instructor"] == instructor["name"]
        and (not pending or appointment["status"] == "Pending")
    ]

def view_instructor_appointments(instructor):
    records = instructor_requests(instructor)
    print("\n--- STUDENT CONSULTATION REQUESTS ---")
    if not records:
        print("No student consultation requests.")
        return
    rows = [
        [i, a["student"], a["year"], a["section"], a["date"], a["time"], a["purpose"], a["status"]]
        for i, a in enumerate(records, 1)
    ]
    print_table(["No.", "Student", "Year", "Section", "Date", "Time", "Purpose", "Status"], rows)

def manage_appointment(instructor):
    records = instructor_requests(instructor, True)
    if not records:
        print("\nNo pending student consultation requests.")
        return
    print("\n--- ACCEPT/REJECT REQUEST ---")
    print_table(
        ["No.", "Student", "Year", "Section", "Date", "Time", "Purpose"],
        [[i, a["student"], a["year"], a["section"], a["date"], a["time"], a["purpose"]]
         for i, a in enumerate(records, 1)]
    )
    appointment = select_item(records, "Select request")
    if appointment is None:
        return
    action = get_input("Enter 1 to Accept or 2 to Reject")
    if action == BACK:
        # Return to selecting a request.
        return manage_appointment(instructor)
    if action == "2":
        appointment["status"] = "Rejected"
        print("Consultation request rejected.")
        return
    if action != "1":
        print("Invalid choice.")
        return
    slot = find_slot(appointment)
    if slot is None or get_used_slots(slot, appointment) >= slot["slots"]:
        appointment["status"] = "Rejected"
        print("Time slot is full or no longer exists. Request rejected.")
        return
    appointment["status"] = "Accepted"
    print("Consultation request accepted.")

def student_menu(student):
    while True:
        print(
            "\n--- STUDENT MENU ---\n"
            "1. View Available Time Slots\n2. Request Consultation\n"
            "3. View My Appointments\n4. Change Appointment\n"
            "5. Cancel Appointment\n6. Logout"
        )
        choice = input("Enter your choice (select 6 to logout): ").strip().upper()
        if choice == "6":
            print("Logging out...")
            return "LOGOUT"
        if choice == "1":
            show_time_slots()
        elif choice == "2":
            set_appointment(student)
        elif choice == "3":
            view_student_appointments(student)
        elif choice == "4":
            change_appointment(student)
        elif choice == "5":
            cancel_appointment(student)
        else:
            print("Invalid choice.")

def instructor_menu(instructor):
    while True:
        print(
            "\n--- INSTRUCTOR MENU ---\n"
            "1. Add Semester Availability\n2. View My Time Slots\n"
            "3. View Student Requests\n4. Accept/Reject Request\n5. Logout"
        )
        choice = input("Enter your choice (select 5 to logout): ").strip().upper()
        if choice == "5":
            print("Logging out...")
            return "LOGOUT"
        if choice == "1":
            add_time_slot(instructor)
        elif choice == "2":
            view_my_time_slots(instructor)
        elif choice == "3":
            view_instructor_appointments(instructor)
        elif choice == "4":
            manage_appointment(instructor)
        else:
            print("Invalid choice.")

def account_menu(user_type):
    while True:
        print(f"\n--- {user_type.upper()} ACCOUNT ---\n1. Register\n2. Login\n3. Back")
        choice = input("Enter your choice: ").strip()
        if choice == "1":
            register_student() if user_type == "Student" else register_instructor()
        elif choice == "2":
            result = student_login() if user_type == "Student" else instructor_login()
            if result == "LOGOUT":
                return
        elif choice == "3" or choice.upper() == "B":
            return
        else:
            print("Invalid choice. Enter 1, 2, or 3.")

def main():
    while True:
        print(
            "\n==========================================\n"
            " STUDENT CONSULTATION APPOINTMENT SYSTEM\n"
            "==========================================\n"
            "1. Student\n2. Instructor\n3. Exit"
        )
        choice = input("Enter your choice: ").strip()
        if choice == "1":
            account_menu("Student")
        elif choice == "2":
            account_menu("Instructor")
        elif choice == "3":
            print("Thank you for using the system!")
            break
        else:
            print("Invalid choice. Enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
