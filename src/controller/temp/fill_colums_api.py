# src/controller/temp/temp_page_api.py

from flask import Blueprint, request, jsonify

from src.model.StudentsDB import StudentsDB
from src.model.StudentSessions import StudentSessions
from src.model.ClassData import ClassData
from src import db

from datetime import datetime

from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required



fill_colums_api_bp = Blueprint( 'fill_colums_api_bp',   __name__)



@fill_colums_api_bp.route('/fill_colums_api', methods=["POST"])
@login_required
@permission_required('admission')
def fill_colums_api():

        data = request.form

        id = data.get('student_id')
        SR = data.get('SR')
        
        Admission_Class = data.get('Admission_Class')
        admission_date_str = data.get('ADMISSION_DATE')

        if not SR and not Admission_Class and not admission_date_str:
            return jsonify({"message": "No data provided!"}), 400

        try:

            record = db.session.query(StudentsDB).filter(StudentsDB.id == id).first()

            if record:
                if SR:

                    existing_sr = db.session.query(StudentsDB).filter(
                        StudentsDB.SR == SR,
                        StudentsDB.id != id  # Exclude current record from check
                    ).first()

                    if existing_sr:
                        return jsonify({"message": f"SR already exists for {existing_sr.STUDENTS_NAME}, Admission No: {existing_sr.ADMISSION_NO}"}), 404
                    
                    record.SR = SR

                if admission_date_str:
                    try:
                        ADMISSION_DATE = datetime.strptime(admission_date_str, "%d-%m-%Y").date()
                    except:
                        return jsonify({"message": "Enter a valid admission date"}), 404 
                    
                    record.ADMISSION_DATE = ADMISSION_DATE

                if Admission_Class:                    
                    record.Admission_Class = Admission_Class

                db.session.commit()
                return jsonify({"message": "Data submitted successfully"}), 200
                

            else:
                return jsonify({"message": "Record not found"}), 404
        except Exception as e:
            print(e)
            return jsonify({"message": f"Error: {str(e)}" }), 404 

