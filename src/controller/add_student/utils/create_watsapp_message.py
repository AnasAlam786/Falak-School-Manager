# src/controller/add_student/create_watsapp_message.py

def watsapp_message(student_data):

    student, session, class_data, school = student_data
    

    message = f"""
        🎉 Admission Confirmed! 🎉

        Dear {student.FATHERS_NAME},

        We are pleased to inform you that the admission of your child has been successfully completed.

        🧑 Student Name: {student.STUDENTS_NAME}
        🏫 Class: {class_data.CLASS}
        🎓 Roll No: {session.ROLL}
        📅 Admission Date: {student.ADMISSION_DATE.strftime('%d-%m-%Y')}

        Welcome to our school family! We look forward to a bright and successful academic journey together. If you have any questions, feel free to contact us.

        Best regards,  
        {school.School_Name}
        📞 {school.Phone}
        """

    # Generate WhatsApp message

    return message