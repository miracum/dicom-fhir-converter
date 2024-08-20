from dicom2fhir import dicom2fhirutils

def gen_extension(ds):

    ex_list = []

    try:
        extension_MR = dicom2fhirutils.gen_extension(
            url="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-ex-bildgebung-modalitaet-mr"
            )
    except Exception:
        pass

    #scanning sequence
    try:
        extension_scanningSequence = dicom2fhirutils.gen_extension(
            url="scanningSequence"
            )
    except Exception:
        pass
    try:
        dicom2fhirutils.add_extension_value(
            e = extension_scanningSequence,
            url = "scanningSequence",
            value=ds[0x0018, 0x0020].value,
            system=None,
            unit= None,
            type="string"
        )
        ex_list.append(extension_scanningSequence)
    except Exception:
        pass

    
    #scanning sequence variant
    try:
        extension_scanningSequenceVariant = dicom2fhirutils.gen_extension(
            url="scanningSequenceVariant"
            )
    except Exception:
        pass
    try:
        dicom2fhirutils.add_extension_value(
            e = extension_scanningSequenceVariant,
            url = "scanningSequenceVariant",
            value=ds[0x0018, 0x0021].value,
            system=None,
            unit= None,
            type="string"
        )
        ex_list.append(extension_scanningSequenceVariant)
    except Exception:
        pass


    #feldstärke
    try:
        extension_magneticFieldStrength = dicom2fhirutils.gen_extension(
            url="magneticFieldStrength"
            )
    except Exception:
        pass
    try:
        dicom2fhirutils.add_extension_value(
            e = extension_magneticFieldStrength,
            url = "magneticFieldStrength",
            value=ds[0x0018, 0x0087].value,
            system=None,
            unit= "tesla",
            type="quantity"
        )
        ex_list.append(extension_magneticFieldStrength)
    except Exception:
        pass
    

    extension_MR.extension = ex_list

    return extension_MR