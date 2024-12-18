from dicom2fhir import dicom2fhirutils

def gen_extension(ds):

    ex_list = []

    try:
        extension_CT = dicom2fhirutils.gen_extension(
            url="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-ex-bildgebung-modalitaet-ct"
            )
    except Exception:
        pass

    #CTDIvol
    try:
        extension_CTDIvol = dicom2fhirutils.gen_extension(
            url="CTDIvol"
            )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e = extension_CTDIvol,
            url = "CTDIvol",
            value=ds[0x0018, 0x9345].value,
            system= "http://unitsofmeasure.org",
            unit= "milligray",
            type="quantity"
        ):
            ex_list.append(extension_CTDIvol)
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
    

    extension_CT.extension = ex_list

    try:
        if not extension_CT.extension:
            raise ValueError("The CT extension has no nested extensions.")
    except Exception as e:
        print(f"Info: {e}")
        return None

    return extension_CT