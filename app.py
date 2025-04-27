from flask import Flask, render_template, jsonify, request, session, url_for, redirect

from sqlalchemy import func, case, select, or_
from sqlalchemy.orm import aliased
from sqlalchemy import true

from flask_mail import Message, Mail

from werkzeug.security import check_password_hash
from bs4 import BeautifulSoup

import datetime
from dotenv import load_dotenv
import json
import logging
import os
from threading import Thread
import re

from model import *

load_dotenv()
logger = logging.getLogger(__name__)


app = Flask(__name__)
app.jinja_env.globals['getattr'] = getattr
app.config['SECRET_KEY'] = os.getenv('SESSION_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # SMTP server (e.g., Gmail)
app.config['MAIL_PORT'] = 587  # Port for sending emails
app.config['MAIL_USE_TLS'] = True  # Use TLS security
app.config['MAIL_USERNAME'] = os.getenv('EMAIL')  # Your email
app.config['MAIL_PASSWORD'] = os.getenv('PASSWORD')  # Your email password (or App Password)
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL')
mail = Mail(app)

db.init_app(app)

def send_email(subject, std, event, questions):
    with app.app_context():  # Fixes "Working outside of application context" error
        try:
            msg = Message(
                subject=f"Question Paper {subject} {std}",
                recipients=["anasalam702@gmail.com"],
                body=f"{event} {subject} {std}\n\n" + "\n\n".join(json.dumps(q, indent=3) for q in questions)
            )
            mail.send(msg)
            print("✅ Email sent successfully!")
        except Exception as e:
            print("❌ Error sending email:", str(e))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/change_session', methods=["POST"])
def change_session():
    data = request.json
    current_session = data.get('year')
    

    # Validate input
    if not current_session or not str(current_session).isdigit():
        return jsonify({"message": "Invalid session ID"}), 400

    current_session = int(current_session)

    # Fetch all sessions from DB
    sessions_data = Sessions.query.with_entities(
        Sessions.id, Sessions.session, Sessions.current_session
    ).order_by(Sessions.session.asc()).all()

    # Store all session years in the session
    session["all_sessions"] = [s.session for s in sessions_data]

    # Find and set the requested session
    for s in sessions_data:
        if current_session == s.session:
            session["current_session"] = s.session
            session["session_id"] = s.id
            return jsonify({"message": "Session Updated"}), 200

    

    return jsonify({"message": "Session not found"}), 404

    

@app.route('/login', methods=["GET", "POST"])
def login():
    error=None
    
    
    if "email" in session:
        return redirect(url_for('studentsData'))

    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        login_as = "admin"

        session["role"] = login_as

        if login_as=="admin":
            school = Schools.query.filter_by(Email=email).first()

            if school and check_password_hash(school.Password, password):

                class_rows = ClassData.query.filter_by(school_id=school.id).order_by(ClassData.id).all()
                class_dict = {cls.id: cls.CLASS for cls in class_rows}

                sessions = Sessions.query.with_entities(Sessions.id, Sessions.session, Sessions.current_session
                                                        ).order_by(Sessions.session.asc()).all()

                session["all_sessions"] = [sessi.session for sessi in sessions]
                session["school_name"] = school.School_Name
                session["classes"] = class_dict
                session["logo"] = school.Logo
                session["email"] = school.Email
                session["school_id"] = school.id


                # pick out the one where current_session==True (or None if none)
                session_id, current_session = next(
                    ((s.id, s.session) for s in sessions if s.current_session),
                    (None, None)
                )

                session["session_id"]      = session_id
                session["current_session"] = current_session

                return redirect(url_for('studentsData'))
            
            else: error="Wrong email or password"
                
        elif login_as=="teacher":
            dbTeacher = TeachersLogin.query.filter_by(email=email).first()

            if dbTeacher and check_password_hash(dbTeacher.password, password):

                school = Schools.query.filter_by(User=dbTeacher.school_id).first()
                
                session["school_name"] = school.School_Name
                session["classes"] = dbTeacher.Classes
                session["Name"] = dbTeacher.name
                session["logo"] = school.Logo
                session["email"] = dbTeacher.email
                session["school_id"] = school.User
                session["id"] = dbTeacher.id

                return redirect(url_for('studentsData'))
            else: error="Wrong email or password"

    return render_template('login.html', error=error)


@app.route('/logout', methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/tempPagePost', methods=["POST"])
def tempPagePost():

        data = request.form

        id = data.get('student_id')
        SR = data.get('SR')
        
        Admission_Class = data.get('Admission_Class')
        admission_date_str = data.get('ADMISSION_DATE')

        try:

            record = db.session.query(StudentsDB).filter_by(id=id).first()
            if record:
                if SR:
                    record.SR = SR

                if admission_date_str:
                    try:
                        ADMISSION_DATE = datetime.datetime.strptime(admission_date_str, "%d-%m-%Y").date()
                    except:
                        return jsonify({"message": "Enter a valid admission date"}), 404 
                    
                    record.ADMISSION_DATE = ADMISSION_DATE

                if Admission_Class:
                    record.Admission_Class = Admission_Class

                db.session.commit() 
                return jsonify({"message": "Data submitted successfully"}), 200
                

            else:
                return jsonify({"message": "Record not found"}), 404
        except:
            return jsonify({"message": "Error while fetching the student"}), 404 


@app.route('/temp_page', methods=["POST","GET"])
def temp_page():

    if "email" not in session:
        return redirect(url_for('login'))
    
    school_id = session["school_id"]
    current_session = session["session_id"]
    classes = session["classes"]

    StudentRollSession = aliased(StudentSessions)

    current_session_students = db.session.query(StudentsDB) \
        .filter(
            StudentsDB.school_id == school_id,
            StudentsDB.session_id == current_session
        ).subquery()

    data = db.session.query(
        current_session_students.c.id,
        current_session_students.c.STUDENTS_NAME,
        current_session_students.c.FATHERS_NAME,
        current_session_students.c.IMAGE,
        current_session_students.c.ADMISSION_NO,
        current_session_students.c.SR,
        current_session_students.c.ADMISSION_DATE,
        current_session_students.c.Admission_Class,

        StudentRollSession.ROLL,
        ClassData.CLASS,
        ClassData.Section,
    ).outerjoin(
        StudentRollSession, StudentRollSession.student_id == current_session_students.c.id
    ).outerjoin(
        ClassData, StudentRollSession.class_id == ClassData.id
    ).filter(
        db.or_(
            current_session_students.c.Admission_Class == None,
            current_session_students.c.ADMISSION_DATE == None,
            current_session_students.c.SR == None
        )
    ).order_by(
        current_session_students.c.STUDENTS_NAME.asc()  # Or use ADMISSION_NO if desired
    ).all()



    return render_template('temp_update_colum.html',data=data, classes=classes)
      

@app.route('/students', methods=['GET', 'POST'])
def studentsData():
    if not "email" in session:
        return redirect(url_for('login'))

    school_id = session["school_id"]
    current_session = session["session_id"]
    classes = session["classes"]
    

    data = db.session.query(
                        StudentsDB.id, StudentsDB.STUDENTS_NAME,
                        func.to_char(StudentsDB.DOB, 'Dy, DD Month YYYY'),  # Format DOB for PostgreSQL
                        StudentsDB.AADHAAR, StudentsDB.FATHERS_NAME,
                        StudentsDB.PEN, StudentsDB.IMAGE, StudentsDB.PHONE,
                        StudentsDB.Free_Scheme,

                        StudentSessions.ROLL,
                        
                        ClassData.CLASS, ClassData.Section,
                    ).join(
                        StudentSessions, StudentSessions.student_id == StudentsDB.id
                    ).join(
                        ClassData, StudentSessions.class_id == ClassData.id
                    ).filter(
                        StudentsDB.school_id == school_id, 
                        StudentSessions.session_id == current_session
                    ).order_by(
                        ClassData.id.asc(), 
                        ClassData.Section.asc(),  # Sort by section
                        StudentSessions.ROLL.asc()  # Sort by roll number
                    ).all()

    return render_template('students.html',data=data, classes=classes)
    


@app.route('/studentModal', methods=["POST"])
def studentModal():
    data = request.json
    
    student_id = int(data.get('studentId'))
    phone = data.get('phone')  #replace by familyID


    student = db.session.query(
            StudentsDB.id, StudentsDB.STUDENTS_NAME, StudentsDB.AADHAAR,
            StudentsDB.FATHERS_NAME, StudentsDB.MOTHERS_NAME, StudentsDB.PHONE,
            StudentsDB.ADMISSION_NO, StudentsDB.ADDRESS, StudentsDB.HEIGHT,
            StudentsDB.WEIGHT, StudentsDB.CAST, StudentsDB.RELIGION,
            StudentsDB.ADMISSION_DATE, StudentsDB.SR, StudentsDB.IMAGE,
            StudentsDB.GENDER, StudentsDB.PEN, StudentsDB.BLOOD_GROUP,
            StudentsDB.APAAR, StudentsDB.Previous_School_Name, StudentsDB.OCCUPATION,
            func.to_char(StudentsDB.DOB, 'Dy, DD Month YYYY').label('DOB'),
            ClassData.CLASS,  # Get the class name from the ClassData table
            StudentSessions.ROLL
        ).join(
            StudentSessions, StudentSessions.student_id == StudentsDB.id  # Join using the foreign key
        ).join(
            ClassData, StudentSessions.class_id == ClassData.id  # Join using the foreign key
        ).filter(
            StudentsDB.PHONE == phone,
            StudentSessions.session_id == session["session_id"],
        ).order_by(
        case(
            (StudentsDB.id == student_id, 0),  # Place the matched student_id at the top
            else_=1
        )
    ).all()

    if not student:
        return jsonify({"message": "Student not found"}), 404
    
    content = render_template('studentModal.html', student=student)
    return jsonify({"html":str(content)})

@app.route('/getfees', methods=["GET", "POST"])
def getfees():

    if request.method == "POST":
        #Paying Fees
        req = request.json
        id = req.get('studentId')

        if req.get('task') =='update':
            
            months = req.get('months')
            current_date = datetime.datetime.now().strftime("%d-%m-%Y")

            resp = updateFees(id, months=months, date=current_date, extra=None)
            return jsonify({"STATUS": resp})
        
        elif req.get('task') =='get':
            student = StudentsDB.query.filter_by(id=id).first()
            
            data=StudentsDB.query.filter_by(PHONE=student.PHONE).all()
            data=[record.to_dict() for record in data]

            for sibling in data:
                
                Fee = ClassData.query.filter_by(CLASS=sibling["CLASS"]).first().Fee
                sibling["Fee"]=Fee
                sibling["CLASS"] = sibling["CLASS"].split("/")[0]
                            
            monthName =  datetime.datetime.now().strftime("%B")
            monthIndex=list(data[0]["Fees"].keys()).index(monthName)+1

            html = render_template('feesModal.html',data=data,currentMonth=monthIndex)
            soup=BeautifulSoup(html,"lxml")
            content=soup.body.decode_contents()
            
            
            return jsonify({"html":str(content),"data":data})


@app.route('/paper', methods=["GET", "POST"])
def paper():
    if 1:

        if request.method == "POST":
            payload = request.json
            value =  payload.get('value')

            if value=="a4PDF":
                questions =  payload.get('questions')
                event =  payload.get('eventName')
                subject =  payload.get('subject')
                std =  payload.get('std')
                MM =  payload.get('MM')
                hrs =  payload.get('hrs')
                school="Falak Public School"

                #questions = [{"marks": "10", "type": "singleWord", "qText": "Define the following:", "subQuestion": ["India", "France", "Japan", "Germany", "Brazil", "Canada"]},
                            # {"marks": "10", "type": "match", "qText": "Match the following countries with their capitals:", "subQuestion": ["India", "France", "Japan", "Germany", "Brazil", "Canada"], "options": ["New Delhi", "Paris", "Tokyo", "Berlin", "Brasília", "Ottawa"]}, 
                            # {"type": "QnA","marks": "10",  "qText": "Answer the following general knowledge questions:", "subQuestion": ["Who is known as the Father of the Nation in India?", "What is the chemical symbol for water?", "Who wrote 'Pride and Prejudice'?", "What is the highest mountain in the world?", "Which planet is known as the Red Planet?"]}, 
                            # {"type": "fillUp", "qText": "Fill in the blanks:", "marks": "10", "subQuestion": ["The Great Wall of _____ is visible from space.", "The boiling point of water is _____ degrees Celsius.", "Albert Einstein developed the theory of _____", "The largest desert in the world is the _____ Desert.", "Light travels at approximately _____ km/s."]}, 
                            # {"type": "T-F", "marks": "10", "qText": "State whether the following statements are True or False:", "subQuestion": ["The Great Pyramid of Giza is one of the Seven Wonders of the Ancient World.", "The Pacific Ocean is the smallest ocean in the world.", "Mount Everest is in the Himalayas.", "Venus is the hottest planet in the solar system.", "The human body has 206 bones."]}, 
                            # {"type": "mcq", "qText": "Choose the correct options:", "marks": "10", "subQuestion": [{"text": "Which is the largest mammal on Earth?", "options": ["Elephant", "Blue Whale", "Giraffe", "Hippopotamus"]}, 
                            # {"marks": "10", "text": "Which is the closest star to Earth?", "options": ["Proxima Centauri", "Sirius", "Betelgeuse", "Alpha Centauri"]}, {"text": "Which is the longest river in the world?", "options": ["Amazon", "Nile", "Yangtze", "Mississippi"]}, {"text": "Which of the following is a primary color?", "options": ["Red", "Green", "Blue", "Yellow"]}]}, 
                            # {"type": "mcq", "qText": "Science and Technology Questions:", "subQuestion": [{"text": "Who invented the light bulb?", "options": ["Thomas Edison", "Nikola Tesla", "Alexander Graham Bell", "Isaac Newton"]}, {"text": "Which planet has the most moons?", "options": ["Jupiter", "Saturn", "Mars", "Uranus"]}, {"text": "What does CPU stand for?", "options": ["Central Processing Unit", "Computer Power Unit", "Control Panel Unit", "Central Program Unit"]}, {"text": "What is the chemical formula for carbon dioxide?", "options": ["CO2", "H2O", "O2", "C2O"]}]}]

                html = render_template('paper_elements.html',questions=questions, school=school, event=event, subject=subject, std=std,MM=MM, hrs=hrs)
                soup=BeautifulSoup(html,"lxml")
                content = soup.find('div', id=value).decode_contents()

                paper_key = f"{subject}_{std}"

                if 'papers' not in session:
                    session['papers'] = {}

                session["papers"][paper_key] = questions
                session.modified = True


                Thread(target=send_email, args=(subject, std, event, questions)).start()
                return jsonify({"html":str(content)})


            if isinstance(value, int):
                html = render_template('paper_elements.html',index=value)
                soup=BeautifulSoup(html,"lxml")
                content = soup.find('div', id="Question").decode_contents()
                
                return jsonify({"html":str(content)})

            html = render_template('paper_elements.html')
            soup=BeautifulSoup(html,"lxml")
            content = soup.find('div', id=value)
            
            return jsonify({"html":str(content)})
            
        papers = None
        if 'papers' in session:
            papers = session['papers']
        
        return render_template('paper.html', index=1, papers=papers)

    else:
        return redirect(url_for('login'))


def validate_name(name, field_name):
    """
    - Must be non-empty after stripping.
    - Must only contain letters, spaces, hyphens or apostrophes.
    - Length between 2 and 50 characters (adjust as you like).
    """

    if not name or not name.strip():
        return f"{field_name} is required."
    name = name.strip()
    # Regex: start with a letter, then letters/spaces/'/- allowed

    if not re.match(r"^[A-Za-z0-9\s.+-]+$", name):
        return (f"{field_name} must start and end with a letter, and only contain letters, spaces, hyphens or apostrophes.")
    return None  # no error

# 2. Loop + 3. unified validate:
def validate_length( value: any, name: str, *, exact: int | None = None, 
                     min_len: int | None = None, max_len: int | None = None, 
                     allow_empty: bool = False ) -> None:    
    s = (value or "").strip()


    if allow_empty and not s:
        return None
    if not s:
        raise Exception(f"{name} is required.")

    L = len(s)

    if exact is not None and L != exact:
        raise Exception(f"{name} must be exactly {exact} characters (got {L}).")
    if min_len is not None and L < min_len:
        raise Exception(f"{name} must be at least {min_len} characters (got {L}).")
    if max_len is not None and L > max_len:
        raise Exception(f"{name} must be at most {max_len} characters (got {L}).")


@app.route('/addstudent', methods=["GET", "POST"])
def addStudent():
    if not "email" in session:
        return redirect(url_for('login')) 

    if request.method == "POST":
        data = request.get_json()

        password = data["password"]
        image = data['IMAGE']
        data.pop('password', None)
        data.pop('IMAGE', None)

        school_id=session["school_id"]

        if not password:
            return jsonify({"message": "Missing password"}), 400

        # 2) Lookup school
        school = Schools.query.filter_by(id=school_id).first()
        if not school:
            return jsonify({"message": "School not found"}), 404

        # 3) Verify password
        if not check_password_hash(school.Password, password):
            return jsonify({"message": "Wrong password"}), 401

        # 4) Success
        if image:
            folder_id = school.students_image_folder_id
            drive_id = upload_image(image, data["ADMISSION_NO"], folder_id)
            student_data["IMAGE"] = drive_id
            print('Uploaded image Drive ID:', drive_id)

        StudentDB_colums = {column.name for column in StudentsDB.__table__.columns}
        StudentDB_data = {key: value for key, value in data.items() if key in StudentDB_colums}

        StudentsSession_colums = {column.name for column in StudentSessions.__table__.columns}
        StudentsSession_data = {key: value for key, value in data.items() if key in StudentsSession_colums}

        unknown_fields = [key for key in data if key not in StudentDB_colums]


        #handling Date fields
        date_fields = ["DOB", "ADMISSION_DATE"]

        for field in date_fields:
            try:
                value = data[field].replace("/", "-")
                StudentDB_data[field] = datetime.datetime.strptime(value, "%d-%m-%Y").date()
            except ValueError:
                return jsonify({"message": f"Invalid date format for {field}. Expected DD-MM-YYYY or DD/MM/YYYY."}), 400
        #handling Date fields END

        #handling Aadhar fields
        aadhar_fields = ['MOTHERS_AADHAR', 'AADHAAR', 'FATHERS_AADHAR']
        for field in aadhar_fields:
            StudentDB_data[field] = data[field].replace("", "-").replace(""," ")
        #handling Aadhar fields End
        

        
        StudentDB_data["school_id"] = school_id
        StudentDB_data["Admission_Class"] = data["CLASS"]
        StudentDB_data["session_id"] = session["session_id"]


        StudentsSession_data["class_id"] = data["CLASS"]
        StudentsSession_data["session_id"] = session["session_id"]
        StudentsSession_data["created_at"] = StudentDB_data["ADMISSION_DATE"]
        StudentsSession_data["Section"] = data["Section"]
        

        for key, value in StudentDB_data.items():
            if value == "":
                StudentDB_data[key] = None

        for key, value in StudentsSession_data.items():
            if value == "":
                StudentsSession_data[key] = None

        try:
            # Start transaction
            
            new_student = StudentsDB(**StudentDB_data)
            db.session.add(new_student)
            db.session.flush()  # Flush to get new_student.id

            student_session = StudentSessions(
                student_id=new_student.id, 
                **StudentsSession_data
            )
            db.session.add(student_session)

            db.session.commit()  # Commit both together

            return jsonify({"message": "Data submitted successfully"}), 200

        except Exception as e:
            db.session.rollback()  # Undo everything
            print('Error while adding student:', str(e))
            return jsonify({"message": "Failed to add student"}), 500

        
        return jsonify({"message": "Data submitted successfully"}), 200


    classes = session["classes"]
    school_id = session["school_id"]

    PersonalInfo = {
            "STUDENTS_NAME": {"label": "Student Name","type": "text", "required":True},  #True
            "DOB": {"label": "DOB", "type": "text", "required":True},  #True
            "GENDER": {"label": "Gender", "type": "select", "default": "Select Gender", "required":True,    #True
                        "options": {"" : "Select Gender", "Male" : "Male", "Female" : "Female"}},
            "AADHAAR": {"label": "Aadhar", "type": "numeric", "maxlength": 14, "required":True},   #True

            "Caste": {"label": "Caste", "type": "text", "required":False},

            "Caste_Type": {"label": "Caste Type", "type": "select", "default": "Select Caste Type", "required":True,    #True
                        "options": {"" : "Select Caste Type", "OBC" : "OBC", "GENERAL" : "GENERAL", "ST" : "ST", "SC" : "SC"}},
            

            "RELIGION": {"label": "Religion", "type": "select", "default": "Select Religion", "required": True,   #True
                        "options": {"" : "Select Religion", "Muslim" : "Muslim", "Hindu" : "Hindu", "Christian" : "Christian",
                                    "Sikh" : "Sikh","Buddhist" : "Buddhist","Parsi" : "Parsi","Jain" : "Jain"}},

            "Height": {"label": "Height (cm)", "type": "numeric", "maxlength": 3, "required":False},
            "Weight": {"label": "Weight (kg)", "type": "numeric", "maxlength": 3, "required":False},

            "BLOOD_GROUP": {"label": "Blood Group", "type": "select", "default": "Select Blood Group", "required":False,
                            "options": {"" : "Select Blood Group", "A+" : "A+", "A-" : "A-", "B+" : "B+","B-" : "B-",
                                        "O+" : "O+","O-" : "O-","AB+" : "AB+","AB-" : "AB-"}
                            }
        }

    AcademicInfo = {
            "CLASS": {
                    "label": "Class",
                    "type": "select",
                    "options": {"": "Select Class", **classes},
                    "default": "Select Class",
                    "required": True   #True
                },
            "Section": {
                "label": "Section",
                "type": "select",
                "options": {"" : "Select Section", "A" : "A", "B" : "B", "C" : "C", "D" : "D", "E": "E", "F": "F"},
                "default": "Select Section",
                "required" : True    #True
            },
            "ROLL": {"label": "Roll No", "type": "numeric", "required":True},   #True
            "SR": {"label": "SR No.", "type": "numeric", "required":True},   #True
            "ADMISSION_NO": {"label": "Admission No.", "type": "numeric", "required":True},    #True
            "ADMISSION_DATE": {"label": "Admission Date", "type": "text", "required":True},    #True
            "PEN": {"label": "PEN No.", "type": "numeric", "maxlength": 11, "required":False},
            "APAAR": {"label": "APAAR No.", "type": "numeric", "maxlength": 12, "required":False},
            
        }

    GuardianInfo = {
            "FATHERS_NAME": {"label": "Father Name", "type": "text", "required": True},   #True
            "MOTHERS_NAME": {"label": "Mother Name", "type": "text", "required": True},   #True
            "FATHERS_AADHAR": {"label": "Father Aadhar", "type": "numeric", "maxlength": 14, "required":False},
            "MOTHERS_AADHAR": {"label": "Mother Aadhar", "type": "numeric", "maxlength": 14, "required":False},
            "FATHERS_EDUCATION": {
                "label": "Father Qualification",
                "type": "select",
                "options": {
                            "":                "Father Qualification",
                            "High School":     "High School",
                            "Intermediate":    "Intermediate",
                            "Graduate":        "Graduate",
                            "Post Graduate":   "Post Graduate",
                            "Other":           "Other",
                        },
                "default": "Father Qualification",
                "required": True   #True
            },
            "MOTHERS_EDUCATION": {
                "label": "Mother Qualification",
                "type": "select",
                "options": {
                        "":                "Mother Qualification",
                        "High School":     "High School",
                        "Intermediate":    "Intermediate",
                        "Graduate":        "Graduate",
                        "Post Graduate":   "Post Graduate",
                        "Other":           "Other",
                        },
                "default": "Mother Qualification", 
                "required":True   #True
            },
            "FATHERS_OCCUPATION": {
                "label": "Father Occupation",
                "type": "select",
                "options": {
                                "":                   "Father Occupation",
                                "Business":           "Business",
                                "Daily Wage Worker" : "Daily Wage Worker",
                                "Farmer":             "Farmer",
                                "Government Job":     "Government Job",
                                "Private Job":        "Private Job",
                                "Other":              "Other",
                            },
                "default": "Father Occupation", 
                "required": True   #True
            },
            "MOTHERS_OCCUPATION": {
                "label": "Mother Occupation",
                "type": "select",
                "options": {
                                "":                   "Mother Occupation",
                                "Homemaker":          "Homemaker",
                                "Business":           "Business",
                                "Daily Wage Worker" : "Daily Wage Worker",
                                "Farmer":             "Farmer",
                                "Government Job":     "Government Job",
                                "Private Job":        "Private Job",
                                "Other":              "Other",
                            },
                "default": "Mother Occupation", 
                "required": True   #True
            }
        }

    ContactInfo = {
            "ADDRESS": {"label": "Address", "type": "text", "required": True},   #True
            
            
            "PHONE": {"label": "Phone", "type": "numeric", "maxlength": 10, "required":False},   #True
            "ALT_MOBILE": {"label": "Alternate Mobile Number", "type": "numeric", "value": "", "maxlength": 10, "required":False},
            "PIN": {"label": "PIN Code", "type": "numeric", "value": "244001", "maxlength": 6, "required":True},   #True
            "Home_Distance": {
                "label": "School to Home Distance (km)",
                "short_label": "Home Distance",
                "type": "select",
                "options": {"" : "Select Distance", "Less than 1 km" : "Less than 1 km", "1-3 km" : "1-3 km", 
                            "3-5 km" : "3-5 km", "More than 5 km" : "More than 5 km"},
                "default": "Select Distance",
                "required":True
            },
            "EMAIL": {"label": "Email ID", "type": "email", "value": "", "required":False},
        }

    AdditionalInfo = {
            "Previous_School_Marks": {"label": "Previous School Marks", "short_label":"Prv. School Marks", "type": "numeric", "maxlength": 3, "required":False},
            "Previous_School_Attendance": {"label": "Previous School Attendance(%)", "short_label":"Prv. School Attendance", "type": "numeric", "maxlength": 3, "required":False},
            "Previous_School_Name": {"label": "Previous School Name", "short_label":"Prv. School", "type": "text", "required":False},
            "Due_Amount": {"label": "Due Amount (Rs.)", "short_label":"Due", "type": "numeric", "required":False},

            
        }

    #get current date
    current_session_year = str(session["current_session"])[-2:]

    max_sr, max_adm = (
        StudentsDB.query
            .with_entities(
                func.max(StudentsDB.SR).label("max_sr"),
                func.max(StudentsDB.ADMISSION_NO).label("max_adm")
            )
            .filter(
                StudentsDB.school_id == school_id,
            )
            .first()
    )

    if max_sr is None:
        max_sr = 0
    if max_adm is None or str(max_adm)[:2] != current_session_year:
        max_adm = int(current_session_year + "000")
    
    new_adm = max_adm + 1
    new_sr = max_sr + 1

    current_date = datetime.datetime.now().strftime("%d-%m-%Y")
    AcademicInfo["ADMISSION_DATE"]["value"] = current_date

    AcademicInfo["SR"]["value"] = new_sr
    AcademicInfo["ADMISSION_NO"]["value"] = new_adm
    
    return render_template('addStudent.html',PersonalInfo=PersonalInfo, AcademicInfo=AcademicInfo, 
                            GuardianInfo=GuardianInfo, ContactInfo=ContactInfo, AdditionalInfo=AdditionalInfo)
    

from flask import Flask, request, jsonify, session
from sqlalchemy import or_
import datetime

@app.route('/verify_admission', methods=["POST"])
def verify_admission():
    data = request.get_json() or {}

    school_id = session.get('school_id')
    current_session_id = session.get('session_id')

    # Normalize Aadhaar and similar fields safely
    def handle_aadhar(key):
        raw = data.get(key) or ""
        return raw.replace('-', '').replace(' ', '')

    admission_no = data.get('ADMISSION_NO')
    SR = data.get('SR')
    PEN = data.get('PEN')
    APAAR = data.get('APAAR')
    aadhaar = handle_aadhar('AADHAAR')
    faadhar = handle_aadhar('FATHERS_AADHAR')
    maadhar = handle_aadhar('MOTHERS_AADHAR')

    # Mandatory text fields
    mandatory_names = [
        "STUDENTS_NAME", "FATHERS_NAME", "MOTHERS_NAME",
        "Caste_Type", "RELIGION", "ADDRESS", "GENDER",
        "FATHERS_OCCUPATION", "MOTHERS_OCCUPATION",
        "FATHERS_EDUCATION", "MOTHERS_EDUCATION",
        "Home_Distance", "Section"
    ]
    for name in mandatory_names:
        val = data.get(name)
        err = validate_name(val, name.replace('_', ' ').title())
        if err:
            return jsonify({'message': err}), 400

    # Optional text fields
    non_mandatory = ["Blood_Group", "Previous_School", "Email", "Free_Scheme", "Caste"]
    for name in non_mandatory:
        val = data.get(name)
        if not val:
            data[name] = None
        else:
            err = validate_name(val, name.replace('_', ' ').title())
            if err:
                return jsonify({'message': err}), 400

    # Length validations (only ValueError expected)
    try:
        validate_length(aadhaar, "AADHAAR", exact=12)
        validate_length(admission_no, "ADMISSION_NO", exact=5)
        validate_length(data.get("PIN"), "PIN", exact=6)
        validate_length(data.get("PHONE"), "Phone", exact=10)
        validate_length(SR, "SR", min_len=1)
        validate_length(data.get("CLASS"), "CLASS", min_len=1, max_len=2)
        validate_length(data.get("ROLL"), "ROLL", min_len=1)
        validate_length(data.get("Height"), "Height", min_len=2, max_len=3)
        validate_length(data.get("Weight"), "Weight", min_len=2, max_len=3)
        validate_length(APAAR or "", "APAAR", exact=12, allow_empty=True)
        validate_length(PEN or "", "PEN", exact=11, allow_empty=True)
        validate_length(data.get("ALT_MOBILE") or "", "ALT_MOBILE", exact=10, allow_empty=True)
        validate_length(faadhar, "Fathers Aadhar", exact=12, allow_empty=True)
        validate_length(maadhar, "Mothers Aadhar", exact=12, allow_empty=True)
    except ValueError as ve:
        return jsonify({'message': str(ve)}), 400

    # Date-field parsing
    for key in ["DOB", "ADMISSION_DATE"]:
        raw = data.get(key)
        if not raw:
            return jsonify({'message': f"Missing required field: {key}"}), 400
        normalized = raw.replace('/', '-')
        try:
            datetime.datetime.strptime(normalized, "%d-%m-%Y").date()
        except ValueError:
            return jsonify({'message': f"Invalid date format for {key}. Expected DD-MM-YYYY."}), 400

    # Check global conflicts for unique IDs
    global_conflict = StudentsDB.query.filter(
        StudentsDB.school_id == school_id,
        or_(
            StudentsDB.PEN == PEN,
            StudentsDB.APAAR == APAAR,
            StudentsDB.AADHAAR == aadhaar
        )
    ).first()
    if global_conflict:
        return jsonify({'message': 'PEN, APAAR, or AADHAAR is already in use.'}), 400

    # Check within this school
    school_conflict = StudentsDB.query.filter(
        StudentsDB.school_id == school_id,
        or_(
            StudentsDB.SR == SR,
            StudentsDB.ADMISSION_NO == admission_no
        )
    ).first()
    if school_conflict:
        return jsonify({'message': 'SR or Admission No. already exists for this school.'}), 400

    # Ensure class_id, Section, ROLL exist in request
    class_id = data.get('class_id')
    section = data.get('Section')
    roll = data.get('ROLL')
    if not class_id or not section or not roll:
        return jsonify({'message': 'Missing class_id, Section, or ROLL for session check.'}), 400

    # Check current-session conflict
    session_conflict = (
        StudentSessions.query
        .join(StudentsDB, StudentSessions.student_id == StudentsDB.id)
        .filter(
            StudentsDB.school_id == school_id,
            StudentSessions.session_id == current_session_id,
            StudentSessions.class_id == class_id,
            StudentSessions.Section == section,
            StudentSessions.ROLL == roll
        )
        .first()
    )
    if session_conflict:
        return jsonify({'message': 'This class/section/roll is already assigned in the current session.'}), 400

    # If we reach here, all validations passed
    return jsonify({'message': 'Admission details are valid.'}), 200


@app.route('/get_new_roll', methods=["POST"])
def get_new_roll():
    data = request.json
    class_id = data.get('class_id')
    school_id = session["school_id"]
    current_session = session["session_id"]

    # Build subquery to calculate the next available roll number in the next class
    next_roll_query = (
        select(func.coalesce(func.max(StudentSessions.ROLL), 0) + 1)
        .join(StudentsDB, StudentsDB.id == StudentSessions.student_id)
        .where(
            StudentSessions.class_id   == class_id,
            StudentSessions.session_id == current_session,
            StudentsDB.school_id       == school_id
        )
    )
    # next_roll now holds the next available roll (1 if none exist)
    try:
        next_roll: int = db.session.execute(next_roll_query).scalar_one()
    except Exception as e:
        return jsonify({"message": e}), 404


    return jsonify({ "next_roll": next_roll })



@app.route('/already_promoted_student_data', methods=["POST"])
def promoted_single_student_data():
    """
    Fetch a single student's data including promotion details based on
    the previous session data.
    
    Expected JSON payload:
    {
        "promoted_session_id": <id of record in StudentSessions table>
    }
    """

    data = request.get_json()

    # Validate input: ensure required keys exist
    if not data or "studentSessionID" not in data:
        return jsonify({"message": "Missing required parameters."}), 400
    
    try:
        promoted_session_id = int(data.get('studentSessionID'))
    except Exception as e:
        print("Invalid parameter format:", data)
        return jsonify({"message": "Invalid parameter format."}), 400
    
    try:
        #session_data = db.session.query(StudentSessions.student_id).filter_by(id=promoted_session_id).scalar()

        # Create aliases for self-join
        PromotedSession = aliased(StudentSessions)
        PreviousSession = aliased(StudentSessions)
        PreviousClass = aliased(ClassData)

        student_row = db.session.query(
            StudentsDB.id, StudentsDB.STUDENTS_NAME, StudentsDB.IMAGE, 
            StudentsDB.FATHERS_NAME, StudentsDB.PHONE,

            # Promoted (current) session
            ClassData.CLASS.label("promoted_class"),
            PromotedSession.ROLL.label("promoted_roll"),
            PromotedSession.Due_Amount.label("due_amount"),
            PromotedSession.id.label("promoted_session_id"),
            func.to_char(PromotedSession.created_at, 'YYYY-MM-DD').label("promoted_date"),

            # Previous session
            PreviousClass.CLASS.label("CLASS"),
            PreviousSession.ROLL.label("ROLL"),

        ).join(
            PromotedSession, PromotedSession.student_id == StudentsDB.id
        ).join(
            ClassData, PromotedSession.class_id == ClassData.id
        ).join(
            PreviousSession, PreviousSession.student_id == StudentsDB.id
        ).join(
            PreviousClass, PreviousSession.class_id == PreviousClass.id
        ).filter(
            PromotedSession.id == promoted_session_id,
            PreviousSession.id != promoted_session_id  # exclude the current session
        ).limit(1).first()  # get the most recent previous session only
        
    except Exception as error:
        # Log error here if you have a logger configured
        print("Error fetching student data:", error)
        return jsonify({"message": "An error occurred while fetching student data."}), 500

    if student_row is None:
        return jsonify({"message": "Student not found"}), 404

    return jsonify(student_row._asdict()), 200

@app.route('/single_student_data', methods=["POST"])
def single_student_data():
    """
    Fetch a single student's data including promotion details based on
    the previous session data.
    
    Expected JSON payload:
    {
        "studentID": <student_id>,
    }
    """
    data = request.get_json()

    # Validate input: ensure required keys exist
    if not data or "studentID" not in data:
        return jsonify({"message": "Missing required parameters."}), 400
    
    try:
        student_id = int(data.get('studentID'))
    except Exception as e:
        print("Invalid parameter format:", data)
        return jsonify({"message": "Invalid parameter format."}), 400

    # Validate session values exist and are valid integers
    try:
        school_id = session["school_id"]
        current_session_id = int(session["session_id"])
        previous_session = current_session_id - 1
    except (KeyError, ValueError):
        return jsonify({"message": "Session data is missing or corrupted. Please logout and login again!"}), 500


    current_class_id = (
        db.session.query(StudentSessions.class_id)
        .filter(StudentSessions.student_id == student_id,
                StudentSessions.session_id == previous_session)
        .scalar()
    )

    # Calculate the next class id (assumes sequential class ids)
    next_class_id = current_class_id + 1

    # Build subquery to get the next class name
    next_class_subquery = (
        select(ClassData.CLASS)
        .where(ClassData.id == next_class_id)
        .scalar_subquery()
    )

    # Build subquery to calculate the next available roll number in the next class
    next_roll_subquery = (
        select(func.coalesce(func.max(StudentSessions.ROLL), 999) + 1)
        .select_from(StudentsDB)
        .join(StudentSessions)
        .where(
            StudentSessions.class_id == next_class_id,
            StudentsDB.school_id == school_id,
            StudentSessions.session_id == int(current_session_id)
        )
        .scalar_subquery()
    )

    try:
        # Main query to retrieve student's data for the previous session
        student_query = db.session.query(
            StudentsDB.id, StudentsDB.STUDENTS_NAME, 
            StudentsDB.IMAGE, StudentsDB.FATHERS_NAME, StudentsDB.PHONE,
            ClassData.CLASS,
            StudentSessions.ROLL,
            next_class_subquery.label("promoted_class"),
            next_roll_subquery.label("promoted_roll"),

            literal(datetime.date.today().strftime('%Y-%m-%d')).label("promoted_date")
        ).join(
            StudentSessions, StudentSessions.student_id == StudentsDB.id
        ).join(
            ClassData, StudentSessions.class_id == ClassData.id
        ).filter(
            StudentsDB.id == student_id,
            StudentSessions.session_id == previous_session
        )
        
        student_row = student_query.first()
        print("Student Row:", student_row)
    except Exception as error:
        # Log error here if you have a logger configured
        print("Error fetching student data:", error)
        return jsonify({"message": "An error occurred while fetching student data."}), 500

    if student_row is None:
        return jsonify({"message": "Student not found"}), 404

    # Convert SQLAlchemy row object to dictionary and return JSON response
    return jsonify(student_row._asdict()), 200


@app.route('/depromote_student', methods=["POST"])
def depromote_student():
    data = request.json

    if not 'email' in session:
        return jsonify({"message": "Unauthorized access."}), 400

    if not data or "studentSessionID" not in data:
        return jsonify({"message": "Missing required parameters."}), 400

    try:
        student_session_ID = int(data.get('studentSessionID'))
    except Exception as e:
        print("Invalid parameter format:", data)
        return jsonify({"message": "Invalid parameter format."}), 400

    # Check if the student exists in the current session
    student_sesssion = db.session.query(StudentSessions).filter_by(id=student_session_ID).first()
    if not student_sesssion:
        return jsonify({"message": "Student not promoted, cant depromote!"}), 404

    #depromote the student by deleting the record from StudentSessions table
    db.session.delete(student_sesssion)
    db.session.commit()

    return jsonify({"message": "Student successfully depromoted"}), 200

@app.route('/update_promoted_student', methods=["POST"])
def update_promoted_student():

    current_session = session.get("session_id")

    data = request.json
    print("Data received:", data)
    sessionDBid = data.get('IDToPassInEndpoint')
    promoted_roll = data.get('promoted_roll')
    promoted_date = data.get('promoted_date')

    due_amount_input = data.get('due_amount')
    due_amount = None
    if due_amount_input:
        try:
            due_amount = int(due_amount_input)  # Using float to handle decimal values
        except ValueError:
            return jsonify({"message": "Invalid due amount."}), 400


    if not sessionDBid or not promoted_roll or not promoted_date:
        return jsonify({"message": "Missing required parameters."}), 400

    student_session = StudentSessions.query.filter_by(id = sessionDBid).first()
    if not student_session:
        return jsonify({"message": "Student not promoted, Try promoting again!"}), 404

    # Check for existing roll number in the target class and session
    conflict = db.session.query(
        StudentsDB.STUDENTS_NAME,
        ClassData.CLASS
        ).join(
            StudentSessions, StudentSessions.student_id == StudentsDB.id
        ).join(
            ClassData, StudentSessions.class_id == ClassData.id
        ).filter(
            StudentSessions.session_id == current_session,
            StudentSessions.class_id == student_session.class_id,
            StudentSessions.ROLL == promoted_roll,
            StudentSessions.id != student_session.id
        ).first()

    if conflict:
        logger.error("This roll number is already in use: %s", conflict)
        return jsonify({
            "message": f"This roll number is already in use in the target class and session, by {conflict.STUDENTS_NAME} in class {conflict.CLASS}"
        }), 400


    try:
        sessionDBid = int(sessionDBid)
        promoted_roll = int(promoted_roll)
        promoted_date = datetime.datetime.strptime(promoted_date, "%Y-%m-%d").date()

    except (ValueError, TypeError):
        return jsonify({"message": "Invalid parameter format."}), 400

    # Update the StudentSessions table with the new roll number and date
    try:
        if student_session:
            student_session.ROLL = promoted_roll
            student_session.created_at = promoted_date
            student_session.Due_Amount = due_amount  # Optional field
            db.session.commit()
            return jsonify({"message": "Student record updated successfully."}), 200
        else:
            return jsonify({"message": "Student session not found."}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error updating student record."}), 500


@app.route('/promote_student_in_DB', methods=["POST"])
def promote_student_in_DB():
    try:
        current_session = int(session["session_id"])
        classes = session["classes"]
    except (KeyError, ValueError):
        return jsonify({"message": "Session data is missing or corrupted. Please logout and login again!"}), 500
        
    data = request.get_json()
    if not data:
        return jsonify({"message": "Missing JSON payload"}), 400

    required_fields = ["IDToPassInEndpoint", "promoted_roll", "promoted_date"]
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing required parameter: {field}"}), 400

        
    try:
        studentId = int(data.get('IDToPassInEndpoint'))
        promoted_roll = int(data.get('promoted_roll'))
    except (TypeError, ValueError):
        return jsonify({"message": "Student or the promoted roll no is not valid!"}), 404
    

    
    promoted_date = data.get('promoted_date')
    if promoted_date:
        try:
            promoted_date = datetime.datetime.strptime(promoted_date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "Invalid promotion date format. Use 'year-month-day'."}), 400
    else:
        return jsonify({"message": "Please enter promotion date."}), 400



    due_amount_input = data.get('due_amount')
    due_amount = None
    if due_amount_input:
        try:
            due_amount = float(due_amount_input)  # Using float to handle decimal values
        except ValueError:
            return jsonify({"message": "Invalid due amount."}), 400
        

        
    #check if the student exist in previous session.
    student = StudentSessions.query.filter_by(student_id = studentId,
                                              session_id = current_session-1).first()
    if not student:
        return jsonify({"message": "Student not found"}), 404
    
    class_to_promote = student.class_id + 1

    if class_to_promote > len(classes):
        return jsonify({"message": "Student cannot be promoted; maximum class reached."}), 400



    # If an entry exists, reject the request immediately
    already_promoted  = StudentSessions.query.filter_by(
        student_id=studentId,
        session_id=current_session
    ).first()
    if already_promoted:
        return jsonify({"message": "Student already has an entry in this session, promotion not allowed!"}), 400



    # Check for existing roll number in the target class and session
    existing_roll = StudentSessions.query.filter_by(
        session_id=current_session,
        class_id=class_to_promote,
        ROLL=promoted_roll
    ).first()

    if existing_roll:
        return jsonify({"message": "This roll number is already in use in the target class and session."}), 400


    new_session = StudentSessions(
        student_id=studentId,
        session_id=current_session,
        ROLL=promoted_roll,
        class_id=class_to_promote,
        Due_Amount=due_amount,
        created_at=promoted_date
    )
    
    try:
        db.session.add(new_session)
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        return jsonify({"message": "Failed to promote student due to a database error."}), 500

    return jsonify({"message" : "Student Promoted successfully"}), 200


@app.route('/promote_student', methods=["GET", "POST"])
def promoteStudent():
    if not "email" in session:
        return redirect(url_for('login'))

    school_id = session["school_id"]
    classes = db.session.query(
        ClassData.id, ClassData.CLASS
    ).filter_by(
        school_id=school_id
    ).order_by(
        ClassData.id
    ).all()
    return render_template('promote_student.html', classes=classes)

@app.route('/generate_message', methods=["POST"])
def generate_message():
    data = request.json
    student_id = data.get('studentID')

    session_id = session["session_id"]

    if not student_id:
        return jsonify({"message": "Missing student ID"}), 400

    PromotedSession = aliased(StudentSessions)
    PromotedClass = aliased(ClassData)
    PreviousSession = aliased(StudentSessions)
    PreviousClass = aliased(ClassData)

    student_data = db.session.query(
        StudentsDB.STUDENTS_NAME,
        StudentsDB.PHONE,
        PromotedClass.CLASS.label("promoted_class"),
        PromotedSession.ROLL.label("promoted_roll"),
        PromotedSession.Due_Amount,

        func.to_char(PromotedSession.created_at, 'FMDay, DD Mon YYYY').label("promoted_date"),
        PreviousClass.CLASS.label("previous_class"),
    ).join(
        PromotedSession,
        (StudentsDB.id == PromotedSession.student_id) &
        (PromotedSession.session_id == session_id)
    ).join(
        PromotedClass,
        PromotedSession.class_id == PromotedClass.id
    ).outerjoin(
        PreviousSession,
        (StudentsDB.id == PreviousSession.student_id) &
        (PreviousSession.session_id == session_id - 1)
    ).outerjoin(
        PreviousClass,
        PreviousSession.class_id == PreviousClass.id
    ).filter(
        StudentsDB.id == student_id
    ).first()
    school_name = session["school_name"]

    message = f'''🎉 Congratulations,\nहमें ये बताते हुए अत्यंत ख़ुशी हो रही है कि _*{student_data.STUDENTS_NAME}*_ का प्रमोशन Class _*{student_data.previous_class}*_ से Class _*{student_data.promoted_class}*_ में सफलतापूर्वक हो चुका है!\n\n\t✨ नया रोल नंबर: _*{student_data.promoted_roll}*_\n\t⏱️ तारीख: _*{student_data.promoted_date}*_\n\n🙌 आपकी मेहनत रंग लाई! ऐसे ही आगे बढ़ते रहो, चमकते रहो और हम सबका नाम रोशन करते रहो! 🌟'''
            
    if student_data.Due_Amount:
        message += f'''\n\n 💰 शेष बकाया राशि: _*{student_data.Due_Amount}*_ रुपये, कृपया जल्द से जल्द भुगतान करने की कृपा करें। 🙏'''

    message += f'''\n🥳🎊 _*{school_name}*_ कि तरफ से ढेरों बधाइयाँ! 🎊🥳'''

        
    return jsonify({"whatsappMessage": message, "PHONE": student_data.PHONE}), 200


@app.route('/get_prv_year_students', methods=["POST"])
def get_prv_year_students():
    data = request.json
    class_id = data.get('class_id')
    next_class_id = int(class_id)+1

    school_id = session["school_id"]
    current_session = session["session_id"]


    PromotedSession = aliased(StudentSessions)
    promoted_subq = (
        select(
            PromotedSession.student_id,
            PromotedSession.id.label("promoted_session_id"),
            PromotedSession.ROLL.label("promoted_roll"),
            PromotedSession.created_at.label("promoted_date")
        )
        .where(
            PromotedSession.session_id == current_session
        )
        .subquery()
    )


    # Main query with LEFT JOIN to promoted_subq
    data = db.session.query(
        StudentsDB.id,
        StudentsDB.STUDENTS_NAME,
        StudentsDB.ADMISSION_NO,
        StudentsDB.IMAGE,
        StudentsDB.FATHERS_NAME,
        StudentsDB.ADMISSION_DATE,
        ClassData.CLASS.label("previous_class"),
        StudentSessions.ROLL.label("previous_roll"),
        StudentSessions.class_id,

        promoted_subq.c.promoted_roll,
        promoted_subq.c.promoted_date,
        promoted_subq.c.promoted_session_id,

        select(ClassData.CLASS)
            .where(ClassData.id == next_class_id)
            .scalar_subquery()
            .label("next_class")
    ).join(
        StudentSessions, 
        StudentSessions.student_id == StudentsDB.id
    ).join(
        ClassData, 
        StudentSessions.class_id == ClassData.id
    ).outerjoin(  # LEFT JOIN promoted details
        promoted_subq,
        promoted_subq.c.student_id == StudentsDB.id
    ).filter(
        ClassData.id == class_id,
        StudentsDB.school_id == school_id,
        StudentSessions.session_id == current_session - 1  # Previous session
    ).order_by(
        StudentSessions.ROLL
    ).all()

    if not data:
        return jsonify({
            "html": """
            <div class="alert alert-warning text-center" role="alert" style="margin-top: 50px;">
                <h5 class="mb-0">No Students Found</h5>
            </div>
            """
        })
    
    html = render_template('promote_student.html', data=data)
    soup=BeautifulSoup(html,"lxml")
    content=soup.body.find('div',{'id':'StudentData'}).decode_contents()

    return jsonify({"html":str(content)})


@app.route('/updatemarks', methods=["GET", "POST"])
def updatemarks():

    if "email" in session:
        classes = session['classes']
        school_id = session["school_id"]
        
        data = None

        if request.method == "POST":
            payload = request.json

            SUBJECT =  payload.get('subject')
            CLASS = payload.get('class')
            EXAM = payload.get('exam')
            current_session_id = session["session_id"]


            if EXAM == "Attendance":
                data = db.session.query(
                                    StudentSessions.id, StudentsDB.STUDENTS_NAME, ClassData.CLASS, 
                                    StudentSessions.ROLL, StudentSessions.Attendance
                                ).join(
                                    StudentSessions, StudentSessions.student_id == StudentsDB.id  # Join using the foreign key
                                ).join(
                                    ClassData, StudentSessions.class_id == ClassData.id  # Join using the foreign key
                                ).filter(
                                    ClassData.CLASS == CLASS,
                                    StudentsDB.school_id == school_id,
                                    StudentSessions.session_id == current_session_id
                                ).order_by(
                                    StudentSessions.ROLL
                                ).all()
            else:
                data = db.session.query(
                                    StudentsMarks.id, StudentsDB.STUDENTS_NAME, 
                                    ClassData.CLASS, StudentSessions.ROLL, 
                                    getattr(StudentsMarks, EXAM), StudentsMarks.Subject
                                ).join(
                                    StudentSessions, StudentSessions.student_id == StudentsDB.id  # Join using the foreign key
                                ).join(
                                    ClassData, StudentSessions.class_id == ClassData.id  # Join using the foreign key
                                ).join(
                                    StudentsMarks, StudentsMarks.student_id == StudentsDB.id
                                ).filter(
                                    StudentsMarks.Subject == SUBJECT,
                                    ClassData.CLASS == CLASS,
                                    StudentsDB.school_id == school_id,
                                    StudentSessions.session_id == current_session_id
                                ).order_by(
                                    StudentSessions.ROLL
                                ).all()


            html = render_template('updatemarks.html', data=data, EXAM=EXAM)
            soup=BeautifulSoup(html,"lxml")
            content=soup.body.find('div',{'id':'marksTable'}).decode_contents()

            return jsonify({"html":str(content)})
            
        return render_template('updatemarks.html', data=data, classes=classes)

    else:
        return redirect(url_for('login'))
        

@app.route('/update', methods=['POST'])
def update():

    data = request.json

    #subject = data.get('subject')
    exam = data.get('exam')
    score = data.get('value')
    id = data.get('id')


    if exam == "Attendance":
        resp = updateCell(StudentSessions, id, exam, score)
    elif exam in ["FA1","FA2","SA1","SA2"]:
        resp = updateCell(StudentsMarks, id, exam, score)
    else:
        return jsonify({"STATUS": "FAILED"})
    
    return jsonify({"STATUS": resp})


@app.route('/transfer_certificate', methods=['POST', 'GET'])
def TransferCertificate():
    
    if "email" in session:
        data = None

        if request.method == "POST":
            data = request.json
            print(data)

            CLASS = data.get('class')
            school_id = session["school_id"]
            current_session_id = session["session_id"]


            data = db.session.query(
                                    StudentsDB.STUDENTS_NAME, StudentsDB.id, StudentsDB.ADMISSION_DATE,
                                    StudentsDB.FATHERS_NAME, StudentsDB.IMAGE, StudentsDB.ADMISSION_NO,
                                    StudentsDB.Admission_Class, StudentsDB.SR,

                                    ClassData.CLASS, 
                                    StudentSessions.ROLL,
                                    func.to_char(StudentsDB.DOB, 'Day, DD Month YYYY').label('DOB'),
                                ).join(
                                    StudentSessions, StudentSessions.student_id == StudentsDB.id  # Join using the foreign key
                                ).join(
                                    ClassData, StudentSessions.class_id == ClassData.id  # Join using the foreign key
                                ).filter(
                                    StudentSessions.class_id == CLASS,
                                    StudentsDB.school_id == school_id,
                                    StudentSessions.session_id == current_session_id
                                ).order_by(
                                    StudentSessions.ROLL
                                ).all()

            html = render_template('transfer_certificate.html', data=data)
            soup=BeautifulSoup(html,"lxml")
            content=soup.body.find('div',{'id':'StudentData'}).decode_contents()

            return jsonify({"html":str(content)})
        
        else:
            school_id = session["school_id"]
            current_session_id = session["session_id"]

            classes = db.session.query(ClassData.id, ClassData.CLASS)\
                .filter_by(school_id=school_id
                ).order_by(ClassData.id).all()

            return render_template('transfer_certificate.html', classes=classes)
        
    else:
        return redirect(url_for('login'))

@app.route('/tcform', methods=['POST'])
def tcform():

    if "email" in session:

        data = request.json

        student_id = data.get('student_id')
        leaving_reason = data.get('leaving_reason')
        classes = session["classes"]
        current_session_id = session["session_id"]


        student_marks = db.session.query(
            StudentsMarks.Subject,
            StudentsMarks.FA1,
            StudentsMarks.SA1,
            StudentsMarks.FA2,
            StudentsMarks.SA2
        ).filter(
            StudentsMarks.student_id == student_id
        ).all()

        results = []
        grading_subjects = []

        for subject, fa1, sa1, fa2, sa2 in student_marks:
            if subject == "Craft":
                continue

            total = 0
            is_grading = False

            for mark in [fa1, sa1, fa2, sa2]:
                try:
                    total += int(mark)
                except:
                    total = mark  # save grade value (e.g., 'A')
                    is_grading = True
                    break

            entry = {'subject': subject, 'total': total}

            if is_grading:
                grading_subjects.append(entry)
            else:
                results.append(entry)

        results.extend(grading_subjects)

        student = db.session.query(
            StudentsDB.STUDENTS_NAME, StudentsDB.AADHAAR,StudentsDB.SR,
            StudentsDB.FATHERS_NAME, StudentsDB.MOTHERS_NAME, StudentsDB.PHONE,
            StudentsDB.ADMISSION_NO, StudentsDB.ADDRESS, StudentsDB.HEIGHT,
            StudentsDB.WEIGHT, StudentsDB.CAST, StudentsDB.RELIGION,
            StudentsDB.ADMISSION_DATE, StudentsDB.SR, StudentsDB.IMAGE,
            StudentsDB.GENDER, StudentsDB.PEN, StudentsDB.HEIGHT,StudentsDB.WEIGHT,
            StudentsDB.APAAR, StudentsDB.Attendance,
            func.to_char(StudentsDB.DOB, 'Dy, DD Month YYYY').label('DOB'),

            ClassData.CLASS,
            ClassData.id.label("class_id"),
            StudentSessions.ROLL

        ).join(
            StudentSessions, StudentSessions.student_id == StudentsDB.id  # Join using the foreign key
        ).join(
            ClassData, StudentSessions.class_id == ClassData.id  # Join using the foreign key
        ).filter(
            StudentsDB.id == student_id,
            StudentSessions.session_id == current_session_id
        ).first()

        class_id = student.class_id

        if class_id + 1 > len(classes):
            promoted_class = "9th"
        else:
            # Get the next class name based on the class_id
            promoted_class = db.session.query(ClassData.CLASS).filter_by(id=class_id + 1).scalar()

        working_days = 214
        general_conduct = "Very Good"
        school_logo = '1WGhnlEn8v3Xl1KGaPs2iyyaIWQzKBL3w'
        current_date = datetime.datetime.now().strftime("%d-%m-%Y")
        print(results)

        html = render_template('pdf-components/tcform.html', 
                               working_days = working_days, student=student, results=results,
                               general_conduct = general_conduct, school_logo = school_logo,
                               current_date = current_date, leaving_reason=leaving_reason,
                               promoted_class = promoted_class)
        
        return jsonify({"html":str(html)})
    
    else:
        return redirect(url_for('login'))


@app.route('/entrycard')
def entryCard():
    if "email" in session:

        data = StudentData("STUDENTS_NAME","FATHERS_NAME","CLASS","ROLL","DOB","PHONE","IMAGE")

        data = [data[i:i + 4] for i in range(0, len(data), 4)]


        logo="https://lh3.googleusercontent.com/d/1WGhnlEn8v3Xl1KGaPs2iyyaIWQzKBL3w=s200"
        school="FALAK PUBLIC SCHOOL"
        year="2024-25"
        exam="SA2"
        quality = "200"

        return render_template('admit.html', data=data, school=school, year=year, exam=exam, logo=logo,quality=quality)
    else:
        return redirect(url_for('login'))

@app.route('/seatChits')
def seatChits():
    if "email" in session:
        result = StudentData("STUDENTS_NAME","FATHERS_NAME","CLASS","ROLL")
        fitlerData = [row for row in result if row["CLASS"] not in ['Nursery', 'LKG','UKG']]
        data = [fitlerData[i:i + 28] for i in range(0, len(fitlerData), 28)]
        
        return render_template('seatChits.html', data=data)
    else:
        return redirect(url_for('login'))


@app.route('/marks', methods=["GET","POST"])
def report_card():
    if "email" in session:
        Data = None
        school_id = session["school_id"]
        current_session_id = session["session_id"]

        if request.method == "POST":

            task = request.json.get('task')

            if task == 'report_card':

                student_id = request.json.get('id')

                students_obj = StudentsDB.query.with_entities(
                                StudentsDB.STUDENTS_NAME, StudentsDB.PHONE, StudentsDB.id,
                                StudentsDB.FATHERS_NAME, StudentsDB.IMAGE, 
                                StudentsDB.MOTHERS_NAME, StudentsDB.ADDRESS,StudentsDB.GENDER,
                                StudentsDB.PEN, StudentsDB.Attendance,

                                ClassData.Numeric_Subjects,ClassData.Grading_Subjects, 
                                ClassData.exam_format,ClassData.CLASS, 
                                StudentSessions.ROLL,
                                TeachersLogin.Sign,
                                func.to_char(StudentsDB.DOB, 'Day, DD Month YYYY').label('DOB'),
                            ).join(
                                StudentSessions, StudentSessions.student_id == StudentsDB.id  # Join using the foreign key
                            ).join(
                                ClassData, StudentSessions.class_id == ClassData.id  # Join using the foreign key
                            ).join(
                                TeachersLogin, ClassData.id == TeachersLogin.class_id
                            ).filter(
                                StudentsDB.id == student_id,
                                StudentSessions.session_id == current_session_id
                            ).all()
            else:
                CLASS = request.json.get('class')

                students_obj = StudentsDB.query.with_entities(
                                StudentsDB.STUDENTS_NAME, StudentsDB.PHONE,
                                StudentsDB.FATHERS_NAME, StudentsDB.id,
                                ClassData.Numeric_Subjects,ClassData.Grading_Subjects, 
                                ClassData.exam_format, ClassData.CLASS, 
                                StudentSessions.ROLL, 
                            ).join(
                                StudentSessions, StudentSessions.student_id == StudentsDB.id  # Join using the foreign key
                            ).join(
                                ClassData, StudentSessions.class_id == ClassData.id  # Join using the foreign key
                            ).filter(
                                ClassData.CLASS == CLASS,
                                StudentsDB.school_id == school_id,
                                StudentSessions.session_id == current_session_id
                            ).order_by(
                                StudentSessions.ROLL
                            ).all()

            students_ids = [row.id for row in students_obj]
            results = ResultData(students_ids=students_ids, current_session_id = current_session_id)

            Data=[]

            students_dict = {s.id: dict(s._asdict()) for s in students_obj}


            for student_id, student_data in students_dict.items():

                #student_id = 7682
                #student_data ={'STUDENTS_NAME': 'Faiz Raza', 'PHONE': '7866952', 'FATHERS_NAME': 'Ham Raza', 'id': 782, 
                #               'Numeric_Subjects': ['English', 'Hindi', 'Math', 'Urdu', 'SST/EVS', 'Computer', 'GK', 'Deeniyat'], 
                #               'Grading_Subjects': ['Drawing', 'Craft'], 'exam_format': {'FA1': '20', 'SA1': '80', 'FA2': '20', 'SA2': '80'}, 
                #               'CLASS': '2nd', 'ROLL': 201}



                numeric_subjects = student_data['Numeric_Subjects']
                grades_subjects = student_data['Grading_Subjects']
                exam_format = student_data['exam_format']

                FA1_Outof = int(exam_format["FA1"])
                SA1_Outof = int(exam_format["SA1"]) 
                FA1_SA1_Outof = FA1_Outof + SA1_Outof

                FA2_Outof = int(exam_format["FA2"])
                SA2_Outof = int(exam_format["SA2"])
                FA2_SA2_Outof = FA2_Outof + SA2_Outof

                Grand_Total_Outof = FA1_SA1_Outof + FA2_SA2_Outof

                no_of_numeric_subjects = len(numeric_subjects)

                numeric_subjects.append("Total")
                numeric_subjects.append("Percentage")
                Subjects = numeric_subjects + grades_subjects

                student_data["Subjects"] = Subjects

                #Mering Result and Student Data
                student_data.update(results[student_id])


                student_data["Percentage"] = {}

                student_data["Percentage"]["FA1"] = round((float(student_data["Total"]["FA1"]) / (FA1_Outof * no_of_numeric_subjects))  * 100, 1)
                student_data["Percentage"]["FA2"] = round((int(student_data["Total"]["FA2"]) / (FA2_Outof * no_of_numeric_subjects))  * 100, 1)
                student_data["Percentage"]["FA1_SA1_Total"] = round((int(student_data["Total"]["FA1_SA1_Total"]) / (FA1_SA1_Outof * no_of_numeric_subjects))  * 100, 1)
                
                
                student_data["Percentage"]["SA1"] = round((int(student_data["Total"]["SA1"]) / (SA1_Outof * no_of_numeric_subjects)) * 100, 1)
                student_data["Percentage"]["SA2"] = round((int(student_data["Total"]["SA2"]) / (SA2_Outof * no_of_numeric_subjects)) * 100, 1)
                student_data["Percentage"]["FA2_SA2_Total"] = round((int(student_data["Total"]["FA2_SA2_Total"]) / (FA2_SA2_Outof * no_of_numeric_subjects)) * 100, 1)
                                                            
                student_data["Percentage"]["Grand_Total"] = round((int(student_data["Total"]["Grand_Total"]) / (Grand_Total_Outof * no_of_numeric_subjects)) * 100, 1)

                for subject in numeric_subjects:

                    if subject == 'Percentage':
                        continue

                    if subject == 'Total':
                        percentage = int(student_data[subject]["Grand_Total"]) / (Grand_Total_Outof * no_of_numeric_subjects) * 100
                        student_data[subject]["Percentage"] = round(percentage, 1)
                        grade, remark = GetGrade(percentage)

                        student_data[subject]["Grade"] = grade
                        student_data[subject]["Remark"] = remark

                        student_data['Percentage']["Grade"] = grade
                        student_data['Percentage']["Remark"] = remark
                        
                        continue


                    percentage = int(student_data[subject]["Grand_Total"]) / (Grand_Total_Outof) * 100
                    student_data[subject]["Percentage"] = round(percentage, 1)  #subject wise percentage


                    grade, remark = GetGrade(percentage)    # Calculate grade and remark of numerical subjects only based on percentage
                    student_data[subject]["Grade"] = grade
                    student_data[subject]["Remark"] = remark

                #print(student_data)

                Data.append(student_data)

            if task == "report_card":
                principle_sign = '14A_2bL47AwZ9ZZyhxsEpCcB1sfInjhe4'
                html = render_template('pdf-components/tall_result.html', data=Data[0], 
                                       attandance_out_of = '214', principle_sign = principle_sign)
                return jsonify({"html":str(html)})


            html = render_template('showMarks.html', Data=Data)
            soup=BeautifulSoup(html,"lxml")
            content=soup.body.find('div',{'id':'results'}).decode_contents()

            return jsonify({"html":str(content)})
        
            

        else:
            return render_template('showMarks.html', Data=Data)
            
    else:
        return redirect(url_for('login'))



@app.route('/aapar', methods=["GET", "POST"])
def aapar():

    if "email" in session:
        data = StudentData("id","STUDENTS_NAME","ROLL", "FATHERS_NAME","MOTHERS_NAME", "FATHERS_AADHAR", "MOTHERS_AADHAR","CLASS")

        if request.method == "POST":
            payload = request.json

            if payload.get('task')=='pageUpdate':

                CLASS = payload.get('class')

                data = StudentData("id","STUDENTS_NAME","ROLL", "FATHERS_NAME","MOTHERS_NAME","FATHERS_AADHAR", "MOTHERS_AADHAR",class_filter_json = {"CLASS": [CLASS]})
    
                html = render_template('aapar.html', data=data)
                soup=BeautifulSoup(html,"lxml")
                content=soup.body.find('div',{'id':'dataTable'}).decode_contents()

                return jsonify({"html":str(content)})
            
            elif payload.get('task')=='aadhar':
                id=payload.get('id')
                motherID = payload.get('Mother_Aadhar').replace("-","")
                fatherID =  payload.get('Father_Aadhar').replace("-","")
            
                if fatherID and not Verhoeff(fatherID):
                    return {"STATUS": "FAILED"}
                    
                if motherID and not Verhoeff(motherID):
                    return {"STATUS": "FAILED"}
                
                fatherIDResult = updateCell(StudentsDB, id, "FATHERS_AADHAR", fatherID)
                motherIDResult = updateCell(StudentsDB, id, "MOTHERS_AADHAR", motherID)

                if fatherIDResult == "FAILED" or motherIDResult == "FAILED":
                    return {"STATUS": 'FAILED'}
                
                
                return{"STATUS": 'SUCCESS'}
            
        return render_template('aapar.html', data=data)

    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(port=5000, debug=True)
