from datetime import datetime, date

from fhir.resources import imagingstudy
from fhir.resources import identifier
from fhir.resources import codeableconcept
from fhir.resources import codeablereference
from fhir.resources import coding
from fhir.resources import patient
from fhir.resources import humanname
from fhir.resources import fhirtypes
from fhir.resources import reference
import pandas as pd

TERMINOLOGY_CODING_SYS = "http://terminology.hl7.org/CodeSystem/v2-0203"
TERMINOLOGY_CODING_SYS_CODE_ACCESSION = "ACSN"
TERMINOLOGY_CODING_SYS_CODE_MRN = "MR"

ACQUISITION_MODALITY_SYS = "http://dicom.nema.org/resources/ontology/DCM"
SCANNING_SEQUENCE_SYS = "https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.3.html"
SCANNING_VARIANT_SYS = "https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.3.html"

SOP_CLASS_SYS = "urn:ietf:rfc:3986"

def get_mapping_table(url):

    df = pd.read_html(url)
    
    df[2].to_csv('mapping_dicom_snomed.csv', index=False)

    mapping = pd.read_csv("./mapping_dicom_snomed.csv")

    return mapping

def get_snomed(dicom_bodypart, df):

    index = int(df[df['Body Part Examined']==dicom_bodypart].index[0])
    code_snomed = df.at[index, 'Code Value']

    return int(code_snomed)


def gen_accession_identifier(id):
    idf = identifier.Identifier()
    idf.use = "usual"
    idf.type = codeableconcept.CodeableConcept()
    idf.type.coding = []
    acsn = coding.Coding()
    acsn.system = TERMINOLOGY_CODING_SYS
    acsn.code = TERMINOLOGY_CODING_SYS_CODE_ACCESSION

    idf.type.coding.append(acsn)
    idf.value = id
    return idf


def gen_studyinstanceuid_identifier(id):
    idf = identifier.Identifier()
    idf.system = "urn:dicom:uid"
    idf.value = "urn:oid:" + id
    return idf


def get_patient_resource_ids(PatientID, IssuerOfPatientID):
    idf = identifier.Identifier()
    idf.use = "usual"
    idf.value = PatientID

    idf.type = codeableconcept.CodeableConcept()
    idf.type.coding = []
    id_coding = coding.Coding()
    id_coding.system = TERMINOLOGY_CODING_SYS
    id_coding.code = TERMINOLOGY_CODING_SYS_CODE_MRN
    idf.type.coding.append(id_coding)

    if IssuerOfPatientID is not None:
        idf.assigner = reference.Reference()
        idf.assigner.display = IssuerOfPatientID

    return idf


def calc_gender(gender):
    if gender is None:
        return "unknown"
    if not gender:
        return "unknown"
    if gender.upper().lower() == "f":
        return "female"
    if gender.upper().lower() == "m":
        return "male"
    if gender.upper().lower() == "o":
        return "other"

    return "unknown"


def calc_dob(dicom_dob):
    if dicom_dob == '':
        return None

    try:
        dob = datetime.strptime(dicom_dob, '%Y%m%d')
        fhir_dob = fhirtypes.Date(
            dob.year,
            dob.month,
            dob.day
        )
    except Exception:
        return None
    return fhir_dob


def inline_patient_resource(referenceId, PatientID, IssuerOfPatientID, patientName, gender, dob):
    p = patient.Patient()
    p.id = referenceId
    p.name = []
    # p.use = "official"
    p.identifier = [get_patient_resource_ids(PatientID, IssuerOfPatientID)]
    hn = humanname.HumanName()
    hn.family = patientName.family_name
    if patientName.given_name != '':
        hn.given = [patientName.given_name]
    p.name.append(hn)
    p.gender = calc_gender(gender)
    p.birthDate = calc_dob(dob)
    p.active = True
    return p


def gen_procedurecode_array(procedures):
    if procedures is None:
        return None
    fhir_proc = []
    for p in procedures:
        concept = codeableconcept.CodeableConcept()
        c = coding.Coding()
        c.system = p["system"]
        c.code = p["code"]
        c.display = p["display"]
        concept.coding = []
        concept.coding.append(c)
        concept.text = p["display"]
        fhir_proc.append(concept)
    if len(fhir_proc) > 0:
        return fhir_proc
    return None


def gen_started_datetime(dt, tm):
    if dt is None:
        return None

    dt_pattern = '%Y%m%d'

    if tm is not None and len(tm) >= 6:
        studytm = datetime.strptime(tm[0:6], '%H%M%S')

        dt_string = dt + " " + str(studytm.hour) + ":" + \
            str(studytm.minute) + ":" + str(studytm.second)
        dt_pattern = dt_pattern + " %H:%M:%S"
    else:
        dt_string = dt

    dt_date = datetime.strptime(dt_string, dt_pattern)

    # strangely, providing the datetime.date object does not work
    fhirDtm = fhirtypes.DateTime(
        dt_date.year,
        dt_date.month,
        dt_date.day,
        dt_date.hour,
        dt_date.minute,
        dt_date.second
    )

    return fhirDtm


def gen_reason(reason, reasonStr):
    if reason is None and reasonStr is None:
        return None
    reasonList = []
    if reason is None or len(reason) <= 0:
        rc = codeableconcept.CodeableConcept()
        rc.text = reasonStr
        reasonList.append(rc)
        return reasonList

    for r in reason:
        rc = codeableconcept.CodeableConcept()
        rc.coding = []
        c = coding.Coding()
        c.system = r["system"]
        c.code = r["code"]
        c.display = r["display"]
        rc.coding.append(c)
        reasonList.append(rc)
    return reasonList


def gen_coding(value, system):
    c = coding.Coding()
    c.system = system
    c.code = value
    return c


def gen_codeable_concept(value_list: list, system):
    c = codeableconcept.CodeableConcept()
    c.coding = []
    for _l in value_list:
        m = gen_coding(_l, system)
        c.coding.append(m)
    return c


def gen_bodysite_cr(bd):

    bd_snomed = get_snomed(bd, df=mapping_table)
    c = codeablereference.CodeableReference()
    c.concept = gen_codeable_concept(
        value_list=[bd_snomed],
        system="http://snomed.info/sct"
    )
    return c


def update_study_modality_list(study: imagingstudy.ImagingStudy, modality: coding.Coding):
    if study.modality is None or len(study.modality) <= 0:
        study.modality = []
        study.modality.append(modality)
        return

    c = next((mc for mc in study.modality if
              mc.coding[0].system == modality.coding[0].system and
              mc.coding[0].code == modality.coding[0].code), None)
    if c is not None:
        return

    study.modality.append(modality)
    return


def update_study_bodysite_list(study: imagingstudy.ImagingStudy, bodysite: codeablereference.CodeableReference):
    if study.bodySite__ext is None or len(study.bodySite__ext) <= 0:
        study.bodySite__ext = []
        study.bodySite__ext.append(bodysite)
        return

    c = next((mc for mc in study.bodySite__ext if
              mc.conecpt.coding[0].system == bodysite.conecpt.coding[0].system and
              mc.conecpt.coding[0].code == bodysite.conecpt.coding[0].code), None)
    if c is not None:
        return

    study.bodySite__ext.append(bodysite)
    return


def update_study_laterality_list(study: imagingstudy.ImagingStudy, laterality: codeableconcept.CodeableConcept):
    if study.laterality__ext is None or len(study.laterality__ext) <= 0:
        study.laterality__ext = []
        study.laterality__ext.append(laterality)
        return

    c = next((mc for mc in study.laterality__ext if
              mc.coding[0].system == laterality.coding[0].system and
              mc.coding[0].code == laterality.coding[0].code), None)
    if c is not None:
        return

    study.laterality__ext.append(laterality)
    return


def gen_coding_text_only(text):
    c = coding.Coding()
    c.code = text
    c.userSelected = True
    return c


def dcm_coded_concept(CodeSequence):
    concepts = []
    for seq in CodeSequence:
        concept = {}
        concept["code"] = seq[0x0008, 0x0100].value
        concept["system"] = seq[0x0008, 0x0102].value
        concept["display"] = seq[0x0008, 0x0104].value
        concepts.append(concept)
    return concepts

# get mapping table
mapping_table = get_mapping_table("https://dicom.nema.org/medical/dicom/current/output/chtml/part16/chapter_L.html")
