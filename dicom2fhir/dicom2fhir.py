import uuid
import os
from fhir import resources as fr
from fhir.resources import fhirtypes
from pydicom import dcmread
from pydicom import dataset
from tqdm import tqdm
import logging

from dicom2fhir import dicom2fhirutils

import sys
add_path = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "../../dicom-fhir-extension/"
    )
)
logging.info(f"Add to $PATH: '{add_path}'")
sys.path.append(add_path)
# dicom-fhir-extension brings ImagingStudySeriesErlangen, ImagingStudyErlangen
from FeasibilityExtension import ImagingStudySeriesErlangen, ImagingStudyErlangen


def _add_imaging_study_instance(
    study: ImagingStudyErlangen,
    series: ImagingStudySeriesErlangen,
    ds: dataset.FileDataset
):
    selectedInstance = None
    instanceUID = ds.SOPInstanceUID
    if series.instance is not None:
        selectedInstance = next(
            (i for i in series.instance if i.uid == instanceUID), None)
    else:
        series.instance = []

    if selectedInstance is not None:
        print("Error: SOP Instance UID is not unique")
        print(selectedInstance.as_json())
        return

    instance_data = {}

    instance_data["uid"] = instanceUID
    instance_data["sopClass"] = dicom2fhirutils.gen_coding(
        value="urn:oid:" + ds.SOPClassUID,
        system=dicom2fhirutils.SOP_CLASS_SYS
    )
    instance_data["number"] = ds.InstanceNumber

    try:
        if series.modality.coding[0].code == "SR":
            seq = ds.ConceptNameCodeSequence
            instance_data["title"] = seq[0x0008, 0x0104]
        else:
            instance_data["title"] = '\\'.join(ds.ImageType)
    except Exception:
        pass  # print("Unable to set instance title")

    # instantiate selected instancee here
    selectedInstance = fr.imagingstudy.ImagingStudySeriesInstance(
        **instance_data)

    series.instance.append(selectedInstance)
    study.numberOfInstances = study.numberOfInstances + 1
    series.numberOfInstances = series.numberOfInstances + 1
    return


def _add_imaging_study_series(study: ImagingStudyErlangen, ds: dataset.FileDataset, fp):

    # inti data container
    series_data = {}

    seriesInstanceUID = ds.SeriesInstanceUID
    # TODO: Add test for studyInstanceUID ... another check to make sure it matches
    selectedSeries = None
    if study.series is not None:
        selectedSeries = next(
            (s for s in study.series if s.uid == seriesInstanceUID), None)
    else:
        study.series = []

    if selectedSeries is not None:
        _add_imaging_study_instance(study, selectedSeries, ds)
        return

    series_data["uid"] = seriesInstanceUID
    try:
        if ds.SeriesDescription != '':
            series_data["description"] = ds.SeriesDescription
    except Exception:
        pass

    series_data["number"] = ds.SeriesNumber
    series_data["numberOfInstances"] = 0

    series_data["modality"] = dicom2fhirutils.gen_codeable_concept(
        value_list=[ds.Modality],
        system=dicom2fhirutils.ACQUISITION_MODALITY_SYS
    )
    dicom2fhirutils.update_study_modality_list(study, series_data["modality"])

    stime = None
    try:
        stime = ds.SeriesTime
    except Exception:
        pass  # print("Series TimeDate is missing")

    try:
        sdate = ds.SeriesDate
        series_data["started"] = dicom2fhirutils.gen_started_datetime(
            sdate, stime)
    except Exception:
        pass  # print("Series Date is missing")

    try:
        series_data["bodySite"] = dicom2fhirutils.gen_bodysite_cr(
            ds.BodyPartExamined)
        dicom2fhirutils.update_study_bodysite_list(
            study, series_data["bodySite"])
    except Exception:
        pass  # print ("Body Part Examined missing")

    try:
        series_data["laterality"] = dicom2fhirutils.gen_coding_text_only(
            ds.Laterality)
        dicom2fhirutils.update_study_laterality_list(
            study, series_data["laterality"])
    except Exception:
        pass  # print ("Laterality missing")

    # TODO: evaluate if we wonat to have inline "performer.actor" for the I am assuming "technician"
    # PerformingPhysicianName	0x81050
    # PerformingPhysicianIdentificationSequence	0x81052

    # extension stuff here
    if series_data["modality"].coding[0].code == "MR":
        try:
            series_data["scanningSequence"] = dicom2fhirutils.gen_coding(
                value=ds[0x0018, 0x0020].value,
                system=dicom2fhirutils.SCANNING_SEQUENCE_SYS
            )
        except Exception:
            pass
        try:
            series_data["scanningVariant"] = dicom2fhirutils.gen_codeable_concept(
                value_list=[ds[0x0018, 0x0021].value],
                system=dicom2fhirutils.SCANNING_VARIANT_SYS
            )
        except Exception:
            pass
        try:
            series_data["echoTime"] = ds[0x0018, 0x0081].value
        except Exception:
            pass

    # Creating New Series
    series = ImagingStudySeriesErlangen(**series_data)

    study.series.append(series)
    study.numberOfSeries = study.numberOfSeries + 1
    _add_imaging_study_instance(study, series, ds)
    return


def _create_imaging_study(ds, fp, dcmDir) -> ImagingStudyErlangen:
    study_data = {}
    study_data["id"] = str(uuid.uuid4())
    study_data["status"] = "available"
    try:
        if ds.StudyDescription != '':
            study_data["description"] = ds.StudyDescription
    except Exception:
        pass  # missing study description

    study_data["identifier"] = []
    study_data["identifier"].append(
        dicom2fhirutils.gen_accession_identifier(ds.AccessionNumber))
    study_data["identifier"].append(
        dicom2fhirutils.gen_studyinstanceuid_identifier(ds.StudyInstanceUID))

    ipid = None
    try:
        ipid = ds.IssuerOfPatientID
    except Exception:
        pass  # print("Issuer of Patient ID is missing")

    study_data["contained"] = []
    patientReference = fhirtypes.ReferenceType()
    patientref = "patient.contained.inline"
    patientReference.reference = "#" + patientref
    study_data["contained"].append(dicom2fhirutils.inline_patient_resource(
        patientref,
        ds.PatientID,
        ipid,
        ds.PatientName,
        ds.PatientSex,
        ds.PatientBirthDate
    ))
    study_data["subject"] = patientReference
    study_data["endpoint"] = []
    endpoint = fhirtypes.ReferenceType()
    endpoint.reference = "file://" + dcmDir

    study_data["endpoint"].append(endpoint)

    procedures = []
    try:
        procedures = dicom2fhirutils.dcm_coded_concept(ds.ProcedureCodeSequence)
    except Exception:
        pass  # procedure code sequence not found

    study_data["procedure"] = dicom2fhirutils.gen_procedurecode_array(
        procedures)

    studyTime = None
    try:
        studyTime = ds.StudyTime
    except Exception:
        pass  # print("Study Date is missing")

    try:
        studyDate = ds.StudyDate
        study_data["started"] = dicom2fhirutils.gen_started_datetime(
            studyDate, studyTime)
    except Exception:
        pass  # print("Study Date is missing")

    # TODO: we can add "inline" referrer
    # TODO: we can add "inline" reading radiologist.. (interpreter)

    reason = None
    reasonStr = None
    try:
        reason = dicom2fhirutils.dcm_coded_concept(
            ds.ReasonForRequestedProcedureCodeSequence)
    except Exception:
        pass  # print("Reason for Request procedure Code Seq is not available")

    try:
        reasonStr = ds.ReasonForTheRequestedProcedure
    except Exception:
        pass  # print ("Reason for Requested procedures not found")

    study_data["reason"] = dicom2fhirutils.gen_reason(reason, reasonStr)

    study_data["numberOfSeries"] = 0
    study_data["numberOfInstances"] = 0

    # instantiate study here, when all required fields are available
    study = ImagingStudyErlangen(**study_data)

    _add_imaging_study_series(study, ds, fp)
    return study


def process_dicom_2_fhir(dcmDir: str) -> ImagingStudyErlangen:
    files = []
    # TODO: subdirectory must be traversed
    for r, d, f in os.walk(dcmDir):
        for file in f:
            files.append(os.path.join(r, file))

    studyInstanceUID = None
    imagingStudy = None
    for fp in tqdm(files):
        try:
            with dcmread(fp, None, [0x7FE00010], force=True, stop_before_pixels=True) as ds:
                if studyInstanceUID is None:
                    studyInstanceUID = ds.StudyInstanceUID
                if studyInstanceUID != ds.StudyInstanceUID:
                    raise Exception(
                        "Incorrect DCM path, more than one study detected")
                if imagingStudy is None:
                    imagingStudy = _create_imaging_study(ds, fp, dcmDir)
                else:
                    _add_imaging_study_series(imagingStudy, ds, fp)
        except Exception as e:
            logging.error(e)
            pass  # file is not a dicom file
    return imagingStudy
