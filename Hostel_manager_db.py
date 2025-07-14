import pandas as pd
import streamlit as st
import psycopg2
from datetime import datetime, timedelta

# ----- Users with Roles -----
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "viewer": {"password": "view123", "role": "viewer"},
}

# PostgreSQL Connection
def get_conn():
    return psycopg2.connect(
        dbname="hostel_managment",
        user="postgres",
        password="XXXXXX",
        host="localhost",
        port="5432"
    )

# Data Functions
def add_student(data):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO hostels (hostelBlock, hostelRoom_no, student_id, student_name, address, phone_number, college_name, branch, admission_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', data)
    conn.commit()
    conn.close()

def get_all_students():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hostels ORDER BY student_id")
    data = cursor.fetchall()
    conn.close()
    return data

def get_student_by_id(student_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hostels WHERE student_id = %s", (student_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def delete_student(student_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM hostels WHERE student_id = %s", (student_id,))
    conn.commit()
    conn.close()

def update_student(data, student_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE hostels 
        SET hostelBlock = %s, hostelRoom_no = %s, student_name = %s, address = %s,
            phone_number = %s, college_name = %s, branch = %s, admission_date = %s
        WHERE student_id = %s
    ''', data + (student_id,))
    conn.commit()
    conn.close()

def validate_fields(student_name, phone_number):
    if not student_name.strip():
        st.warning("⚠️ Student name cannot be empty.")
        return False
    if not phone_number.isdigit() or len(phone_number) != 10:
        st.warning("⚠️ Phone number must be 10 digits.")
        return False
    return True

# -------------------- LOGIN SYSTEM --------------------

SESSION_TIMEOUT_MINUTES = 10

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.last_active = datetime.now()
    st.session_state.username = ""
    st.session_state.role = ""

# Logout function
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.rerun()

# Auto logout after inactivity
if st.session_state.logged_in:
    now = datetime.now()
    if now - st.session_state.last_active > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        st.warning("⏱️ Session expired due to inactivity.")
        logout()
    else:
        st.session_state.last_active = now

# Login UI
if not st.session_state.logged_in:
    st.title("🔐 User Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = USERS.get(username)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = user["role"]
            st.session_state.last_active = datetime.now()
            st.success(f"✅ Welcome, {username} ({user['role']})")
            st.rerun()
        else:
            st.error("❌ Invalid credentials.")
    st.stop()

# -------------------- MAIN APP --------------------

st.title("🏨 Hostel Management System")
st.sidebar.markdown(f"👤 Logged in as **{st.session_state.username}** ({st.session_state.role})")
if st.sidebar.button("Logout"):
    logout()

# Role-based Menu
if st.session_state.role == "admin":
    menu = ["Add", "View All", "Search by ID", "Search by Hostel_Block", "Search by Room_No", "Update", "Delete", "Download"]
else:  # viewer
    menu = ["View All", "Search by ID", "Search by Hostel_Block", "Search by Room_No", "Download"]

choice = st.sidebar.selectbox("Menu", menu)

# -------------------- MENU ACTIONS --------------------

if choice == "Add":
    st.subheader("Add Student")
    hostelBlock = st.text_input("Hostel Block")
    hostelRoom_no = st.number_input("Room Number", min_value=1)
    student_id = st.text_input("Student ID")
    student_name = st.text_input("Student Name")
    address = st.text_input("Address")
    phone_number = st.text_input("Phone Number")
    college_name = st.text_input("College Name")
    branch = st.text_input("Branch")
    admission_date = st.date_input("Admission Date")

    if st.button("Add Student"):
        if validate_fields(student_name, phone_number):
            data = (hostelBlock, hostelRoom_no, student_id, student_name, address,
                    phone_number, college_name, branch, admission_date)
            add_student(data)
            st.success(f"✅ Student {student_name} added successfully!")

elif choice == "View All":
    st.subheader("All Students")
    data = get_all_students()
    if data:
        st.dataframe(data, use_container_width=True)
    else:
        st.info("⚠️ No student records found.")

elif choice == "Search by ID":
    st.subheader("Search Student")
    hostelBlock = st.text_input("Enter Hostel Block to search")
    hostelRoom_no = st.number_input("Enter Room Number to search", min_value=1)
    student_id = st.text_input("Enter Student ID to search")
    if st.button("Search"):
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hostels WHERE hostelRoom_no = %s AND hostelBlock = %s AND student_id = %s",
                       (hostelRoom_no, hostelBlock, student_id))
        data = cursor.fetchall()
        conn.close()
        if data:
            st.table(data)
        else:
            st.warning("⚠️ Student not found.")

elif choice == "Search by Hostel_Block":
    st.subheader("Search by Hostel Block")
    hostelBlock = st.text_input("Enter Hostel Block to search")
    if st.button("Search"):
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hostels WHERE hostelBlock = %s", (hostelBlock,))
        data = cursor.fetchall()
        conn.close()
        if data:
            st.table(data)
        else:
            st.warning("⚠️ No students found in this hostel block.")

elif choice == "Search by Room_No":
    st.subheader("Search by Room Number")
    hostelBlock = st.text_input("Enter Hostel Block to search")
    hostelRoom_no = st.number_input("Enter Room Number to search", min_value=1)
    if st.button("Search"):
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hostels WHERE hostelRoom_no = %s AND hostelBlock = %s", (hostelRoom_no, hostelBlock))
        data = cursor.fetchall()
        conn.close()
        if data:
            st.table(data)
        else:
            st.warning("⚠️ No students found in this room number.")

elif choice == "Update":
    st.subheader("Update Student")
    student_ids = [s[2] for s in get_all_students()]
    selected_id = st.selectbox("Select Student ID to update", student_ids)

    if st.button("Load Student"):
        student = get_student_by_id(selected_id)
        if student:
            new_hostelBlock = st.text_input("Hostel Block", value=student[0])
            new_hostelRoom_no = st.number_input("Room Number", value=student[1])
            new_student_name = st.text_input("Student Name", value=student[3])
            new_address = st.text_input("Address", value=student[4])
            new_phone_number = st.text_input("Phone Number", value=student[5])
            new_college_name = st.text_input("College Name", value=student[6])
            new_branch = st.text_input("Branch", value=student[7])
            new_admission_date = st.date_input("Admission Date", value=pd.to_datetime(student[8]))

            if st.button("Update Student"):
                if validate_fields(new_student_name, new_phone_number):
                    updated_data = (
                        new_hostelBlock, new_hostelRoom_no, new_student_name, new_address,
                        new_phone_number, new_college_name, new_branch, new_admission_date
                    )
                    update_student(updated_data, selected_id)
                    st.success(f"✅ Student ID {selected_id} updated successfully.")
        else:
            st.warning("⚠️ Student not found.")

elif choice == "Delete":
    st.subheader("Delete Student")
    student_ids = [s[2] for s in get_all_students()]
    student_id = st.selectbox("Select Student ID to delete", student_ids)
    if st.button("Delete"):
        delete_student(student_id)
        st.success(f"🗑️ Student ID {student_id} deleted.")

elif choice == "Download":
    st.subheader("📁 Download Student Data")
    data = get_all_students()
    if data:
        df = pd.DataFrame(data, columns=[
            "Hostel Block", "Room No", "Student ID", "Student Name", "Address",
            "Phone", "College", "Branch", "Admission Date"
        ])
        st.dataframe(df, use_container_width=True)
        file_format = st.radio("Select format", ("CSV", "Excel"))

        if file_format == "CSV":
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", data=csv, file_name="students.csv", mime="text/csv")
        else:
            excel = df.to_excel(index=False, engine='openpyxl')
            st.download_button("Download Excel", data=excel, file_name="students.xlsx", mime="application/vnd.ms-excel")
    else:
        st.info("⚠️ No records to download.")
