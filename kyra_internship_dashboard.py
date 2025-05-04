# -*- coding: utf-8 -*-
"""kyra_internship_dashboard.py

Ky'ra Internship Dashboard with enhanced UI and role-based dashboards.
"""

# --- Imports ---
import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
import uuid

# --- Streamlit Config ---
st.set_page_config(
    page_title="Ky'ra Internship Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🌟"
)

# Custom CSS for Ky'ra branding
st.markdown("""
    <style>
    /* General Styling */
    body {
        font-family: 'Poppins', sans-serif;
        background-color: #FAF9F6;
        color: #333333;
    }
    .stApp {
        background-color: #FAF9F6;
    }
    /* Headings */
    h1, h2, h3, h4 {
        color: #50C878;
        font-weight: 600;
    }
    h1 { font-size: 24px; }
    h2 { font-size: 20px; }
    h3 { font-size: 16px; }
    /* Buttons */
    .stButton>button {
        background-color: #50C878;
        color: #FAF9F6;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-size: 14px;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #FFD700;
        color: #333333;
    }
    /* Sidebar */
    .css-1d391kg {
        background-color: #FAF9F6;
        border-right: 1px solid #E0E0E0;
    }
    .sidebar .sidebar-content {
        padding: 20px;
    }
    /* Cards */
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    /* Inputs */
    .stTextInput>div>input, .stTextArea textarea {
        border-radius: 8px;
        border: 1px solid #E0E0E0;
        background-color: #FFFFFF;
    }
    </style>
""", unsafe_allow_html=True)

# --- Database Connection (SQLite) ---
@st.cache_resource
def get_connection():
    db_path = os.path.join(os.getcwd(), "internship_tracking.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return conn

# --- Database Initialization ---
@st.cache_data
def initialize_database():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL,
            org TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT,
            FOREIGN KEY (student_id) REFERENCES users (id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            query_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            prompt TEXT,
            response TEXT,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            metric_name TEXT,
            value INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS internships (
            internship_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            company_name TEXT NOT NULL,
            duration TEXT NOT NULL,
            feedback TEXT,
            msme_digitalized INTEGER DEFAULT 0,
            FOREIGN KEY (student_id) REFERENCES users (id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            rating INTEGER,
            comments TEXT,
            FOREIGN KEY (student_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    cur.close()

# --- Helper Functions ---
def fetch_user_data(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, role, org FROM users WHERE email = ?", (email,))
    user = cur.fetchone()
    if user:
        user_id, name, email, role, org = user
        cur.execute("SELECT company_name, duration, feedback, msme_digitalized FROM internships WHERE student_id = ?", (user_id,))
        internships = cur.fetchall()
        cur.execute("SELECT project_id, title, description, status FROM projects WHERE student_id = ?", (user_id,))
        projects = cur.fetchall()
        cur.close()
        return {
            "id": user_id,
            "name": name,
            "email": email,
            "role": role,
            "org": org,
            "internships": [{"company_name": i[0], "duration": i[1], "feedback": i[2], "msme_digitalized": i[3]} for i in internships],
            "projects": [{"project_id": p[0], "title": p[1], "description": p[2], "status": p[3]} for p in projects]
        }
    cur.close()
    return None

def log_internship(email, company, duration, feedback, msme_digitalized):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cur.fetchone()
        if not user:
            name = email.split("@")[0].capitalize()
            cur.execute("INSERT INTO users (name, email, role, org) VALUES (?, ?, ?, ?)", (name, email, "student", "Unknown"))
            conn.commit()
            cur.execute("SELECT id FROM users WHERE email = ?", (email,))
            user = cur.fetchone()
        user_id = user[0]
        cur.execute("""
            INSERT INTO internships (student_id, company_name, duration, feedback, msme_digitalized)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, company, duration, feedback, msme_digitalized))
        conn.commit()
        cur.close()
        return True
    except sqlite3.Error:
        cur.close()
        return False

def log_project(student_id, title, description, status):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO projects (student_id, title, description, status) VALUES (?, ?, ?, ?)",
                    (student_id, title, description, status))
        conn.commit()
        cur.close()
        return True
    except sqlite3.Error:
        cur.close()
        return False

def log_query(user_id, prompt, response):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO queries (user_id, prompt, response, timestamp) VALUES (?, ?, ?, ?)",
                    (user_id, prompt, response, datetime.utcnow().isoformat()))
        conn.commit()
        cur.close()
        return True
    except sqlite3.Error:
        cur.close()
        return False

def fetch_metrics(role):
    conn = get_connection()
    cur = conn.cursor()
    try:
        if role == "student":
            cur.execute("SELECT COUNT(*) FROM internships")
            total_internships = cur.fetchone()[0]
            cur.execute("SELECT SUM(msme_digitalized) FROM internships")
            total_msmes = cur.fetchone()[0] or 0
            cur.close()
            return {
                "total_internships": total_internships,
                "total_msmes": total_msmes,
                "certifications_issued": total_internships
            }
        elif role == "college":
            cur.execute("SELECT COUNT(*) FROM users WHERE role = ?", ("student",))
            students = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM projects")
            projects = cur.fetchone()[0]
            cur.close()
            return {
                "students_participating": students,
                "projects_submitted": projects
            }
        elif role == "mentor":
            cur.execute("SELECT COUNT(*) FROM feedback")
            feedback_count = cur.fetchone()[0]
            cur.close()
            return {
                "sessions_conducted": feedback_count,
                "feedback_logged": feedback_count
            }
        elif role == "msme":
            cur.execute("SELECT COUNT(*) FROM projects")
            projects = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT student_id) FROM projects WHERE student_id IS NOT NULL")
            students_matched = cur.fetchone()[0]
            cur.close()
            return {
                "projects_received": projects,
                "students_matched": students_matched
            }
        elif role == "government":
            cur.execute("SELECT COUNT(*) FROM users WHERE role = ?", ("college",))
            colleges = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM internships")
            total_engagement = cur.fetchone()[0]
            cur.close()
            return {
                "colleges_onboarded": colleges,
                "total_engagement": total_engagement
            }
    except sqlite3.Error:
        cur.close()
        return {}
    cur.close()
    return {}

def log_feedback(student_id, rating, comments):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO feedback (student_id, rating, comments) VALUES (?, ?, ?)",
                    (student_id, rating, comments))
        conn.commit()
        cur.close()
        return True
    except sqlite3.Error:
        cur.close()
        return False

def query_kyra_api(prompt):
    return f"Ky'ra response to: {prompt}"

def main():
    # Initialize database
    initialize_database()

    # --- Login Page ---
    st.title("🌟 Welcome to Ky'ra")
    st.markdown("Ky'ra is here to guide your internship journey. Let's begin.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        email = st.text_input("Enter your email", key="login_email")
        role = st.selectbox("Select your role", ["Student", "College", "Mentor", "MSME", "Government"])
        if st.button("Login 🚀"):
            with st.spinner("Verifying your profile..."):
                user_data = fetch_user_data(email)
                if not user_data:
                    name = email.split("@")[0].capitalize()
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO users (name, email, role, org) VALUES (?, ?, ?, ?)",
                                (name, email, role.lower(), "Unknown"))
                    conn.commit()
                    cur.close()
                    user_data = fetch_user_data(email)
                st.session_state.user = user_data
                st.session_state.page = "Dashboard"
                st.rerun()
    
    with col2:
        st.markdown("### Choose Your Journey")
        roles = {
            "Student": "Track your learning and internships.",
            "College": "Monitor student progress.",
            "Mentor": "Guide your mentees.",
            "MSME": "Digitalize your business.",
            "Government": "View regional impact."
        }
        for r, desc in roles.items():
            st.markdown(f"**{r}**: {desc}")

    # --- Dashboard ---
    if hasattr(st.session_state, 'page') and st.session_state.page == "Dashboard" and hasattr(st.session_state, 'user') and st.session_state.user:
        user = st.session_state.user
        role = user["role"]
        
        # Sidebar
        st.sidebar.image("https://via.placeholder.com/150x50?text=Ky'ra+Logo", use_column_width=True)
        st.sidebar.markdown(f"### Hi, {user['name']}!")
        st.sidebar.markdown(f"Role: {role.capitalize()}")
        menu_options = {
            "student": ["Your Progress", "Log Internship", "Upskilling", "Opportunities", "Feedback"],
            "college": ["Student Performance", "Upload Projects"],
            "mentor": ["Guide Students", "Assign Tasks", "Feedback"],
            "msme": ["Project Needs", "Review Interns", "Digitalization Dashboard"],
            "government": ["Regional Impact"]
        }
        choice = st.sidebar.selectbox("Navigate", menu_options.get(role, ["Your Progress"]))
        
        # Main Content
        st.title(f"🌟 Ky'ra: Your {role.capitalize()} Journey")
        st.markdown(f"How can Ky'ra help you today, {user['name']}?")
        
        # Metrics
        metrics = fetch_metrics(role)
        cols = st.columns(3)
        for i, (key, value) in enumerate(metrics.items()):
            with cols[i % 3]:
                st.markdown(f"""
                    <div class="metric-card">
                        <h3>{key.replace('_', ' ').title()}</h3>
                        <p style="font-size: 24px; color: #50C878;">{value}</p>
                    </div>
                """, unsafe_allow_html=True)
        
        # Ky'ra Chatbot
        st.markdown("### Ask Ky'ra")
        prompt = st.text_input("Your question or task", key="kyra_prompt")
        if st.button("Submit to Ky'ra 🤖"):
            with st.spinner("Ky'ra is thinking..."):
                response = query_kyra_api(prompt)
                log_query(user["id"], prompt, response)
                st.success(response)
        
        # Role-Specific Dashboards
        if role == "student":
            if choice == "Your Progress":
                st.header("Your Progress")
                st.markdown("You're doing great! Let's continue.")
                for internship in user["internships"]:
                    st.markdown(f"""
                        <div class="metric-card">
                            <h3>{internship['company_name']}</h3>
                            <p>Duration: {internship['duration']}</p>
                            <p>Feedback: {internship['feedback'] or 'N/A'}</p>
                            <p>MSMEs Digitalized: {internship['msme_digitalized']}</p>
                        </div>
                    """, unsafe_allow_html=True)
            
            elif choice == "Log Internship":
                st.header("🛠️ Log Internship")
                company = st.text_input("Company Name")
                duration = st.text_input("Duration (e.g., 3 months)")
                feedback = st.text_area("Feedback")
                msme_digitalized = st.number_input("MSMEs Digitalized", min_value=0)
                if st.button("Submit Internship"):
                    if company and duration:
                        with st.spinner("Saving your internship..."):
                            success = log_internship(user["email"], company, duration, feedback, msme_digitalized)
                        if success:
                            st.success("Internship logged successfully! 🎉")
                            st.balloons()
                    else:
                        st.error("Please fill in all required fields.")
            
            elif choice == "Upskilling":
                st.header("📚 Upskilling Journey")
                st.markdown("This small step brings you closer to your purpose.")
                course = st.text_input("Enrolled Course")
                hours = st.number_input("Learning Hours Completed", min_value=0)
                project_title = st.text_input("Project Title")
                project_desc = st.text_area("Project Description")
                if st.button("Submit Project"):
                    if course and project_title:
                        log_project(user["id"], project_title, project_desc, "Submitted")
                        st.success("Project submitted successfully!")
            
            elif choice == "Opportunities":
                st.header("🚀 Opportunities")
                st.info("Explore new internships soon!")
            
            elif choice == "Feedback":
                st.header("🗣️ Share Your Feedback")
                rating = st.slider("Rate your experience", 1, 5, 3)
                comments = st.text_area("Comments")
                if st.button("Submit Feedback"):
                    with st.spinner("Submitting feedback..."):
                        if log_feedback(user["id"], rating, comments):
                            st.success("Thanks for your feedback! 🌟")
        
        elif role == "college":
            if choice == "Student Performance":
                st.header("Student Performance")
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT name, email FROM users WHERE role = ?", ("student",))
                students = cur.fetchall()
                cur.close()
                for student in students:
                    st.markdown(f"""
                        <div class="metric-card">
                            <h3>{student[0]}</h3>
                            <p>Email: {student[1]}</p>
                        </div>
                    """, unsafe_allow_html=True)
            
            elif choice == "Upload Projects":
                st.header("Upload Projects")
                title = st.text_input("Project Title")
                desc = st.text_area("Project Description")
                if st.button("Upload Project"):
                    log_project(None, title, desc, "Open")
                    st.success("Project uploaded successfully!")
        
        elif role == "mentor":
            if choice == "Guide Students":
                st.header("Guide Students")
                st.info("Assign tasks and provide feedback soon!")
            
            elif choice == "Assign Tasks":
                st.header("Assign Tasks")
                student_email = st.text_input("Student Email")
                task = st.text_area("Task Description")
                if st.button("Assign Task"):
                    st.success("Task assigned successfully!")
            
            elif choice == "Feedback":
                st.header("Provide Feedback")
                student_email = st.text_input("Student Email")
                rating = st.slider("Rating", 1, 5, 3)
                comments = st.text_area("Comments")
                if st.button("Submit Feedback"):
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM users WHERE email = ?", (student_email,))
                    student = cur.fetchone()
                    if student:
                        log_feedback(student[0], rating, comments)
                        st.success("Feedback submitted!")
                    else:
                        st.error("Student not found.")
                    cur.close()
        
        elif role == "msme":
            if choice == "Project Needs":
                st.header("Submit Project Need")
                title = st.text_input("Project Title")
                desc = st.text_area("Project Description")
                if st.button("Submit Need"):
                    log_project(None, title, desc, "Open")
                    st.success("Project need submitted!")
            
            elif choice == "Review Interns":
                st.header("Review Interns")
                st.info("Review matched interns soon!")
            
            elif choice == "Digitalization Dashboard":
                st.header("Digitalization Dashboard")
                st.markdown("Track your digital transformation progress.")
                website_live = st.checkbox("Website Live")
                crm_setup = st.checkbox("CRM Setup")
                satisfaction = st.slider("Satisfaction Score", 1, 5, 3)
                if st.button("Submit Progress"):
                    st.success("Progress updated!")
        
        elif role == "government":
            if choice == "Regional Impact":
                st.header("Regional Impact")
                st.markdown("View the impact of internships across regions.")
                metrics_data = {"Colleges": metrics.get("colleges_onboarded", 0), "Engagement": metrics.get("total_engagement", 0)}
                st.bar_chart(metrics_data)

if __name__ == "__main__":
    # Initialize session state
    if not hasattr(st.session_state, 'page'):
        st.session_state.page = "Login"
    if not hasattr(st.session_state, 'user'):
        st.session_state.user = None
    main()