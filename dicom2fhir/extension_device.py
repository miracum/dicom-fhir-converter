from dicom2fhir import dicom2fhirutils

def gen_extension(ds):

    ex_list = []

    try:
        extension_device = dicom2fhirutils.gen_extension(
            url="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-ex-bildgebung-geraet-hersteller"
            )
    except Exception:
        pass

    #manufacturer
    try:
        extension_manufacturer = dicom2fhirutils.gen_extension(
            url="manufacturer"
            )
    except Exception:
        pass
    try:
        dicom2fhirutils.add_extension_value(
            e = extension_manufacturer,
            url = "manufacturer",
            value=ds[0x0008, 0x0070].value,
            system=None,
            unit= None,
            type="string"
        )
        ex_list.append(extension_manufacturer)
    except Exception:
        pass

    
    #manufacturerModelName
    try:
        extension_manufacturerModelName = dicom2fhirutils.gen_extension(
            url="manufacturerModelName"
            )
    except Exception:
        pass
    try:
        dicom2fhirutils.add_extension_value(
            e = extension_manufacturerModelName,
            url = "manufacturerModelName",
            value=ds[0x0008, 0x1090].value,
            system=None,
            unit= None,
            type="string"
        )
        ex_list.append(extension_manufacturerModelName)
    except Exception:
        pass
    

    extension_device.extension = ex_list

    return extension_device