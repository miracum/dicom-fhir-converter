from dicom2fhir import dicom2fhirutils
import logging
import pandas as pd

RADIOPHARMACEUTICAL_SNOMED_MAPPING_URL = "https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4021.html"
radionuclide_SNOMED_MAPPING_URL = "https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4020.html"


def _get_snomed_mapping(url, debug: bool = False):

    logging.info(f"Get Radiopharmaceutical-SNOMED mapping from {url}")
    df = pd.read_html(url, converters={
        "Code Value": str,
        "Code Meaning": str,
        "SNOMED-RT ID": str
    })

    # required columns
    req_cols = ["Code Value", "Code Meaning", "SNOMED-RT ID"]

    mapping = df[2][req_cols]

    return mapping


# get mapping table
mapping_table_radiopharmaceutical = _get_snomed_mapping(
    url=RADIOPHARMACEUTICAL_SNOMED_MAPPING_URL)
mapping_table_radionuclide = _get_snomed_mapping(
    url=radionuclide_SNOMED_MAPPING_URL)


def _get_snomed(value, sctmapping):
    # codes are strings
    return (sctmapping.loc[sctmapping['SNOMED-RT ID'] == value]["Code Value"].values[0])


def parse_time_to_seconds(time_str):
    hours = int(time_str[:2])  # Erste 2 Zeichen sind Stunden
    minutes = int(time_str[2:4])  # Nächste 2 Zeichen sind Minuten
    seconds = float(time_str[4:])  # Der Rest sind Sekunden und Millisekunden

    return hours * 3600 + minutes * 60 + seconds


def gen_extension(ds):

    ex_list = []

    try:
        extension_PT_NM = dicom2fhirutils.gen_extension(
            url="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-ex-bildgebung-modalitaet-pt-nm"
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
        if value == "BQML":
            value = ["Bq/ml", "Becquerels/milliliter"]
        elif value ==  "PROPCPS":
            value = ["{propcounts}", "Proportional to counts"]
        else:
            value = [value, None]

        if dicom2fhirutils.add_extension_value(
            e = extension_units,
            url = "units",
            value = value[0],
            system="http://unitsofmeasure.org",
            unit= None,
            display = value[1],
            type= "codeableconcept"
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

        snomed_pharmaceutical = _get_snomed(
            ds[0x0054, 0x0016][0][0x0054, 0x0304][0][0x0008, 0x0100].value, mapping_table_radiopharmaceutical)

        if dicom2fhirutils.add_extension_value(
            e=extension_radiopharmaceutical,
            url="radiopharmaceutical",
            value=snomed_pharmaceutical,
            system="http://snomed.info/sct",
            display=ds[0x0054, 0x0016][0][0x0054,
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

        snomed_radionuclide = _get_snomed(
            ds[0x0054, 0x0016][0][0x0054, 0x0300][0][0x0008, 0x0100].value, mapping_table_radionuclide)

        if dicom2fhirutils.add_extension_value(
            e=extension_radionuclide,
            url="radionuclide",
            value=snomed_radionuclide,
            system="http://snomed.info/sct",
            display=ds[0x0054, 0x0016][0][0x0054,
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

    extension_PT_NM.extension = ex_list

    try:
        if not extension_PT_NM.extension:
            raise Warning("The PT extension has no nested extensions.")
    except Exception as e:
        print(f"Info: {e}")
        return None

    return extension_PT_NM
