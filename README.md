# 🎓 Student Feedback Portal (Advanced Django System)

A full-featured role-based feedback management system built using Django.
This application enables students to submit structured feedback while providing teachers, HODs, and administrators with detailed analytics and insights.

---

## 🚀 Key Features

### 👨‍🎓 Student

* Submit feedback for subjects (monthly, semester-wise)
* View feedback history with filters (semester & month)
* Track performance trends and progress over time
* Prevent duplicate submissions

### 👨‍🏫 Teacher

* View subject-wise feedback analytics
* Question-wise average ratings
* Student comments for qualitative insights
* Monthly performance trends & improvement tracking

### 🏫 HOD (Head of Department)

* Manage students and teachers within department
* Add/manage subjects and feedback questions
* View department-wide feedback analytics
* Role-based restrictions for secure access

### 🏢 CEO / Admin

* Manage departments and assign HODs
* Create users and assign roles
* View overall system analytics across departments

---

## 🔐 Role-Based Access Control

* Strict access control implemented using user roles
* Protected routes using Django authentication decorators
* Department-level data isolation for HODs
* Superuser support for CEO-level access

---

## 📊 Analytics & Insights

* Monthly and semester-wise feedback tracking
* Performance comparison (current vs previous month)
* Improvement/decline detection using percentage logic
* Weakest topic identification based on lowest ratings
* Aggregated averages using Django ORM (`Avg`, `Count`)

---

## 🛠️ Tech Stack

* Python
* Django
* SQLite (can be extended)
* HTML/CSS (templates)

---

## 🧩 Database Design

* Role-based architecture using Profile model
* Separate StudentProfile and TeacherProfile
* Feedback system:

  * Feedback (per student, subject, month)
  * FeedbackResponse (question-wise ratings)
  * FeedbackQuestion (dynamic questions)

📌 Enforced constraint:

* One feedback per student per subject per month
  (via unique_together)

---

## ⚙️ Core Functional Logic

* Dynamic role-based dashboard redirection
* Secure object-level access (teachers see only their subjects)
* Feedback validation (e.g., mandatory comment for low ratings)
* Query optimization using `select_related` and `prefetch_related`
* Modular architecture for scalability

---

## 📌 Learning Outcomes

* Advanced Django architecture and role management
* Handling complex relational databases
* Implementing analytics using ORM aggregation
* Secure backend development with access control
* Building scalable multi-user systems

---

## 🔮 Future Improvements

* Add authentication UI (login/signup system)
* REST API integration (Django REST Framework)
* Data visualization (charts/graphs)
* Deployment (AWS / Render / Docker)

---

## 👨‍💻 Author

Gaurav
Computer Science Student | Aspiring Cybersecurity Professional
