import uuid
import os
from fhir.resources import R4B as fr
from fhir.resources.R4B import reference
from fhir.resources.R4B import imagingstudy
from fhir.resources.R4B import identifier
from fhir.resources.R4B import meta
from pydicom import dcmread
from pydicom import dataset
from tqdm import tqdm
import logging
import hashlib

from dicom2fhir import dicom2fhirutils
from dicom2fhir import extension_MR
from dicom2fhir import extension_CT
from dicom2fhir import extension_MG_CR_DX
from dicom2fhir import extension_PT
from dicom2fhir import extension_NM
from dicom2fhir import extension_contrast
from dicom2fhir import extension_instance
from dicom2fhir import extension_reason

from dicom2fhir import create_device


# global list for all distinct series modalities
study_list_modality_global = []
devices_list_global = []


def _add_imaging_study_instance(
    study: imagingstudy.ImagingStudy,
    series: imagingstudy.ImagingStudySeries,
    ds: dataset.FileDataset,
    include_instances
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

    ########### extension stuff here ##########

    instance_extensions = []

    # instance extension
    e_instance = extension_instance.gen_extension(ds)
    if e_instance is not None:
        instance_extensions.append(e_instance)

    instance_data["extension"] = instance_extensions

    # instantiate selected instance here
    selectedInstance = fr.imagingstudy.ImagingStudySeriesInstance(
        **instance_data)

    if include_instances:
        series.instance.append(selectedInstance)
    study.numberOfInstances = study.numberOfInstances + 1
    series.numberOfInstances = series.numberOfInstances + 1
    return


def _add_imaging_study_series(study: imagingstudy.ImagingStudy, ds: dataset.FileDataset, fp, include_instances):

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
        _add_imaging_study_instance(
            study, selectedSeries, ds, include_instances)
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

    global study_list_modality_global
    study_list_modality_global = dicom2fhirutils.update_study_modality_list(
        study_list_modality_global, ds.Modality)

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

    # MR extension
    if series_data["modality"].code == "MR":

        e_MR = extension_MR.gen_extension(ds)
        if e_MR is not None:
            series_extensions.append(e_MR)

    # CT extension
    if series_data["modality"].code == "CT":

        e_CT = extension_CT.gen_extension(ds)
        if e_CT is not None:
            series_extensions.append(e_CT)

    # MG CR DX extension
    if (series_data["modality"].code == "MG" or series_data["modality"].code == "CR" or series_data["modality"].code == "DX"):

        e_MG_CR_DX = extension_MG_CR_DX.gen_extension(ds)
        if e_MG_CR_DX is not None:
            series_extensions.append(e_MG_CR_DX)

    # PT extension
    if (series_data["modality"].code == "PT"):

        e_PT = extension_PT.gen_extension(ds)
        if e_PT is not None:
            series_extensions.append(e_PT)

    # NM extension
    if (series_data["modality"].code == "NM"):

        e_NM = extension_NM.gen_extension(ds)
        if e_NM is not None:
            series_extensions.append(e_NM)

    # contrast extension
    e_contrast = extension_contrast.gen_extension(ds)
    if e_contrast is not None:
        series_extensions.append(e_contrast)

    series_data["extension"] = series_extensions

    ###### Creating device resource ########

    global devices_list_global

    try: 
        dev, dev_id = create_device.create_device_resource(ds.Manufacturer, ds.ManufacturerModelName, ds.DeviceSerialNumber)
        devices_list_global.append([dev, dev_id])

    except Exception:
        pass

    try:
        dev_ref = reference.Reference()
        dev_ref.reference = "Device/"+str(dev_id)
        series_data["performer"] = [
            {
                "actor": dev_ref
            }
        ]
    except Exception:
        pass


    # Creating New Series
    series = imagingstudy.ImagingStudySeries(**series_data)

    study.series.append(series)
    study.numberOfSeries = study.numberOfSeries + 1
    _add_imaging_study_instance(study, series, ds, include_instances)
    return


def _create_imaging_study(ds, fp, dcmDir, include_instances) -> imagingstudy.ImagingStudy:
    study_data = {}

    m = meta.Meta(profile=[
                  "https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-pr-bildgebung-bildgebungsstudie"])
    study_data["meta"] = m
    study_data["id"] = str(uuid.uuid4())
    study_data["status"] = "available"

    try:
        if ds.StudyDescription != '':
            study_data["description"] = ds.StudyDescription
    except Exception:
        pass
    study_data["identifier"] = []
    if len(ds.AccessionNumber) > 0:
        accession_nr = ds.AccessionNumber
        study_data["identifier"].append(
            dicom2fhirutils.gen_accession_identifier(accession_nr))
    else:
        logging.warning(
            "No accession number availabe - using StudyInstanceUID as Identifier")
        accession_nr = None
        study_data["identifier"].append(
            dicom2fhirutils.gen_studyinstanceuid_identifier(ds.StudyInstanceUID))

    patID9 = str(ds.PatientID)[:9]
    patIdentifier = "https://fhir.diz.uk-erlangen.de/identifiers/patient-id|"+patID9
    hashedIdentifier = hashlib.sha256(
        patIdentifier.encode('utf-8')).hexdigest()
    patientReference = "Patient/"+hashedIdentifier
    patientRef = reference.Reference()
    patientRef.reference = patientReference
    patIdent = identifier.Identifier()
    patIdent.system = "https://fhir.diz.uk-erlangen.de/identifiers/patient-id"
    patIdent.type = dicom2fhirutils.gen_codeable_concept(
        ["MR"], "http://terminology.hl7.org/CodeSystem/v2-0203")
    patIdent.value = patID9
    patientRef.identifier = patIdent
    study_data["subject"] = patientRef

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

    study_data["numberOfSeries"] = 0
    study_data["numberOfInstances"] = 0

    study_data["modality"] = []

    procedures = []
    try:
        procedures = dicom2fhirutils.dcm_coded_concept(
            ds.ProcedureCodeSequence)
    except Exception:
        pass

    procedures_list = []

    try:
        for p in procedures:
            concept = dicom2fhirutils.gen_codeable_concept(
                None, None, None, p["code"])
            procedures_list.append(concept)
    except Exception:
        pass

    study_data["procedureCode"] = procedures_list

    study_extensions = []

    # reason extension
    e_reason = extension_reason.gen_extension(ds)
    if e_reason is not None:
        study_extensions.append(e_reason)

    study_data["extension"] = study_extensions

    # instantiate study here, when all required fields are available
    study = imagingstudy.ImagingStudy(**study_data)

    _add_imaging_study_series(study, ds, fp, include_instances)

    return study, accession_nr


def process_dicom_2_fhir(dcmDir: str, include_instances: bool) -> imagingstudy.ImagingStudy:

    global study_list_modality_global
    files = []
    # TODO: subdirectory must be traversed
    for r, d, f in os.walk(dcmDir):
        for file in f:
            files.append(os.path.join(r, file))

    studyInstanceUID = None
    imagingStudy = None
    accession_number = None
    for fp in tqdm(files):
        try:
            with dcmread(fp, None, [0x7FE00010], force=True) as ds:
                if studyInstanceUID is None:
                    studyInstanceUID = ds.StudyInstanceUID
                if studyInstanceUID != ds.StudyInstanceUID:
                    raise Exception(
                        "Incorrect DCM path, more than one study detected")
                if imagingStudy is None:
                    imagingStudy, accession_number = _create_imaging_study(
                        ds, fp, dcmDir, include_instances)
                else:
                    _add_imaging_study_series(
                        imagingStudy, ds, fp, include_instances)
        except Exception as e:
            logging.error(e)
            pass  # file is not a dicom file

    # add modality list to study level
    try:
        mod_codings = []
        for mod in study_list_modality_global:
            c = dicom2fhirutils.gen_coding(
                value=mod,
                system=dicom2fhirutils.ACQUISITION_MODALITY_SYS)
            mod_codings.append(c)
        imagingStudy.modality = mod_codings
    except Exception as e:
        pass

    study_list_modality_global = []

    return imagingStudy, studyInstanceUID, accession_number, devices_list_global
