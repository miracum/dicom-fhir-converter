import json
import pandas as pd
from pathlib import Path
from dicom2fhir import dicom2fhirutils

RADIONUCLIDE_MAPPING_PATH = Path(
    __file__).parent.parent / "resources" / "terminologies" / "radionuclide_PT.json"
RADIONUCLIDE_MAPPING = pd.DataFrame(json.loads(
    RADIONUCLIDE_MAPPING_PATH.read_text(encoding="utf-8")))
RADIOPHARMACEUTICAL_MAPPING_PATH = Path(
    __file__).parent.parent / "resources" / "terminologies" / "radiopharmaceutical_PT.json"
RADIOPHARMACEUTICAL_MAPPING = pd.DataFrame(json.loads(
    RADIONUCLIDE_MAPPING_PATH.read_text(encoding="utf-8")))
UNITS_CSV_PATH = Path(__file__).parent.parent / \
    "resources" / "terminologies" / "units.csv"
UNITS_MAPPING = pd.read_csv(UNITS_CSV_PATH, encoding="utf-8")
EXTENSION_PT_URL = "https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-ex-bildgebung-modalitaet-pt"


def parse_time_to_seconds(time_str):
    hours = int(time_str[:2])  # Hours
    minutes = int(time_str[2:4])  # Minutes
    seconds = float(time_str[4:])  # Seconds + Milliseconds

    return hours * 3600 + minutes * 60 + seconds


def _get_snomed(value, sctmapping):

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


def get_units_mapping(csv_mapping, value):

    # Check DICOM value
    match = csv_mapping[csv_mapping['DICOM Value'] == value]
    if not match.empty:
        row = match.iloc[0]
        return row.iloc[1], row.iloc[2]

    # Check Value itself
    match = csv_mapping[csv_mapping['Code Value'] == value]
    if not match.empty:
        row = match.iloc[0]
        return row.iloc[1], row.iloc[2]
    # No mapping found
    return None, None


def gen_extension(ds):

    ex_list = []

    try:
        extension_PT = dicom2fhirutils.gen_extension(
            url=EXTENSION_PT_URL
        )
    except Exception:
        pass

    # units
    try:
        extension_units = dicom2fhirutils.gen_extension(
            url="units"
        )
    except Exception:
        pass
    try:
        value = ds[0x0054, 0x1001].value
        units_value, units_display = get_units_mapping(UNITS_MAPPING, value)

        if dicom2fhirutils.add_extension_value(
            e=extension_units,
            url="units",
            value=units_value,
            system="http://unitsofmeasure.org",
            unit=None,
            display=units_display,
            type="codeableconcept"
        ):
            ex_list.append(extension_units)
    except Exception:
        pass

    # Tracer Einwirkzeit
    try:
        extension_tracerExposureTime = dicom2fhirutils.gen_extension(
            url="tracerExposureTime"
        )
    except Exception:
        pass
    try:

        acq_time = parse_time_to_seconds(ds[0x0008, 0x0032].value)
        start_time = parse_time_to_seconds(
            ds[0x0054, 0x0016][0][0x0018, 0x1072].value)

        diff_time = abs(acq_time - start_time)

        if dicom2fhirutils.add_extension_value(
            e=extension_tracerExposureTime,
            url="tracerExposureTime",
            value=diff_time,
            system="http://unitsofmeasure.org",
            unit="seconds",
            type="quantity"
        ):
            ex_list.append(extension_tracerExposureTime)
    except Exception:
        pass

    # Radiopharmakon
    try:
        extension_radiopharmaceutical = dicom2fhirutils.gen_extension(
            url="radiopharmaceutical"
        )
    except Exception:
        pass
    try:

        snomed_value, snomed_display = _get_snomed(
            ds[0x0054, 0x0016][0][0x0054, 0x0304][0][0x0008, 0x0100].value, sctmapping=RADIOPHARMACEUTICAL_MAPPING)

        if dicom2fhirutils.add_extension_value(
            e=extension_radiopharmaceutical,
            url="radiopharmaceutical",
            value=snomed_value,
            system="http://snomed.info/sct",
            display=snomed_display,
            text=ds[0x0054, 0x0016][0][0x0054,
                                       0x0304][0][0x0008, 0x0104].value,
            unit=None,
            type="codeableconcept"
        ):
            ex_list.append(extension_radiopharmaceutical)
    except Exception:
        pass

    # Radionuklid Dosis
    try:
        extension_radionuclideTotalDose = dicom2fhirutils.gen_extension(
            url="radionuclideTotalDose"
        )
    except Exception:
        pass
    try:

        dose = ds[0x0054, 0x0016][0][0x0018, 0x1074].value
        # only valid for UKER data - please check!
        dose /= 1000000

        if dicom2fhirutils.add_extension_value(
            e=extension_radionuclideTotalDose,
            url="radionuclideTotalDose",
            value=dose,
            system="http://unitsofmeasure.org",
            unit="Megabecquerel",
            type="quantity"
        ):
            ex_list.append(extension_radionuclideTotalDose)
    except Exception:
        pass

    # Radionuklid Halbwertszeit
    try:
        extension_radionuclideHalfLife = dicom2fhirutils.gen_extension(
            url="radionuclideHalfLife"
        )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e=extension_radionuclideHalfLife,
            url="radionuclideHalfLife",
            value=ds[0x0054, 0x0016][0][0x0018, 0x1075].value,
            system="http://unitsofmeasure.org",
            unit="Seconds",
            type="quantity"
        ):
            ex_list.append(extension_radionuclideHalfLife)
    except Exception:
        pass

    # Radionuklid
    try:
        extension_radionuclide = dicom2fhirutils.gen_extension(
            url="radionuclide"
        )
    except Exception:
        pass
    try:

        snomed_radionuclide, snomed_display = _get_snomed(
            ds[0x0054, 0x0016][0][0x0054, 0x0300][0][0x0008, 0x0100].value, sctmapping=RADIONUCLIDE_MAPPING)

        if dicom2fhirutils.add_extension_value(
            e=extension_radionuclide,
            url="radionuclide",
            value=snomed_radionuclide,
            system="http://snomed.info/sct",
            display=snomed_display,
            text=ds[0x0054, 0x0016][0][0x0054,
                                       0x0300][0][0x0008, 0x0104].value,
            unit=None,
            type="codeableconcept"
        ):
            ex_list.append(extension_radionuclide)
    except Exception:
        pass

    # Serientyp
    try:
        extension_seriesType = dicom2fhirutils.gen_extension(
            url="seriesType"
        )
    except Exception:
        pass
    try:

        seriesType_values = ds[0x0054, 0x1000].value
        if isinstance(seriesType_values, str):
            seriesTypes = seriesType_values
        else:
            seriesTypes = []
            for v in seriesType_values:
                seriesTypes.append(v)

        if dicom2fhirutils.add_extension_value(
            e=extension_seriesType,
            url="seriesType",
            value=seriesTypes,
            system="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/CodeSystem/mii-cs-bildgebung-series-type",
            unit=None,
            type="codeableconcept"
        ):
            ex_list.append(extension_seriesType)
    except Exception:
        pass

    extension_PT.extension = ex_list

    if not extension_PT.extension:
        return None

    return extension_PT
