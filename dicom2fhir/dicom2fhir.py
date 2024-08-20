import uuid
import os
from fhir.resources import R4B as fr
from fhir.resources.R4B import reference
from fhir.resources.R4B import imagingstudy
from fhir.resources.R4B import identifier
from fhir.resources.R4B import extension
from pydicom import dcmread
from pydicom import dataset
from tqdm import tqdm
import logging
import hashlib

from dicom2fhir import dicom2fhirutils
from dicom2fhir import extension_MR
from dicom2fhir import extension_CT
from dicom2fhir import extension_MG_CR_DX
from dicom2fhir import extension_PT_NM
from dicom2fhir import extension_device
from dicom2fhir import extension_contrast
from dicom2fhir import extension_instance
from dicom2fhir import extension_reason

global study_list_modality

study_list_modality = []

def _add_imaging_study_instance(
    study: imagingstudy.ImagingStudy,
    series: imagingstudy.ImagingStudySeries,
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
        if series.modality.code == "SR":
            seq = ds.ConceptNameCodeSequence
            instance_data["title"] = seq[0x0008, 0x0104]
        else:
            instance_data["title"] = '\\'.join(ds.ImageType)
    except Exception:
        pass  # print("Unable to set instance title")

    ########### extension stuff here ##########
    
    instance_extensions = []

    #instance extension
    e_instance = extension_instance.gen_extension(ds)
    instance_extensions.append(e_instance)
    
    instance_data["extension"] = instance_extensions


    # instantiate selected instance here
    selectedInstance = fr.imagingstudy.ImagingStudySeriesInstance(
        **instance_data)

    series.instance.append(selectedInstance)
    study.numberOfInstances = study.numberOfInstances + 1
    series.numberOfInstances = series.numberOfInstances + 1
    return


def _add_imaging_study_series(study: imagingstudy.ImagingStudy, ds: dataset.FileDataset, fp, study_list_modality):

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

    series_data["modality"] = dicom2fhirutils.gen_coding(
        value=ds.Modality,
        system=dicom2fhirutils.ACQUISITION_MODALITY_SYS
    )

    study_list_modality = dicom2fhirutils.update_study_modality_list(study_list_modality, ds.Modality)

    stime = None
    try:
        stime = ds.SeriesTime
    except Exception:
        pass

    try:
        sdate = ds.SeriesDate
        series_data["started"] = dicom2fhirutils.gen_started_datetime(
            sdate, stime)
    except Exception:
        pass

    try:
        series_data["bodySite"] = dicom2fhirutils.gen_bodysite_coding(
            ds.BodyPartExamined)
    except Exception:
        pass

    try:
        series_data["laterality"] = dicom2fhirutils.gen_coding_text_only(
            ds.Laterality)
    except Exception:
        pass 


    ########### extension stuff here ##########
    
    series_extensions = []

    #MR extension
    if series_data["modality"].code == "MR":
        
        e_MR = extension_MR.gen_extension(ds)
        series_extensions.append(e_MR)
    
    #CT extension
    if series_data["modality"].code == "CT":
        
        e_CT = extension_CT.gen_extension(ds)
        series_extensions.append(e_CT)

    #MG CR DX extension
    if (series_data["modality"].code == "MG" or series_data["modality"].code == "CR" or series_data["modality"].code == "DX"):
        
        e_MG_CR_DX = extension_MG_CR_DX.gen_extension(ds)
        series_extensions.append(e_MG_CR_DX)

    #PT NM extension
    if (series_data["modality"].code == "PT" or series_data["modality"].code == "NM"):
        
        e_PT_NM = extension_PT_NM.gen_extension(ds)
        series_extensions.append(e_PT_NM)
    
    #device extension
    e_device = extension_device.gen_extension(ds)
    series_extensions.append(e_device)

    #contrast extension
    e_contrast = extension_contrast.gen_extension(ds)
    series_extensions.append(e_contrast)

    series_data["extension"] = series_extensions

    # Creating New Series
    series = imagingstudy.ImagingStudySeries(**series_data)

    study.series.append(series)
    study.numberOfSeries = study.numberOfSeries + 1
    _add_imaging_study_instance(study, series, ds)
    return


def _create_imaging_study(ds, fp, dcmDir) -> imagingstudy.ImagingStudy:
    study_data = {}
    study_data["id"] = str(uuid.uuid4())
    study_data["status"] = "available" #dicom2fhirutils.gen_coding("available", "http://hl7.org/fhir/ValueSet/imagingstudy-status")
    
    try:
        if ds.StudyDescription != '':
            study_data["description"] = ds.StudyDescription
    except Exception:
        pass

    study_data["identifier"] = []
    study_data["identifier"].append(
        dicom2fhirutils.gen_accession_identifier(ds.AccessionNumber))
    study_data["identifier"].append(
        dicom2fhirutils.gen_studyinstanceuid_identifier(ds.StudyInstanceUID))
    
    patID9 = str(ds.PatientID)[:9]
    patIdentifier = "https://fhir.diz.uk-erlangen.de/identifiers/patient-id|"+patID9
    hashedIdentifier = hashlib.sha256(patIdentifier.encode('utf-8')).hexdigest()
    patientReference = "Patient/"+hashedIdentifier
    patientRef = reference.Reference()
    patientRef.reference = patientReference
    patIdent = identifier.Identifier()
    patIdent.system = "https://fhir.diz.uk-erlangen.de/identifiers/patient-id"
    patIdent.type = dicom2fhirutils.gen_codeable_concept(["MR"],"http://terminology.hl7.org/CodeSystem/v2-0203")
    patIdent.value = patID9
    patientRef.identifier = patIdent
    study_data["subject"] = patientRef

    # study_data["endpoint"] = []
    # endpoint = reference.Reference()
    # endpoint.reference = "file://" + dcmDir
    # study_data["endpoint"].append(endpoint)

    procedures = []
    try:
        procedures = dicom2fhirutils.dcm_coded_concept(ds.ProcedureCodeSequence)
    except Exception:
        pass

    study_data["procedureCode"] = dicom2fhirutils.gen_procedurecode_array(
        procedures)

    studyTime = None
    try:
        studyTime = ds.StudyTime
    except Exception:
        pass

    try:
        studyDate = ds.StudyDate
        study_data["started"] = dicom2fhirutils.gen_started_datetime(
            studyDate, studyTime)
    except Exception:
        pass

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

    study_data["reasonCode"] = dicom2fhirutils.gen_reason(reason, reasonStr)

    study_data["numberOfSeries"] = 0
    study_data["numberOfInstances"] = 0

    study_extensions = []
    
    #reason extension
    e_reason = extension_reason.gen_extension(ds)
    study_extensions.append(e_reason)
    
    study_data["extension"] = study_extensions

    # instantiate study here, when all required fields are available
    study = imagingstudy.ImagingStudy(**study_data)

    _add_imaging_study_series(study, ds, fp, study_list_modality)

    return study


def process_dicom_2_fhir(dcmDir: str) -> imagingstudy.ImagingStudy:
    files = []
    # TODO: subdirectory must be traversed
    for r, d, f in os.walk(dcmDir):
        for file in f:
            files.append(os.path.join(r, file))

    studyInstanceUID = None
    imagingStudy = None
    for fp in tqdm(files):
        try:
            with dcmread(fp, None, [0x7FE00010], force=True) as ds:
                if studyInstanceUID is None:
                    studyInstanceUID = ds.StudyInstanceUID
                if studyInstanceUID != ds.StudyInstanceUID:
                    raise Exception(
                        "Incorrect DCM path, more than one study detected")
                if imagingStudy is None:
                    imagingStudy = _create_imaging_study(ds, fp, dcmDir)
                else:
                    _add_imaging_study_series(imagingStudy, ds, fp, study_list_modality)

                #imagingStudy["modality"] = study_list_modality

        except Exception as e:
            logging.error(e)
            pass  # file is not a dicom file
    return imagingStudy, studyInstanceUID