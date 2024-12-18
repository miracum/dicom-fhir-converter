from dicom2fhir import dicom2fhirutils


def gen_extension(ds):

    ex_list = []

    try:
        extension_MR = dicom2fhirutils.gen_extension(
            url="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-ex-bildgebung-modalitaet-mr"
        )
    except Exception:
        pass

    # scanning sequence
    try:
        extension_scanningSequence = dicom2fhirutils.gen_extension(
            url="scanningSequence"
        )
    except Exception:
        pass

    try:
        value = ds[0x0018, 0x0020].value
        sequence_values = value.split("\\")

        if dicom2fhirutils.add_extension_value(
            e=extension_scanningSequence,
            url="scanningSequence",
            value=sequence_values,
            system="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/CodeSystem/mii-cs-bildgebung-scanning-sequence",
            unit=None,
            type="codeableconcept",
        ):
            ex_list.append(extension_scanningSequence)
    except Exception:
        pass

    # scanning sequence variant
    try:
        extension_scanningSequenceVariant = dicom2fhirutils.gen_extension(
            url="scanningSequenceVariant"
        )
    except Exception:
        pass
    try:
        values = ds[0x0018, 0x0021].value
        variant_values = []
        for v in values:
            variant_values.append(v)

        if dicom2fhirutils.add_extension_value(
            e=extension_scanningSequenceVariant,
            url="scanningSequenceVariant",
            value=variant_values,
            system="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/CodeSystem/mii-cs-bildgebung-scanning-sequence-variant",
            unit=None,
            type="codeableconcept"
        ):
            ex_list.append(extension_scanningSequenceVariant)
    except Exception:
        pass

    # feldstärke
    try:
        extension_magneticFieldStrength = dicom2fhirutils.gen_extension(
            url="magneticFieldStrength"
        )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e=extension_magneticFieldStrength,
            url="magneticFieldStrength",
            value=ds[0x0018, 0x0087].value,
            system="http://unitsofmeasure.org",
            unit="tesla",
            type="quantity"
        ):
            ex_list.append(extension_magneticFieldStrength)
    except Exception:
        pass

    # TE
    try:
        extension_TE = dicom2fhirutils.gen_extension(
            url="echoTime"
        )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e=extension_TE,
            url="echoTime",
            value=ds[0x0018, 0x0081].value,
            system="http://unitsofmeasure.org",
            unit="milliseconds",
            type="quantity"
        ):
            ex_list.append(extension_TE)
    except Exception:
        pass

    # TR
    try:
        extension_TR = dicom2fhirutils.gen_extension(
            url="repetitionTime"
        )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e=extension_TR,
            url="repetitionTime",
            value=ds[0x0018, 0x0080].value,
            system="http://unitsofmeasure.org",
            unit="milliseconds",
            type="quantity"
        ):
            ex_list.append(extension_TR)
    except Exception:
        pass

    # TI
    try:
        extension_TI = dicom2fhirutils.gen_extension(
            url="inversionTime"
        )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e=extension_TI,
            url="inversionTime",
            value=ds[0x0018, 0x0082].value,
            system="http://unitsofmeasure.org",
            unit="milliseconds",
            type="quantity"
        ):
            ex_list.append(extension_TI)
    except Exception:
        pass

    # kippwinkel
    try:
        extension_flipAngle = dicom2fhirutils.gen_extension(
            url="flipAngle"
        )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e=extension_flipAngle,
            url="flipAngle",
            value=ds[0x0018, 0x1314].value,
            system="http://unitsofmeasure.org",
            unit="plane angle degree",
            type="quantity"
        ):
            ex_list.append(extension_flipAngle)
    except Exception:
        pass

    extension_MR.extension = ex_list

    try:
        if not extension_MR.extension:
            raise ValueError("The MR extension has no nested extensions.")
    except Exception as e:
        print(f"Info: {e}")
        return None

    return extension_MR
