from sqlalchemy import Enum

class StudentsDBEnums:
    GENDER = Enum('Male', 'Female', name='GENDER')

    CASTE_TYPE = Enum('GENERAL', 'OBC', 'SC', 'ST', name='Caste_Type')

    RELIGION = Enum(
        'Muslim', 'Hindu', 'Christian', 'Sikh',
        'Buddhist', 'Parsi', 'Jain',
        name='RELIGION'
    )

    HOME_DISTANCE = Enum(
        'Less than 1 km', 'Between 1-3 Kms', 'Between 3-5 Kms',
        'More than 5 Kms',
        name='Home_Distance'
    )

    BLOOD_GROUP = Enum(
        'A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-',
        name='BLOOD_GROUP'
    )

    EDUCATION_TYPE = Enum(
        'Primary', 'Upper Primary', 'Secondary or Equivalent',
        'Higher Secondary or Equivalent', 'More than Higher Secondary',
        'No Schooling Experience',
        name='EDUCATION_TYPE'
    )

    FATHERS_OCCUPATION = Enum(
        'Labour', 'Business', 'Shop Owner', 'Private Job', 
        'Government Job', 'Farmer', 'Other',
        name='FATHERS_OCCUPATION'
    )

    MOTHERS_OCCUPATION = Enum(
        'Homemaker', 'Labour',  'Business',  'Shop Owner', 
        'Private Job',  'Government',
        name='MOTHERS_OCCUPATION'
    )