from flask import Flask, render_template, jsonify, request, session, url_for, redirect
import os
from dotenv import load_dotenv
from werkzeug.security import check_password_hash
from model import *
from bs4 import BeautifulSoup
import datetime
from threading import Thread
from flask_mail import Message, Mail
import json
from sqlalchemy import func



load_dotenv()

app = Flask(__name__)
app.jinja_env.globals['getattr'] = getattr
app.config['SECRET_KEY'] = os.getenv('SESSION_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=50)

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

                session["school_name"] = school.School_Name
                session["classes"] = school.Classes
                session["logo"] = school.Logo
                session["email"] = school.Email
                session["school_id"] = school.id
                session["session_id"] = school.session_id

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


@app.route('/studentModal', methods=["POST"])
def studentModal():
    data = request.json
    
    id = data.get('studentId')
    student = StudentsDB.query.filter_by(id=id).first()

    data=StudentsDB.query.filter_by(PHONE=student.PHONE).all()
    student.CLASS=student.CLASS.split("/")[0]
    
    if student.AADHAAR:
        student.AADHAAR = "-".join(student.AADHAAR[i:i+4] for i in range(0, 12, 4))
    if student.DOB:
        student.DOB = student.DOB.strftime('%a, %d %b %Y')
    if student.ADMISSION_DATE:
        student.ADMISSION_DATE = student.ADMISSION_DATE.strftime('%d %b %Y')  

    student.Siblings=[]
    for record in data:
        if str(record.id) != id:
            student.Siblings.append({"Name":record.STUDENTS_NAME, "Class": record.CLASS.split("/")[0], "Roll": record.ROLL, "id": record.id})


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

            resp=updateFees(id, months=months, date=current_date, extra=None)
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
        
@app.route('/addstudent', methods=["GET", "POST"])
def addStudent():
    if "email" in session:

        if request.method == "POST":
            data = request.form.to_dict()
            password = data["password"]
            image = request.files['IMAGE'].read()
            data.pop('password', None)
            data.pop('image', None)
            print(image)
            school_id=session["school_id"]

            school = Schools.query.filter_by(User=school_id).first()
            if school and check_password_hash(school.Password, password):
                return jsonify({'status': 'SUCCESS', "message": "Student Added Succesfully"})
            else:
                return jsonify({'status': 'FAILED', "message": "Wrong Password"})



        classes = session["classes"]

        PersonalInfo = {
                "STUDENTS_NAME": {"label": "Student Name", "type": "text", "value":"anas alam", "required":False},
                "DOB": {"label": "DOB", "type": "date", "value":"", "required":False},
                "AADHAAR": {"label": "Aadhar", "type": "number",  "maxlength": 14, "required":False},
                "HEIGHT": {"label": "Height", "type": "number", "value":"", "maxlength": 3},
                "WEIGHT": {"label": "Weight", "type": "number", "value":"", "maxlength": 3},

                "GENDER": {"label": "Gender", "type": "select", "default": "Select Gender", "required":True,
                            "options": ["Select Gender", "Male", "Female", "Other"]},

                "CAST": {"label": "Caste", "type": "select", "default": "Select Caste", "required":True,
                            "options": ["Select Caste", "OBC", "GENERAL", "ST", "SC"]},

                "RELIGION": {"label": "Religion", "type": "select", "default": "Select Religion", "required":True,
                            "options": ["Select Religion", "Muslim", "Hindu", "Christian","Sikh","Buddhist","Parsi","Jain"]},

                "BLOOD_GROUP": {"label": "Blood Group", "type": "select", "default": "Select Blood Group", "required":False,
                            "options": ["Select Blood Group", "A+", "A-", "B+","B-","O+","O-","AB+","AB-"]}
            }

        AcademicInfo = {
                "ROLL": {"label": "Roll No", "type": "number", "value": "", "required":True},
                "ADMISSION_NO": {"label": "Admission No.", "type": "number", "value": "", "required":True},
                "PEN": {"label": "PEN No.", "type": "number", "value": "", "required":False},
                "SR": {"label": "SR No.", "type": "number", "value": "", "required":True},
                "APAAR": {"label": "APAAR No.", "type": "number", "value": "", "required":False},
                "CLASS": {
                    "label": "Class",
                    "type": "select",
                    "options": classes,
                    "default": "Select class",
                    "required":True
                },
                "SECTION": {
                    "label": "Section",
                    "type": "select",
                    "options": ["A", "B", "C", "D"],
                    "default": "Select Section",
                    "required":True
                }
            }


        GuardianInfo = {
                "FATHERS_NAME": {"label": "Father Name", "type": "text", "value": "", "required":True},
                "MOTHERS_NAME": {"label": "Mother Name", "type": "text", "value": "", "required":True},
                "FATHERS_AADHAR": {"label": "Father Aadhar", "type": "number", "value": "", "maxlength": 14, "required":False},
                "MOTHERS_AADHAR": {"label": "Mother Aadhar", "type": "number", "value": "", "maxlength": 14, "required":False},
                "FATHERS_EDUCATION": {
                    "label": "Father Qualification",
                    "type": "select",
                    "options": ["High School", "Intermediate", "Graduate", "Post Graduate", "Other"],
                    "default": "Graduate",
                    "required":True
                },
                "MOTHERS_EDUCATION": {
                    "label": "Mother Qualification",
                    "type": "select",
                    "options": ["High School", "Intermediate", "Graduate", "Post Graduate", "Other"],
                    "default": "Graduate", 
                    "required":True
                },
                "FATHERS_OCCUPATION": {
                    "label": "Father Occupation",
                    "type": "select",
                    "options": ["Business", "Daily Wage Worker", "Farmer", "Government Job", "Private Job",   "Other"],
                    "default": "Business", 
                    "required":True
                },
                "MOTHERS_OCCUPATION": {
                    "label": "Mother Occupation",
                    "type": "select",
                    "options": ["Homemaker", "Business", "Daily Wage Worker", "Farmer", "Government Job", "Private Job",   "Other"],
                    "default": "Homemaker", 
                    "required":True
                }
}

        ContactInfo = {
                "ADDRESS": {"label": "Address", "type": "text", "value": "", "required":True},
                "PIN": {"label": "PIN Code", "type": "number", "value": "", "maxlength": 6, "required":True},
                "EMAIL": {"label": "Email ID", "type": "email", "value": "", "required":False},
                "MOBILE": {"label": "Mobile Number", "type": "number", "value": "", "maxlength": 10, "required":True},
                "ALT_MOBILE": {"label": "Alternate Mobile Number", "type": "number", "value": "", "maxlength": 10, "required":False}
            }

        AdditionalInfo = {
                "Previous_Class_Marks": {"label": "Previous Class Marks", "type": "number", "value": "", "maxlength": 3, "required":False},
                "Previous_Class_Attendance": {"label": "Previous Class Attendance (%)", "type": "number", "value": "", "maxlength": 3, "required":False},
                "Previous_School": {"label": "Previous School Name", "type": "text", "value": ""},
                "Home_Distance": {
                    "label": "School to Home Distance (km)",
                    "type": "select",
                    "options": ["Less than 1 km", "1-3 km", "3-5 km", "More than 5 km"],
                    "default": "1-3 km",
                    "required":True
                }
            }
        
        return render_template('addStudent.html',PersonalInfo=PersonalInfo, AcademicInfo=AcademicInfo, 
                               GuardianInfo=GuardianInfo, ContactInfo=ContactInfo, AdditionalInfo=AdditionalInfo)
    else:
        return redirect(url_for('login'))

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


            if EXAM == "Attendance":
                data = StudentsDB.query.with_entities(StudentsDB.STUDENTS_NAME,
                                                        StudentsDB.ROLL,
                                                        StudentsDB.CLASS,
                                                        StudentsDB.id,
                                                        StudentsDB.Attendance
                                                    ).filter(
                                                        StudentsDB.CLASS == CLASS,
                                                        StudentsDB.school_id == school_id
                                                    ).order_by(
                                                        StudentsDB.ROLL
                                                    ).all()
            else:
                data = StudentsMarks.query.with_entities(
                                                    StudentsMarks.student_id,
                                                    StudentsMarks.id,
                                                    StudentsMarks.Subject,
                                                    getattr(StudentsMarks, EXAM),
                                                    StudentsDB.STUDENTS_NAME,
                                                    StudentsDB.ROLL,
                                                    StudentsDB.CLASS
                                                ).join(
                                                    StudentsDB, StudentsMarks.student_id == StudentsDB.id
                                                ).filter(
                                                    StudentsMarks.Subject == SUBJECT,
                                                    StudentsMarks.school_id == school_id,
                                                    StudentsDB.CLASS == CLASS  # Changed from StudentsMarks.student_id.CLASS to StudentsDB.CLASS
                                                ).order_by(
                                                    StudentsDB.ROLL
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
        resp = updateCell(StudentsDB, id, exam, score)
    elif exam in ["FA1","FA2","SA1","SA2"]:
        resp = updateCell(StudentsMarks, id, exam, score)
    else:
        return jsonify({"STATUS": "FAILED"})
    
    return jsonify({"STATUS": resp})

@app.route('/students', methods=['GET', 'POST'])
def studentsData():
    if "email" in session:
        data = StudentData("id","STUDENTS_NAME","DOB","CLASS","ROLL","PHONE","IMAGE","FATHERS_NAME", "AADHAAR")
        """data = StudentsDB.query.with_entities(StudentsDB.STUDENTS_NAME, StudentsDB.DOB, StudentsDB.PHONE, 
                                              StudentsDB.ROLL, StudentsDB.CLASS, StudentsDB.Fees,
                                              StudentsDB.id, StudentsDB.IMAGE,StudentsDB.FATHERS_NAME).all()"""
        for student in data:
            student['DOB'] = student['DOB'].strftime('%d %B %Y')

        
        if request.method == "POST":
            payload = request.json

            CLASS =  payload.get('CLASS')

            if CLASS=="All":
                html = render_template('students.html', data=data)
                soup=BeautifulSoup(html,"lxml")
                content=soup.body.find('div',{'id':'StudentData'}).decode_contents()

                return jsonify({"html":str(content)})

            else:
                data = [row for row in data if row.CLASS == CLASS]

                html = render_template('students.html', data=data)
                soup=BeautifulSoup(html,"lxml")
                content=soup.body.find('div',{'id':'StudentData'}).decode_contents()

                return jsonify({"html":str(content)})


        return render_template('students.html',data=data)
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


"""@app.route('/marks', methods=["GET","POST"])
def marks():
    if "email" in session:
        Data = None

        if request.method == "POST":

            CLASS = request.json.get('class')

            Data = StudentData("STUDENTS_NAME","ROLL","FATHERS_NAME", "FA1", "FA2", "SA1", "SA2", class_filter_json = {"CLASS": [CLASS]})

            for student in Data:
            # Add 'Total' to each FA1, FA2, SA1, and SA2
                for key in ['FA1', 'FA2', 'SA1', 'SA2']:
                    scores = student[key]
                    total = sum(int(value) for value in scores.values() if value.isdigit())
                    scores['Total'] = total

                # Calculate FA1_SA1 (Sum of FA1 and SA1)
                fa1_sa1 = {}
                for subject in student['FA1']:
                    if subject != 'Total':
                        fa1_value = int(student['FA1'].get(subject, 0)) if student['FA1'].get(subject, '').isdigit() else 0
                        sa1_value = int(student['SA1'].get(subject, 0)) if student['SA1'].get(subject, '').isdigit() else 0
                        fa1_sa1[subject] = str(fa1_value + sa1_value)
                fa1_sa1['Total'] = sum(int(value) for value in fa1_sa1.values() if value.isdigit())
                student['FA1_SA1'] = fa1_sa1

                # Calculate FA2_SA2 (Sum of FA2 and SA2)
                fa2_sa2 = {}
                for subject in student['FA2']:
                    if subject != 'Total':
                        fa2_value = int(student['FA2'].get(subject, 0)) if student['FA2'].get(subject, '').isdigit() else 0
                        sa2_value = int(student['SA2'].get(subject, 0)) if student['SA2'].get(subject, '').isdigit() else 0
                        fa2_sa2[subject] = str(fa2_value + sa2_value)
                fa2_sa2['Total'] = sum(int(value) for value in fa2_sa2.values() if value.isdigit())
                student['FA2_SA2'] = fa2_sa2

                # Calculate Grand_Total (Sum of all scores across FA1, FA2, SA1, and SA2)
                grand_total = {}
                for subject in student['FA1']:
                    if subject != 'Total':
                        total_value = sum(
                            int(student[key].get(subject, 0)) if student[key].get(subject, '').isdigit() else 0
                            for key in ['FA1', 'FA2', 'SA1', 'SA2']
                        )
                        grand_total[subject] = str(total_value)
                grand_total['Total'] = sum(int(value) for value in grand_total.values() if value.isdigit())
                student['Grand_Total'] = grand_total

            if CLASS in ["2nd","3rd","4th","5th","6th","7th","8th"]:
                for data in Data:
                    for exam_key in ['FA1', 'FA2', 'SA1', 'SA2', 'FA1_SA1', 'FA2_SA2', 'Grand_Total']:
                        if exam_key in data:
                            exam = data[exam_key]
                            exam['Drawing'] = exam.pop('Drawing', '')  # Move 'Drawing' to the end
                            total = exam.pop('Total', '')  # Remove 'Total'
                            exam['Total'] = total 

            html = render_template('showMarks.html', Data=Data)
            soup=BeautifulSoup(html,"lxml")
            content=soup.body.find('div',{'id':'results'}).decode_contents()

            return jsonify({"html":str(content)})
        
        return render_template('showMarks.html', Data=Data)
    
    else:
        return redirect(url_for('login'))"""

@app.route('/marks', methods=["GET","POST"])
def report_card():
    if "email" in session:
        Data = None
        school_id = session["school_id"]

        if request.method == "POST":

            task = request.json.get('task')

            if task == 'report_card':

                id = request.json.get('id')

                students_obj = StudentsDB.query.with_entities(
                                StudentsDB.STUDENTS_NAME,
                                StudentsDB.ROLL,
                                StudentsDB.PHONE,
                                StudentsDB.id,
                                StudentsDB.CLASS,
                                StudentsDB.FATHERS_NAME,
                                StudentsDB.IMAGE,
                                StudentsDB.MOTHERS_NAME,
                                StudentsDB.ADDRESS,
                                func.to_char(StudentsDB.DOB, 'Day, DD Month YYYY').label('DOB'),
                                StudentsDB.GENDER,
                                StudentsDB.PEN,
                                StudentsDB.Attendance,
                                TeachersLogin.Sign  # Include the Sign column from TeachersLogin
                            ).join(
                                TeachersLogin, StudentsDB.CLASS == TeachersLogin.Classes
                            ).filter(
                                StudentsDB.id == id
                            ).all()
            else:
                CLASS = request.json.get('class')

                students_obj = StudentsDB.query.with_entities(StudentsDB.STUDENTS_NAME,
                                                        StudentsDB.ROLL,
                                                         StudentsDB.PHONE,
                                                        StudentsDB.CLASS,
                                                        StudentsDB.FATHERS_NAME,
                                                        StudentsDB.id,
                                                    ).filter(
                                                        StudentsDB.CLASS == CLASS,
                                                        StudentsDB.school_id == school_id
                                                    ).order_by(
                                                        StudentsDB.ROLL
                                                    ).all()
            

            subjects_data = ClassData.query.with_entities(ClassData.CLASS, ClassData.Numeric_Subjects, 
                                                        ClassData.Grading_Subjects, ClassData.exam_format).filter_by(school_id = school_id).all()
            
            Numeric_Subjects = dict((data.CLASS, data.Numeric_Subjects) for data in subjects_data)
            Grading_Subjects = dict((data.CLASS, data.Grading_Subjects) for data in subjects_data)
            exam_format = subjects_data[0].exam_format

            FA1_Outof = int(exam_format["FA1"])
            SA1_Outof = int(exam_format["SA1"]) 
            FA1_SA1_Outof = FA1_Outof + SA1_Outof

            FA2_Outof = int(exam_format["FA2"])
            SA2_Outof = int(exam_format["SA2"])
            FA2_SA2_Outof = FA2_Outof + SA2_Outof

            Grand_Total_Outof = FA1_SA1_Outof + FA2_SA2_Outof

            students_ids = [row.id for row in students_obj]
            results = ResultData(students_ids=students_ids)

            Data=[]

            students_dict = {s.id: dict(s._asdict()) for s in students_obj}
            for student_id, student_data in students_dict.items():

                Class = student_data["CLASS"]

                numeric_subjects = Numeric_Subjects.get(Class, []).copy()
                grades_subjects = Grading_Subjects.get(Class, [])

                no_of_numeric_subjects = len(numeric_subjects)

                numeric_subjects.append("Total")
                numeric_subjects.append("Percentage")
                Subjects = numeric_subjects + grades_subjects

                student_data["Subjects"] = Subjects

                #Mering Result and Student Data
                #{'id': 7744, 'STUDENTS_NAME': 'Mohd Ahad Khan', 'CLASS': '2nd', 'ROLL': 263, 'FATHERS_NAME': 'Mohd Maksood Khan', ''
                #'Subjects': ['English', 'Hindi', 'Math', 'Urdu', 'SST/EVS', 'Computer', 'GK', 'Deeniyat', 'Total', 'Percentage', 'Drawing', 'Craft'], 
                #'GK': {'FA1': Decimal('19'), 'SA1': ....

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
