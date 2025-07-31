from dicom2fhir import dicom2fhirutils
from pathlib import Path
import pandas as pd
import csv
import json

VIEWPOSISTION_MG_MAPPING_PATH = Path(
    __file__).parent.parent / "resources" / "terminologies" / "viewposition_MG.json"
VIEWPOSISTION_DX_MAPPING_PATH = Path(
    __file__).parent.parent / "resources" / "terminologies" / "viewposition_DX.json"
VIEWPOSISTION_MG_MAPPING = pd.DataFrame(json.loads(
    VIEWPOSISTION_MG_MAPPING_PATH.read_text(encoding="utf-8")))
VIEWPOSISTION_DX_MAPPING = pd.DataFrame(json.loads(
    VIEWPOSISTION_DX_MAPPING_PATH.read_text(encoding="utf-8")))
VIEWPOSITION_DX_CSV_PATH = Path(
    __file__).parent.parent / "resources" / "terminologies" / "viewposition_DX_2.csv"


def _get_snomed_MG(value, sctmapping):
    # Check: 'ACR MQCM 1999 Equivalent'
    match = sctmapping[sctmapping['ACR MQCM 1999 Equivalent'] == value]
    if not match.empty:
        row = match.iloc[0]
        return row["Code Value"], row["Code Meaning"]

    # Check: 'SNOMED-RT ID'
    match = sctmapping[sctmapping['SNOMED-RT ID'] == value]
    if not match.empty:
        row = match.iloc[0]
        return row["Code Value"], row["Code Meaning"]

    # Check: 'Code Meaning'
    match = sctmapping[sctmapping['Code Meaning'] == value]
    if not match.empty:
        row = match.iloc[0]
        return row["Code Value"], row["Code Meaning"]

    # Check: already valid 'Code Value'
    match = sctmapping[sctmapping['Code Value'] == value]
    if not match.empty:
        row = match.iloc[0]
        return row["Code Value"], row["Code Meaning"]

    # No mapping found
    return None, None


def _get_snomed_DX(value, sctmapping):
    # Check: 'SNOMED-RT ID'
    match = sctmapping[sctmapping['SNOMED-RT ID'] == value]
    if not match.empty:
        row = match.iloc[0]
        return row["Code Value"], row["Code Meaning"]

    # Check: 'Code Meaning'
    match = sctmapping[sctmapping['Code Meaning'] == value]
    if not match.empty:
        row = match.iloc[0]
        return row["Code Value"], row["Code Meaning"]

    # Check: already valid 'Code Value'
    match = sctmapping[sctmapping['Code Value'] == value]
    if not match.empty:
        row = match.iloc[0]
        return row["Code Value"], row["Code Meaning"]

    return None, None

# alternative mapping (common abbreviations)


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
        print(f"Error loading the csv file: {e}")
    return mapping


def gen_extension(ds):

    ex_list = []

    try:
        extension_MG_CR_DX = dicom2fhirutils.gen_extension(
            url="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-ex-bildgebung-modalitaet-mg-cr-dx"
        )
    except Exception:
        return

    # KVP
    try:
        extension_KVP = dicom2fhirutils.gen_extension(
            url="KVP"
        )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e=extension_KVP,
            url="KVP",
            value=ds[0x0018, 0x0060].value,
            system="http://unitsofmeasure.org",
            unit="kilovolt",
            type="quantity"
        ):
            ex_list.append(extension_KVP)
    except Exception:
        pass

    # exposureTime
    try:
        extension_exposureTime = dicom2fhirutils.gen_extension(
            url="exposureTime"
        )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e=extension_exposureTime,
            url="exposureTime",
            value=ds[0x0018, 0x1150].value,
            system="http://unitsofmeasure.org",
            unit="milliseconds",
            type="quantity"
        ):
            ex_list.append(extension_exposureTime)
    except Exception:
        pass

    # exposure
    try:
        extension_exposure = dicom2fhirutils.gen_extension(
            url="exposure"
        )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e=extension_exposure,
            url="exposure",
            value=ds[0x0018, 0x1152].value,
            system="http://unitsofmeasure.org",
            unit="milliampere second",
            type="quantity"
        ):
            ex_list.append(extension_exposure)
    except Exception:
        pass

    # tube current
    try:
        extension_xRayTubeCurrent = dicom2fhirutils.gen_extension(
            url="xRayTubeCurrent"
        )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e=extension_xRayTubeCurrent,
            url="xRayTubeCurrent",
            value=ds[0x0018, 0x1151].value,
            system="http://unitsofmeasure.org",
            unit="milliampere",
            type="quantity"
        ):
            ex_list.append(extension_xRayTubeCurrent)
    except Exception:
        pass

    # view position
    try:
        extension_viewPosition = dicom2fhirutils.gen_extension(
            url="viewPosition"
        )
    except Exception:
        pass
    try:
        if ds[0x0008, 0x0060].value == "MG":
            snomed_value, snomed_display = _get_snomed_MG(
                ds[0x0018, 0x5101].value, sctmapping=VIEWPOSISTION_MG_MAPPING)
        elif ds[0x0008, 0x0060].value == "DX":
            snomed_value, snomed_display = _get_snomed_DX(
                ds.ViewPosition, sctmapping=VIEWPOSISTION_DX_MAPPING)
            if snomed_value is None:
                mapping = load_DX_mapping_from_csv(VIEWPOSITION_DX_CSV_PATH)
                meaning = mapping.get(ds.ViewPosition, None)
                snomed_value, snomed_display = _get_snomed_DX(
                    meaning, sctmapping=VIEWPOSISTION_DX_MAPPING)
        else:
            snomed_value = snomed_display = None

        if dicom2fhirutils.add_extension_value(
            e=extension_viewPosition,
            url="viewPosition",
            value=snomed_value,
            system="http://snomed.info/sct",
            unit=None,
            display=snomed_display,
            type="codeableconcept"
        ):
            ex_list.append(extension_viewPosition)
    except Exception:
        pass

    extension_MG_CR_DX.extension = ex_list

    if not extension_MG_CR_DX.extension:
        return None

    return extension_MG_CR_DX
