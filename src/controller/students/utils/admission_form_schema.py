from pydantic import BaseModel, Field, EmailStr, constr, conint, ConfigDict, field_validator, model_validator
from typing import Optional, Literal, Any, get_origin, get_args
from enum import Enum as PyEnum

from datetime import date

from .validate_aadhaar import verify_aadhaar
from .str_to_date import str_to_date

from src.model.enums import StudentsDBEnums

# Build Python Enums from SQLAlchemy Enum values for use with Pydantic
def _sanitize_enum_member_name(raw: str) -> str:
    name = ''.join(ch if ch.isalnum() else '_' for ch in str(raw)).upper()
    if name and name[0].isdigit():
        name = f'N_{name}'
    return name or 'EMPTY'

def _build_python_enum(enum_name: str, sa_enum) -> type[PyEnum]:
    members: dict[str, str] = {}
    seen: set[str] = set()
    for idx, value in enumerate(sa_enum.enums):
        base_name = _sanitize_enum_member_name(value)
        name = base_name
        # ensure unique member names in case sanitization collides
        counter = 1
        while name in seen:
            counter += 1
            name = f"{base_name}_{counter}"
        seen.add(name)
        members[name] = value
    return PyEnum(enum_name, members)

GenderEnum = _build_python_enum("GENDER", StudentsDBEnums.GENDER)
CasteTypeEnum = _build_python_enum("Caste_Type", StudentsDBEnums.CASTE_TYPE)
ReligionEnum = _build_python_enum("RELIGION", StudentsDBEnums.RELIGION)
BloodGroupEnum = _build_python_enum("BLOOD_GROUP", StudentsDBEnums.BLOOD_GROUP)
EducationTypeEnum = _build_python_enum("EDUCATION_TYPE", StudentsDBEnums.EDUCATION_TYPE)
FatherOccupationEnum = _build_python_enum("FATHERS_OCCUPATION", StudentsDBEnums.FATHERS_OCCUPATION)
MotherOccupationEnum = _build_python_enum("MOTHERS_OCCUPATION", StudentsDBEnums.MOTHERS_OCCUPATION)
HomeDistanceEnum = _build_python_enum("Home_Distance", StudentsDBEnums.HOME_DISTANCE)

class CleanBaseModel(BaseModel):

    @model_validator(mode="before")
    @classmethod
    def cleaning_data(cls, values: dict[str, Any]) -> dict[str, Any]:
        cleaned_data = {}

        for key, value in values.items():
    
            # Skip cleaning if field is Literal or Enum-typed
            field = cls.model_fields.get(key)

            if field:
                annotation = field.annotation
                origin = get_origin(annotation)

                # Skip Literal[...] as-is
                if origin is Literal:
                    cleaned_data[key] = value
                    continue

                # Skip Enum types, even when wrapped in Optional/Union,
                # but convert empty strings to None for Optional enum fields
                def _is_enum_annotation(ann: Any) -> bool:
                    if isinstance(ann, type) and issubclass(ann, PyEnum):
                        return True
                    inner_origin = get_origin(ann)
                    if inner_origin is not None:
                        for arg in get_args(ann):
                            if isinstance(arg, type) and issubclass(arg, PyEnum):
                                return True
                    return False

                if _is_enum_annotation(annotation):
                    if isinstance(value, str):
                        stripped_value = value.strip()
                        # treat empty selection as None for Optional enum fields
                        if stripped_value == "":
                            cleaned_data[key] = None
                        else:
                            cleaned_data[key] = value
                    else:
                        cleaned_data[key] = value
                    continue

            #updating text fields.
            if isinstance(value, str):
                value = value.strip()

                if value == "":
                    value = None  # empty string becomes None

                elif "email" not in key.lower():
                    value = value.title()

            cleaned_data[key] = value
        
        return cleaned_data
    
    def verified_model_dump(self) -> dict[str, dict[str, Any]]:
        """
        Returns: { field: {value: ..., label: ...}, ... }
        """
        data = self.model_dump()
        config_extra = self.__class__.model_config.get("json_schema_extra", {}) or {}

        result = []
        for field, value in data.items():
            field_meta = config_extra.get(field, {})
            short_label =  field_meta.get("data-short_label")
            # ensure Enum values are serialized to their raw value
            if isinstance(value, PyEnum):
                value_out = value.value
            else:
                value_out = value

            result.append({
                "field": field,
                "value": value_out,
                "label": short_label
            })

        return result


# ------------------------- Personal Info -------------------------
class PersonalInfoModel(CleanBaseModel):
    
    STUDENTS_NAME: constr(pattern=r'^[^\W\d_]+(?: [^\W\d_]+)*$') = Field(...) # type: ignore
    
    DOB: date = Field(...)
    GENDER: GenderEnum = Field(...)
    AADHAAR: Optional[constr(min_length=12, max_length=12)] = Field(default=None) # type: ignore
    Caste: Optional[str] = Field(None)
    Caste_Type: CasteTypeEnum = Field(...)

    RELIGION: ReligionEnum = Field(...)

    Height: Optional[conint(gt=0, lt=300)] = Field(None) # type: ignore
    Weight: Optional[conint(gt=0, lt=300)] = Field(None) # type: ignore

    BLOOD_GROUP: Optional[BloodGroupEnum] = Field(None)
    
    # --- Aadaar validators ---
    @field_validator('AADHAAR', mode='before')
    @classmethod
    def clean_aadhaar(cls, v):
        if not v:
            return None
        
        validated_clean_aaadhar = verify_aadhaar(v)
        return validated_clean_aaadhar
    
    # --- date validators ---
    @field_validator('DOB', mode='before')
    @classmethod
    def date_normalization(cls, v):
        if not v:
            return None
        
        date = str_to_date(v)
        return date
    

    class Config:
        json_schema_extra = {
            "STUDENTS_NAME": {
                "id": "STUDENTS_NAME", "type": "text", "inputmode": "text",
                "label": "Student's Name", "data-short_label": "Name", "placeholder": "",
                "required": True, "data-description": "Full name of the student",
                "name": "STUDENTS_NAME"
            },

            "DOB": {
                "id": "DOB", "type": "numeric", "label": "Date of Birth", "placeholder": "",
                "data-short_label": "DOB", "required": True, "data-description": "Date of Birth of the student",
                "name": "DOB"
            },

            "GENDER": {
                "id": "GENDER", "type": "select", "value": "Select Gender",
                "data-short_label": "Gender", "required": True,
                "options": {"": "Select Gender", **{e: e for e in StudentsDBEnums.GENDER.enums}},
                "data-description": "Select the Gender of student",
                "name": "GENDER"
            },

            "AADHAAR": {
                "id": "AADHAAR", "type": "text", "label": "Aadhar Number", "placeholder": "",
                "data-short_label": "Aadhar", "maxlength": 14,
                "data-description": "AADHAAR Number of the student",
                "name": "AADHAAR"
            },

            "Caste": {
                "id": "Caste", "type": "text", "label": "Caste", "placeholder": "",
                "data-short_label": "Caste", "data-description": "Caste of the student",
                "name": "Caste"
            },

            "Caste_Type": {
                "id": "Caste_Type", "type": "select",
                "value": "Select Caste Type",
                "data-short_label": "Caste Type", "required": True,
                "options": {"": "Select Caste Type", **{e: e for e in StudentsDBEnums.CASTE_TYPE.enums}},
                "data-description": "Select the Caste Type of student",
                "name": "Caste_Type"
            },

            "RELIGION": {
                "id": "RELIGION", "type": "select", "value": "Select Religion",
                "data-short_label": "Religion", "required": True,
                "options": {"": "Select Religion", **{e: e for e in StudentsDBEnums.RELIGION.enums}},
                "data-description": "Select the Religion of student",
                "name": "RELIGION"
            },

            "Height": {
                "id": "Height", "type": "numeric", "label": "Height (cm)", "placeholder": "",
                "data-short_label": "Height", "maxlength": 3,
                "data-description": "Height of the student in centimeters",
                "name": "Height"
            },

            "Weight": {
                "id": "Weight", "type": "numeric", "label": "Weight (kg)", "placeholder": "",
                "data-short_label": "Weight", "maxlength": 3,
                "data-description": "Weight of the student in kilograms",
                "name": "Weight"
            },

            "BLOOD_GROUP": {
                "id": "BLOOD_GROUP", "type": "select", "value": "Select Blood Group",
                "data-short_label": "Blood Group",
                "options": {"": "Select Blood Group", **{e: e for e in StudentsDBEnums.BLOOD_GROUP.enums}},
                "data-description": "Select the Blood Group of student",
                "name": "BLOOD_GROUP"
            }
        }



# ------------------------- Academic Info -------------------------
class AcademicInfoModel(CleanBaseModel):
    CLASS: str = Field(...)
    Section: Literal["A", "B", "C", "D", "E", "F"] = Field(...)
    ROLL: conint(gt=0) = Field(...) # type: ignore
    SR: conint(gt=0) = Field(...) # type: ignore
    ADMISSION_NO: conint(gt=0) = Field(...) # type: ignore
    ADMISSION_DATE: date = Field(...)
    PEN: Optional[constr(max_length=11, min_length=11)] = Field(None) # type: ignore
    APAAR: Optional[constr(max_length=12, min_length=12)] = Field(None) # type: ignore

    @field_validator('ADMISSION_DATE', mode='before')
    @classmethod
    def date_normalization(cls, v):
        if not v:
            return None
        
        date = str_to_date(v)
        return date
    

    class Config:
        json_schema_extra = {
            "CLASS": {
                "id": "CLASS", "type": "select", "value": "Select Class",
                "data-short_label": "Class", "options": {}, 
                "required": True, "data-description": "Select the class",
                "name": "CLASS"
            },
            "Section": {
                "id": "Section", "type": "select", "value": "Select Section",
                "data-short_label": "Section", "options": {
                    "": "Select Section", "A": "A", "B": "B", "C": "C",
                    "D": "D", "E": "E", "F": "F"
                },
                "required": True, "data-description": "Select the section",
                "name": "Section"
            },
            "ROLL": {
                "id": "ROLL", "type": "numeric", "label": "Roll No", "placeholder": "",
                "data-short_label": "Roll", "required": True, "data-description": "Roll number of the student",
                "name": "ROLL"
            },
            "SR": {
                "id": "SR", "type": "numeric", "label": "SR No.", "placeholder": "",
                "data-short_label": "SR", "required": True, "data-description": "School Register number",
                "name": "SR"
            },
            "ADMISSION_NO": {
                "id": "ADMISSION_NO", "type": "numeric", "label": "Admission No.", "placeholder": "",
                "data-short_label": "Admi. No", "required": True, "data-description": "Admission number of the student",
                "name": "ADMISSION_NO"
            },
            "ADMISSION_DATE": {
                "id": "ADMISSION_DATE", "type": "date", "label": "Admission Date",
                "data-short_label": "Admi. Date", "required": True, "placeholder": "",
                "data-description": "Date of admission (YYYY-MM-DD)",
                "name": "ADMISSION_DATE"
            },
            "PEN": {
                "id": "PEN", "type": "numeric", "label": "PEN No.", "placeholder": "",
                "data-short_label": "PEN", "maxlength": 11,
                "data-description": "Permanent Education Number (optional)",
                "name": "PEN"
            },
            "APAAR": {
                "id": "APAAR", "type": "numeric", "label": "APAAR No.", "placeholder": "",
                "data-short_label": "AAPAR", "maxlength": 12,
                "data-description": "APAAR Number (optional)",
                "name": "APAAR"
            }
        }

# ------------------------- Guardian Info -------------------------
class GuardianInfoModel(CleanBaseModel):
    FATHERS_NAME: constr(pattern=r'^[^\W\d_]+(?: [^\W\d_]+)*$') = Field(...) # type: ignore
    MOTHERS_NAME: constr(pattern=r'^[^\W\d_]+(?: [^\W\d_]+)*$') = Field(...) # type: ignore
    FATHERS_AADHAR: Optional[constr(max_length=12, min_length=12)] = Field(None) # type: ignore
    MOTHERS_AADHAR: Optional[constr(max_length=12, min_length=12)] = Field(None) # type: ignore
    
    FATHERS_EDUCATION: EducationTypeEnum = Field(...)

    FATHERS_OCCUPATION: FatherOccupationEnum = Field(...)

    MOTHERS_EDUCATION: Optional[EducationTypeEnum] = Field(None)

    MOTHERS_OCCUPATION: Optional[MotherOccupationEnum] = Field(None)

    # --- Field validators ---
    @field_validator('FATHERS_AADHAR', 'MOTHERS_AADHAR', mode='before')
    @classmethod
    def clean_aadhaar(cls, v):
        if not v:
            return None
        
        validated_clean_aaadhar = verify_aadhaar(v)
        return validated_clean_aaadhar


    class Config:
        json_schema_extra = {
            "FATHERS_NAME": {
                "id": "FATHERS_NAME", "type": "text", "label": "Father Name", "placeholder": "",
                "data-short_label": "Father", "required": True, "data-description": "Full name of the father",
                "name": "FATHERS_NAME"
            },
            "MOTHERS_NAME": {
                "id": "MOTHERS_NAME", "type": "text", "label": "Mother Name", "placeholder": "",
                "data-short_label": "Mother", "required": True, "data-description": "Full name of the mother",
                "name": "MOTHERS_NAME"
            },
            "FATHERS_AADHAR": {
                "id": "FATHERS_AADHAR", "type": "numeric", "label": "Father Aadhar",
                "data-short_label": "Father Aadhar", "maxlength": 14,
                "data-description": "Aadhar number of the father", "placeholder": "",
                "name": "FATHERS_AADHAR"
            },
            "MOTHERS_AADHAR": {
                "id": "MOTHERS_AADHAR", "type": "numeric", "label": "Mother Aadhar",
                "data-short_label": "Mother Aadhar", "maxlength": 14,
                "data-description": "Aadhar number of the mother", "placeholder": "",
                "name": "MOTHERS_AADHAR"
            },
            "FATHERS_EDUCATION": {
                "id": "FATHERS_EDUCATION", "type": "select", "value": "Select Father Qualification",
                "data-short_label": "Father Edu.", "required": True,
                "options": {"": "Select Father's Qualification", **{e: e for e in StudentsDBEnums.EDUCATION_TYPE.enums}},
                "data-description": "Education qualification of the father",
                "name": "FATHERS_EDUCATION"
            },
            "FATHERS_OCCUPATION": {
                "id": "FATHERS_OCCUPATION", "type": "select", "value": "Select Father Occupation",
                "data-short_label": "F Occupation", "required": True,
                "options": {"": "Select Father's Occupation", **{e: e for e in StudentsDBEnums.FATHERS_OCCUPATION.enums}},
                "data-description": "Occupation of the father",
                "name": "FATHERS_OCCUPATION"
            },
            "MOTHERS_EDUCATION": {
                "id": "MOTHERS_EDUCATION", "type": "select", "value": "Select Mother Qualification",
                "data-short_label": "Mother Edu.",
                "options": {"": "Select Mother's Qualification", **{e: e for e in StudentsDBEnums.EDUCATION_TYPE.enums}},
                "data-description": "Education qualification of the mother",
                "name": "MOTHERS_EDUCATION"
            },
            "MOTHERS_OCCUPATION": {
                "id": "MOTHERS_OCCUPATION", "type": "select", "value": "Select Mother Occupation",
                "data-short_label": "M Occupation",
                "options": {"": "Select Mother's Occupation", **{e: e for e in StudentsDBEnums.MOTHERS_OCCUPATION.enums}},
                "data-description": "Occupation of the mother",
                "name": "MOTHERS_OCCUPATION"
            }
        }

class ContactInfoModel(CleanBaseModel):
    ADDRESS: str = Field(...) # type: ignore
    PHONE: Optional[constr(min_length=10, max_length=10)] = Field(...) # type: ignore
    ALT_MOBILE: Optional[constr(min_length=10, max_length=10)] = Field(None) # type: ignore
    PIN: constr(min_length=6, max_length=6) = Field(...) # type: ignore
    Home_Distance: Optional[HomeDistanceEnum] = Field(default=None)
    EMAIL: Optional[EmailStr] = Field(None)

    class Config:
        json_schema_extra = {
            "ADDRESS": {
                "id": "ADDRESS", "name": "ADDRESS",
                "label": "Home Address", "data-short_label": "Address",
                "type": "text", "required": True,
                "data-description": "Complete home address", "placeholder": ""
            },
            "PHONE": {
                "id": "PHONE", "name": "PHONE",
                "label": "Phone no.", "data-short_label": "Phone",
                "type": "numeric", "maxlength": 10, "required": True,
                "data-description": "Primary contact number", "placeholder": ""
            },
            "ALT_MOBILE": {
                "id": "ALT_MOBILE", "name": "ALT_MOBILE",
                "label": "Alternate Mobile Number", "data-short_label": "Alt Mobile",
                "type": "numeric", "maxlength": 10,
                "data-description": "Alternate contact number", "placeholder": ""
            },
            "PIN": {
                "id": "PIN", "name": "PIN",
                "label": "PIN Code", "data-short_label": "PIN",
                "type": "numeric", "maxlength": 6, "required": True,
                "data-description": "6-digit area postal code", "placeholder": ""
            },
            "Home_Distance": {
                "id": "Home_Distance", "name": "Home_Distance",
                "value": "Select Home Distance", "data-short_label": "Home Distance",
                "type": "select",
                "options": {"": "Select Home Distance", **{e: e for e in StudentsDBEnums.HOME_DISTANCE.enums}},
                "data-description": "Distance from school to student's home (km)"
            },
            "EMAIL": {
                "id": "EMAIL", "name": "EMAIL",
                "label": "Email ID", "data-short_label": "Email",
                "type": "email", "placeholder": "",
                "data-description": "Email address (optional)"
            }
        }


class AdditionalInfoModel(CleanBaseModel):
    Previous_School_Marks: Optional[constr(max_length=3)] = Field(None) # type: ignore
    Previous_School_Attendance: Optional[constr(max_length=3)] = Field(None) # type: ignore
    Previous_School_Name: Optional[constr(min_length=2)] = Field(None) # type: ignore
    Due_Amount: Optional[float] = Field(None)

    class Config:
        json_schema_extra = {
            "Previous_School_Marks": {
                "id": "Previous_School_Marks", "name": "Previous_School_Marks",
                "label": "Previous School Marks(%)",
                "data-short_label": "Prv. School Marks",
                "type": "numeric", "placeholder": "",
                "maxlength": 3,
                "data-description": "Marks obtained in previous school in percentage"
            },
            "Previous_School_Attendance": {
                "id": "Previous_School_Attendance", "name": "Previous_School_Attendance",
                "label": "Previous School Attendance(%)",
                "data-short_label": "Prv. School Attendance",
                "type": "numeric", "placeholder": "",
                "maxlength": 3,
                "data-description": "Previous school attendance in percentage"
            },
            "Previous_School_Name": {
                "id": "Previous_School_Name", "name": "Previous_School_Name",
                "label": "Previous School Name",
                "data-short_label": "Prv. School",
                "type": "text", "placeholder": "",
                "data-description": "Name of the previous school attended"
            },
            "Due_Amount": {
                "id": "Due_Amount", "name": "Due_Amount",
                "label": "Due Amount (Rs.)",
                "data-short_label": "Due",
                "type": "numeric", "placeholder": "",
                "data-description": "Enter if any due fees remains"
            }
        }


# ------------------------- Full Admission Form -------------------------
class AdmissionFormModel(BaseModel):
    model_config = ConfigDict(extra='ignore')

    personal: PersonalInfoModel
    academic: AcademicInfoModel
    guardian: GuardianInfoModel
    contact: ContactInfoModel
    additional: AdditionalInfoModel
