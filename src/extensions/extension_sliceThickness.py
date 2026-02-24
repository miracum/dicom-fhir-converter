from dicom2fhir import dicom2fhirutils


def gen_extension(ds):

    ex_list = []

    try:
        extension_ST = dicom2fhirutils.gen_extension(
            url="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-ex-bildgebung-serie-schichtdicke"
        )
    except Exception:
        pass

    # slice thickness
    try:
        extension_sliceThickness = dicom2fhirutils.gen_extension(
            url="sliceThickness"
        )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e=extension_sliceThickness,
            url="sliceThickness",
            value=ds[0x0018, 0x0050].value,
            system="http://unitsofmeasure.org",
            unit="millimeter",
            type="quantity"
        ):
            ex_list.append(extension_sliceThickness)
    except Exception:
        return None

    extension_ST.extension = ex_list

    if not extension_ST.extension:
        return None

    return extension_ST
