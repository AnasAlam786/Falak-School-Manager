from flask import Flask, render_template_string
import os
from dotenv import load_dotenv
from model import db

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SESSION_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


@app.route('/')
def home():
    page="""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RTE Table</title>
<style>
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 2px;
    box-sizing: border-box;
    font-size: 11px; /* Adjusted for better fitting */
}
table {
    width: 100%; /* Ensure table does not exceed the page width */
    text-align: left;
    border-collapse: collapse;
    table-layout: fixed; /* Ensures columns auto-adjust */
}
th, td {
    border: 1px solid black;
    padding: 2px;
    text-align: center;
    white-space: normal; /* Allow wrapping at natural word boundaries */
    overflow-wrap: break-word; /* Ensures text wraps to the next line */
    word-break: normal; /* Avoid breaking words unless necessary */
}
th {
    font-weight: bold;
    font-size: 9px; /* Slightly smaller header text */
}
.label-cell {
    width: 15%; /* Adjusted width for better layout */
    font-weight: bold;
}
@media print {
    body {
        margin: 2mm;
    }
    table {
        font-size: 11px; /* Smaller font for printed table */
    }
}
</style>


</head>
<body>
    <div>
        <div class="header" style="text-align: center; font-weight: bold; margin-bottom: 10px; font-size: 24px;">
            RTE के अन्तर्गत प्रवेशित बच्चों की सूचना, नगर क्षेत्र मुरादाबाद
        </div>

        <table>
            <tr>
                <td colspan="1" class="label-cell">NAME OF DISTRICT:</td>
                <td colspan="2">MORADABAD</td>
                <td colspan="1" class="label-cell">NAME OF BLOCK:</td>
                <td colspan="2">MORADABAD CITY</td>
            </tr>
            <tr>
                <td class="label-cell">NAME OF SCHOOL WITH ADDRESS:</td>
                <td colspan="5">FALAK PUBLIC SCHOOL, JAYANTIPUR ROAD KARULA MORADABAD</td>
            </tr>
            <tr>
                <td class="label-cell">UDISE CODE OF SCHOOL:</td>
                <td colspan="1">09041404306</td>
                <td class="label-cell">School Manager Name:</td>
                <td>ISRAR AHMAD</td>
                <td class="label-cell">Mobile Number:</td>
                <td>8533998822</td>
            </tr>
            <tr>
                <td class="label-cell">School Account Name:</td>
                <td>FALAK PUBLIC SCHOOL</td>
                <td class="label-cell">Name Of Bank:</td>
                <td>CANARA BANK</td>
                <td class="label-cell">Branch Name:</td>
                <td>PARSVNATH PLAZA, MAJHOLA, MBD</td>
            </tr>
            <tr>
                <td class="label-cell">BOARD OF SCHOOL (CBSE/ICSE/OTHER):</td>
                <td>U.P BOARD</td>
                <td class="label-cell">Account Number:</td>
                <td>120003050001</td>
                <td class="label-cell">IFSC: </td>
                <td>CNRB0018826</td>
            </tr>
            <tr>
                <td class="label-cell">CATEGORY OF SCHOOL:</td>
                <td colspan="2">2 - Primary with Upper Primary</td>
                <td class="label-cell">Fee Per Month:</td>
                <td colspan="2">₹350.00</td>
            </tr>
        </table>

        <table>
            <thead style="text-align: center;">
                <tr style="text-align: center;">
                    <th>Students Name</th>
                    <th>Fathers Name</th>
                    <th style="width: 100px;">Address</th>
                    <th>Mobile No</th>
                    <th>Admission Year</th>
                    <th>कक्षा जिसमे बच्चे का प्रवेश हुआ</th>
                    <th style="width: 45px;">नामांकन पंजिका क्रमांक (S.R)</th>
                    <th>वर्तमान कक्षा</th>
                    <th style="width: 70px;">बच्चे की वर्तमान स्थिति (पढ़ रहा है अथवा ड्रॉप आउट)</th>
                    <th>DOB</th>
                    <th>Gender</th>
                    <th style="width: 70px;">Mothers Name</th>
                    <th>Name Of Act Holder</th>
                    <th>Name of Bank</th>
                    <th>Branch Name</th>
                    <th style="width: 90px;">IFSC Code</th>
                    <th style="width: 100px;">Act Number</th>
                </tr>
            </thead>
            <tbody>
                <!-- Add table rows dynamically here -->
                {% for student in students %}
                <tr>
                    <td>{{ student.STUDENTS_NAME }}</td>
                    <td>{{ student.FATHERS_NAME }}</td>
                    <td>{{ student.ADDRESS }}</td>
                    <td>{{ student.PHONE }}</td>
                    <td>{{ student.ADMISSION_SESSION }}</td>
                    <td>{{ student.ADMISSION_CLASS[0] }}</td>
                    <td>{{ student.SR }}</td>
                    <td>{{ student.CLASS }}</td>
                    <td>STUDYING</td>
                    <td style="white-space: nowrap;">{{ student.DOB }}</td>
                    <td>{{ student.GENDER }}</td>
                    <td>{{ student.MOTHERS_NAME }}</td>
                    <td>{{ student.Free_Scheme["AC Holder"] }}</td>
                    <td>{{ student.Free_Scheme["Bank"] }}</td>
                    <td>{{ student.Free_Scheme["Branch"] }}</td>
                    <td>{{ student.Free_Scheme["IFSC"] }}</td>
                    <td>{{ student.Free_Scheme["AC"] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    return render_template_string(page)

if __name__ == '__main__':
    app.run(debug=True)