from dicom2fhir import dicom2fhirutils
import logging
import pandas as pd
import time

RADIONUCLEIDE_SNOMED_MAPPING_URL = "https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_18.html"


def parse_time_to_seconds(time_str):
    hours = int(time_str[:2])  # Erste 2 Zeichen sind Stunden
    minutes = int(time_str[2:4])  # Nächste 2 Zeichen sind Minuten
    seconds = float(time_str[4:])  # Der Rest sind Sekunden und Millisekunden

    return hours * 3600 + minutes * 60 + seconds


def _get_snomed_mapping(url, debug: bool = False):

    logging.info(f"Get Radionucleide-SNOMED mapping from {url}")
    df = pd.read_html(url, converters={
        "Code Value": str,
        "SNOMED-RT ID": str
    })

    # required columns
    req_cols = ["Code Value", "Code Meaning", "SNOMED-RT ID"]

    mapping = df[2][req_cols]

    # remove empty values:
    mapping = mapping[~mapping['Code Value'].isnull()]

    return mapping


# get mapping table
mapping_table = _get_snomed_mapping(url=RADIONUCLEIDE_SNOMED_MAPPING_URL)


def _get_snomed(snomed_rt, sctmapping):
    # codes are strings
    return (sctmapping.loc[sctmapping['SNOMED-RT ID'] == snomed_rt]["Code Value"].values[0])


def gen_extension(ds):

    ex_list = []

    try:
        extension_NM = dicom2fhirutils.gen_extension(
            url="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-ex-bildgebung-modalitaet-pt-nm"
        )
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
        if dicom2fhirutils.add_extension_value(
            e=extension_radiopharmaceutical,
            url="radiopharmaceutical",
            value=None,
            system=None,
            display=None,
            unit=None,
            text=ds[0x0054, 0x0016][0][0x0018,
                                       0x0031].value,
            type="codeableconcept"
        ):
            ex_list.append(extension_radiopharmaceutical)
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
        snomed_radionucleide = _get_snomed(
            ds[0x0054, 0x0016][0][0x0054,
                                  0x0300][0][0x0008, 0x0100].value, mapping_table)

        if dicom2fhirutils.add_extension_value(
            e=extension_radionuclide,
            url="radionuclide",
            value=snomed_radionucleide,
            system="http://snomed.info/sct",
            display=ds[0x0054, 0x0016][0][0x0054,
                                          0x0300][0][0x0008, 0x0104].value,
            unit=None,
            type="codeableconcept"
        ):
            ex_list.append(extension_radionuclide)
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

    # radionuclideTotalDose
    try:
        extension_radionuclideTotalDose = dicom2fhirutils.gen_extension(
            url="radionuclideTotalDose"
        )
    except Exception:
        pass
    try:

        dose = ds[0x0054, 0x0016][0][0x0018, 0x1074].value

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

    # radionuclideHalfLife
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

    # units
    # am UKER bei NM-Serien nicht befüllt

    try:
        extension_units = dicom2fhirutils.gen_extension(
            url="units"
        )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e=extension_units,
            url="units",
            value=ds[0x0054, 0x1001].value,
            system="http://unitsofmeasure.org",
            unit=None,
            type="codeableconcept"
        ):
            ex_list.append(extension_units)
    except Exception:
        pass

    extension_NM.extension = ex_list

    try:
        if not extension_NM.extension:
            raise ValueError("The NM extension has no nested extensions.")
    except Exception as e:
        print(f"Info: {e}")
        return None

    return extension_NM
