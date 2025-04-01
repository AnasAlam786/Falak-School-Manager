from flask import Flask, render_template_string
import os
from dotenv import load_dotenv
from model import db, StudentData

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SESSION_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


@app.route('/')
def home():
    page="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Horizontal A4 Sheet with Pagination</title>
</head>
<body>
    
        <div class="container" style="text-align: center; font-family: Arial, Helvetica, sans-serif;">
        <p style="font-size: 30px; font-weight: bold; margin: 1px 0;">
            <u>Falak Public School, Moradabad  |  UDISE Code - 09041404306</u>
        </p>
        <p style="font-size: 24px; font-weight: bold; margin: 1px 1;">
            आर०टी०ई० के अन्तर्गत शैक्षिक सत्र 2024-25 में नामांकन प्राप्त करने वाले छात्र/छात्रों का विवरण
        </p>
        <p style="font-size: 20px; font-weight: bold; margin: 1px 0;">
            प्रारूप - (क)
        </p>

        <table style="border-collapse: collapse; width: 100%; border: 3px solid black; font-size: 15px;">
            <thead>
                <tr>
                    <th style="border: 3px solid black; padding: 8px; width: 20px;">क्रO संO</th>
                    <th style="border: 3px solid black; padding: 8px; width: 50px;">SR No.</th>
                    <th style="border: 3px solid black; padding: 8px; width: 50px;">रजिस्ट्रेशन सं०</th>
                    <th style="border: 3px solid black; padding: 8px; ">छात्र/छात्रा का नाम</th>
                    <th style="border: 3px solid black; padding: 8px;">पिता का नाम</th>
                    <th style="border: 3px solid black; padding: 8px;">प्रवेश लेने की कक्षा</th>
                    <th style="border: 3px solid black; padding: 8px; width: 150px;">विद्यालय का नाम</th>
                    <th style="border: 3px solid black; padding: 8px;">पोर्टल पर विद्यालय द्वारा डाटा फीड किया गया अथवा नहीं</th>
                    <th style="border: 3px solid black; padding: 8px; width: 120px;">डाटा न फीड किये जाने का कारण</th>
                </tr>
            </thead>
            <tbody>
                {% for student in students %}
                <tr>
                    <td style="border: 3px solid black; padding: 8px;">{{ loop.index }}</td>
                    <td style="border: 3px solid black; padding: 8px;">{{ student.SR }}</td>
                    <td style="border: 3px solid black; padding: 8px;">{{ student.ADMISSION_NO }}</td>
                    <td style="border: 3px solid black; padding: 8px;">{{ student.STUDENTS_NAME }}</td>
                    <td style="border: 3px solid black; padding: 8px;">{{ student.FATHERS_NAME }}</td>
                    <td style="border: 3px solid black; padding: 8px;">{{ student.CLASS }}</td>
                    <td style="border: 3px solid black; padding: 8px;">Falak Public School</td>
                    <td style="border: 3px solid black; padding: 8px;">YES</td>
                    <td style="border: 3px solid black; padding: 8px;">None</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

    </div>
</body>
</html>



    """

    data = StudentData("STUDENTS_NAME","ROLL","SR","DOB","FATHERS_NAME","ADMISSION_DATE","ADMISSION_NO","Free_Scheme","AADHAAR","ADDRESS","CAST","PEN","CLASS")
    #data = sorted(data, key=lambda x: x['ADMISSION_DATE'] or datetime.date.max)

    for entry in data:
        if entry['DOB']:
            entry['DOB'] = entry['DOB'].strftime('%d-%m-%Y')
        if entry['ADMISSION_DATE']:
            entry['ADMISSION_DATE'] = entry['ADMISSION_DATE'].strftime('%d-%m-%Y')
            
    students = [entry for entry in data if entry['Free_Scheme'] != None and entry['Free_Scheme']["Scheme"] == 'RTE']
    print(students)


    return render_template_string(page,students=students)

if __name__ == '__main__':
    app.run(debug=True)