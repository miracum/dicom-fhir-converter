from dicom2fhir import dicom2fhirutils
import logging
import pandas as pd
import csv
import os

viewPosision_MG_SNOMED_MAPPING_URL = "https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4014.html"
viewPosision_DX_SNOMED_MAPPING_URL = "https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4010.html"
script_dir = os.path.dirname(__file__)
DX_csv_file = os.path.join(script_dir, "DX_viewPosition_Mapping.csv")


def _get_snomed_mapping_MG(url, debug: bool = False):

    logging.info(f"Get viewPosition-SNOMED mapping from {url}")
    df = pd.read_html(url, converters={
        "Code Value": str,
        "ACR MQCM 1999 Equivalent": str,
        "Code Meaning": str
    })

    # required columns
    req_cols = ["Code Value", "Code Meaning", "ACR MQCM 1999 Equivalent"]

    mapping = df[2][req_cols]

    # remove empty values:
    mapping = mapping[~mapping['Code Value'].isnull()]

    return mapping

def _get_snomed_mapping_DX(url, debug: bool = False):

    logging.info(f"Get viewPosition-SNOMED mapping from {url}")
    df = pd.read_html(url, converters={
        "Code Value": str,
        "Code Meaning": str
    })

    # required columns
    req_cols = ["Code Value", "Code Meaning"]

    mapping = df[2][req_cols]

    # remove empty values:
    mapping = mapping[~mapping['Code Value'].isnull()]

    return mapping


# get mapping table
mapping_table_MG = _get_snomed_mapping_MG(url=viewPosision_MG_SNOMED_MAPPING_URL)

mapping_table_DX = _get_snomed_mapping_DX(url=viewPosision_DX_SNOMED_MAPPING_URL)


def _get_snomed_MG(acr, sctmapping):
    # codes are strings
    return (sctmapping.loc[sctmapping['ACR MQCM 1999 Equivalent'] == acr]["Code Value"].values[0])

def _get_snomed_DX(code, sctmapping):
    # codes are strings
    try:
        return (sctmapping.loc[sctmapping['Code Meaning'] == code.lower()]["Code Value"].values[0])
    except Exception:
        return None

def load_DX_mapping_from_csv(csv_file):
    
    mapping = {}
    try:
        with open(csv_file, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                code = row['ACR'].strip()
                meaning = row['Code Meaning'].strip()
                mapping[code] = meaning
    except Exception as e:
        print(f"Fehler beim Laden der CSV-Datei: {e}")
    return mapping

def gen_extension(ds):

    ex_list = []

    try:
        extension_MG_CR_DX = dicom2fhirutils.gen_extension(
            url="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-ex-bildgebung-modalitaet-mg-cr-dx"
            )
    except Exception:
        return

    #KVP
    try:
        extension_KVP = dicom2fhirutils.gen_extension(
            url="KVP"
            )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e = extension_KVP,
            url = "KVP",
            value=ds[0x0018, 0x0060].value,
            system= "http://unitsofmeasure.org",
            unit= "kilovolt",
            type="quantity"
        ):
            ex_list.append(extension_KVP)
    except Exception:
        pass

    #exposureTime
    try:
        extension_exposureTime = dicom2fhirutils.gen_extension(
            url="exposureTime"
            )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e = extension_exposureTime,
            url = "exposureTime",
            value=ds[0x0018, 0x1150].value,
            system= "http://unitsofmeasure.org",
            unit= "milliseconds",
            type="quantity"
        ):
            ex_list.append(extension_exposureTime)
    except Exception:
        pass

    #exposure
    try:
        extension_exposure = dicom2fhirutils.gen_extension(
            url="exposure"
            )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e = extension_exposure,
            url = "exposure",
            value=ds[0x0018, 0x1152].value,
            system= "http://unitsofmeasure.org",
            unit= "milliampere second",
            type="quantity"
        ):
            ex_list.append(extension_exposure)
    except Exception:
        pass

    #tube current
    try:
        extension_xRayTubeCurrent = dicom2fhirutils.gen_extension(
            url="xRayTubeCurrent"
            )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e = extension_xRayTubeCurrent,
            url = "xRayTubeCurrent",
            value=ds[0x0018, 0x1151].value,
            system= "http://unitsofmeasure.org",
            unit= "milliampere",
            type="quantity"
        ):
            ex_list.append(extension_xRayTubeCurrent)
    except Exception:
        pass

    #view position
    try:
        extension_viewPosition = dicom2fhirutils.gen_extension(
            url="viewPosition"
            )
    except Exception:
        pass
    try:
        if ds[0x0008, 0x0060].value == "MG":
            snomed_value = _get_snomed_MG(ds[0x0018, 0x5101].value, sctmapping=mapping_table_MG)
        elif ds[0x0008, 0x0060].value == "DX":
            snomed_value = _get_snomed_DX(ds[0x0018, 0x5101].value, sctmapping=mapping_table_DX)
            if snomed_value is None:
                mapping = load_DX_mapping_from_csv(DX_csv_file)
                meaning = mapping.get(ds[0x0018, 0x5101].value, None)
                snomed_value = _get_snomed_DX(meaning, sctmapping=mapping_table_DX)
        else: 
            snomed_value = None

        if dicom2fhirutils.add_extension_value(
            e = extension_viewPosition,
            url = "viewPosition",
            value=snomed_value,
            system= "http://snomed.info/sct",
            unit= None,
            display = ds[0x0018, 0x5101].value,
            type="codeableconcept"
        ):
            ex_list.append(extension_viewPosition)
    except Exception:
        pass
    

    extension_MG_CR_DX.extension = ex_list

    try:
        if not extension_MG_CR_DX.extension:
            raise ValueError("The MG-CR-DX extension has no nested extensions.")
    except Exception as e:
        print(f"Info: {e}")
        return None

    return extension_MG_CR_DX