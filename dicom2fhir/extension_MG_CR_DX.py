from dicom2fhir import dicom2fhirutils
import logging
import pandas as pd

viewPosision_MG_SNOMED_MAPPING_URL = "https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4014.html"
viewPosision_DX_SNOMED_MAPPING_URL = "https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4010.html"


def _get_snomed_mapping(url, debug: bool = False):

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


# get mapping table
mapping_table_MG = _get_snomed_mapping(url=viewPosision_MG_SNOMED_MAPPING_URL)

# funktioniert so nicht - in den Erlanger Daten stehen auch hier ACR Abkürzungen, die jedoch nicht mehr in der DICOM-Tabelle stehen
# mapping_table_DX = _get_snomed_mapping(url=viewPosision_DX_SNOMED_MAPPING_URL)


def _get_snomed(acr, sctmapping):
    # codes are strings
    return (sctmapping.loc[sctmapping['ACR MQCM 1999 Equivalent'] == acr]["Code Value"].values[0])

def gen_extension(ds):

    ex_list = []

    try:
        extension_MG_CR_DX = dicom2fhirutils.gen_extension(
            url="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-ex-bildgebung-modalitaet-mg-cr-dx"
            )
    except Exception:
        pass

    #KVP
    try:
        extension_KVP = dicom2fhirutils.gen_extension(
            url="KVP"
            )
    except Exception:
        pass
    try:
        dicom2fhirutils.add_extension_value(
            e = extension_KVP,
            url = "KVP",
            value=ds[0x0018, 0x0060].value,
            system= "http://unitsofmeasure.org",
            unit= "kilovolt",
            type="quantity"
        )
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
        dicom2fhirutils.add_extension_value(
            e = extension_exposureTime,
            url = "exposureTime",
            value=ds[0x0018, 0x1150].value,
            system= "http://unitsofmeasure.org",
            unit= "kilovolt",
            type="quantity"
        )
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
        dicom2fhirutils.add_extension_value(
            e = extension_exposure,
            url = "exposure",
            value=ds[0x0018, 0x1152].value,
            system= "http://unitsofmeasure.org",
            unit= "milliampere second",
            type="quantity"
        )
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
        dicom2fhirutils.add_extension_value(
            e = extension_xRayTubeCurrent,
            url = "xRayTubeCurrent",
            value=ds[0x0018, 0x1151].value,
            system= "http://unitsofmeasure.org",
            unit= "milliampere",
            type="quantity"
        )
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
            snomed_value = _get_snomed(ds[0x0018, 0x5101].value, sctmapping=mapping_table_MG)
        # elif ds[0x0018, 0x1151].value == "DX":
        #     snomed_value = _get_snomed(ds[0x0018, 0x1151].value, sctmapping=mapping_table_DX)
        else: 
            snomed_value = None

        dicom2fhirutils.add_extension_value(
            e = extension_viewPosition,
            url = "viewPosition",
            value=snomed_value,
            system= "http://snomed.info/sct",
            unit= None,
            display = ds[0x0018, 0x5101].value,
            type="codeableconcept"
        )
        ex_list.append(extension_viewPosition)
    except Exception:
        pass
    

    extension_MG_CR_DX.extension = ex_list

    return extension_MG_CR_DX