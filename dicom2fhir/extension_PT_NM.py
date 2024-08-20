from dicom2fhir import dicom2fhirutils
import logging
import pandas as pd

RADIOPHARMACEUTICAL_SNOMED_MAPPING_URL = "https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_25.html"


def _get_snomed_mapping(url, debug: bool = False):

    logging.info(f"Get Radiopharmaceutical-SNOMED mapping from {url}")
    df = pd.read_html(url, converters={
        "Code Value": str,
        "SNOMED-RT ID": str
    })

    # required columns
    req_cols = ["Code Value", "Code Meaning", "SNOMED-RT ID"]

    mapping = df[2][req_cols]

    # remove empty values:
    mapping = mapping[~mapping['SNOMED-RT ID'].isnull()]

    return mapping


# get mapping table
mapping_table = _get_snomed_mapping(url=RADIOPHARMACEUTICAL_SNOMED_MAPPING_URL)


def _get_snomed(snomed_rt, sctmapping):
    # codes are strings
    return (sctmapping.loc[sctmapping['SNOMED-RT ID'] == snomed_rt]["Code Value"].values[0])


def gen_extension(ds):

    ex_list = []

    try:
        extension_PT_NM = dicom2fhirutils.gen_extension(
            url="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-ex-bildgebung-modalitaet-pt-nm"
            )
    except Exception:
        pass

    #RadiopharmaceuticalStartTime
    try:
        extension_radiopharmaceuticalStartTime = dicom2fhirutils.gen_extension(
            url="radiopharmaceuticalStartTime"
            )
    except Exception:
        pass
    try:
        dicom2fhirutils.add_extension_value(
            e = extension_radiopharmaceuticalStartTime,
            url = "radiopharmaceuticalStartTime",
            value= ds[0x0054, 0x0016][0][0x0018,0x1072].value,
            system= None,
            unit= None,
            type= "datetime"
        )
        ex_list.append(extension_radiopharmaceuticalStartTime)
    except Exception:
        pass

    #Radiopharmakon
    try:
        extension_radiopharmaceutical = dicom2fhirutils.gen_extension(
            url="radiopharmaceutical"
            )
    except Exception:
        pass
    try:

        snomed_pharmaceutical = _get_snomed(ds[0x0054, 0x0016][0][0x0054, 0x0304][0][0x0008,0x0100].value, mapping_table)

        dicom2fhirutils.add_extension_value(
            e = extension_radiopharmaceutical,
            url = "radiopharmaceutical",
            value= snomed_pharmaceutical,
            system= "http://snomed.info/sct",
            display = ds[0x0054, 0x0016][0][0x0054, 0x0304][0][0x0008,0x0104].value,
            unit= None,
            type= "codeableconcept"
        )
        ex_list.append(extension_radiopharmaceutical)
    except Exception:
        pass

    #radionuclideTotalDose
    try:
        extension_radionuclideTotalDose = dicom2fhirutils.gen_extension(
            url="radionuclideTotalDose"
            )
    except Exception:
        pass
    try:

        dose = ds[0x0054, 0x0016][0][0x0018,0x1074].value

        if ds[0x0008,0x0060].value == "PT":
            dose /= 1000000

        dicom2fhirutils.add_extension_value(
            e = extension_radionuclideTotalDose,
            url = "radionuclideTotalDose",
            value= dose,
            system= "http://unitsofmeasure.org",
            unit= "Megabecquerel",
            type= "quantity"
        )
        ex_list.append(extension_radionuclideTotalDose)
    except Exception:
        pass

    #radionuclideHalfLife
    try:
        extension_radionuclideHalfLife = dicom2fhirutils.gen_extension(
            url="radionuclideHalfLife"
            )
    except Exception:
        pass
    try:
        dicom2fhirutils.add_extension_value(
            e = extension_radionuclideHalfLife,
            url = "radionuclideHalfLife",
            value= ds[0x0054, 0x0016][0][0x0018,0x1075].value,
            system= "http://unitsofmeasure.org",
            unit= "Seconds",
            type= "quantity"
        )
        ex_list.append(extension_radionuclideHalfLife)
    except Exception:
        pass
    

    extension_PT_NM.extension = ex_list

    return extension_PT_NM