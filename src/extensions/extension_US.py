from dicom2fhir import dicom2fhirutils


def gen_extension(ds):

    ex_list = []

    try:
        extension_US = dicom2fhirutils.gen_extension(
            url="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-ex-bildgebung-modalitaet-us"
        )
    except Exception:
        pass

    # transducerType
    try:
        extension_transducerType = dicom2fhirutils.gen_extension(
            url="transducerType"
        )
    except Exception:
        pass
    try:
        transducer_type = ds[0x0018, 0x6031].value
        if len(transducer_type.split()) > 1:
            counter = 0
            transducer_type_concat = ""
            for v in transducer_type.split():
                if counter != 0:
                    transducer_type_concat = transducer_type_concat + "_"
                transducer_type_concat = transducer_type_concat + v
                counter += 1
        else:
            transducer_type_concat = transducer_type

        if dicom2fhirutils.add_extension_value(
            e=extension_transducerType,
            url="transducerType",
            value=transducer_type_concat,
            system="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/CodeSystem/mii-cs-bildgebung-transducer-type",
            unit=None,
            type="codeableconcept"
        ):
            ex_list.append(extension_transducerType)
    except Exception:
        pass

    # transducerFrequency
    try:
        extension_transducerFrequency = dicom2fhirutils.gen_extension(
            url="transducerFrequency"
        )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e=extension_transducerFrequency,
            url="transducerFrequency",
            value=ds[0x0018, 0x6011][0][0x0018, 0x6030].value,
            system="http://unitsofmeasure.org",
            unit="kilohertz",
            type="quantity"
        ):
            ex_list.append(extension_transducerFrequency)
    except Exception:
        pass

    # pulseRepetitionFrequency
    try:
        extension_pulseRepetitionFrequency = dicom2fhirutils.gen_extension(
            url="pulseRepetitionFrequency"
        )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e=extension_pulseRepetitionFrequency,
            url="pulseRepetitionFrequency",
            value=ds[0x0018, 0x6011][0][0x0018, 0x6032].value,
            system="http://unitsofmeasure.org",
            unit="hertz",
            type="quantity"
        ):
            ex_list.append(extension_pulseRepetitionFrequency)
    except Exception:
        pass

    # ultrasoundColor
    try:
        extension_ultrasoundColor = dicom2fhirutils.gen_extension(
            url="ultrasoundColor"
        )
    except Exception:
        pass
    try:
        if ((ds[0x0028, 0x0014].value == 1) or (ds[0x0028, 0x0014].value == "01") or (ds[0x0028, 0x0014].value == "1")):
            value_color = True
        else:
            value_color = False

        if dicom2fhirutils.add_extension_value(
            e=extension_ultrasoundColor,
            url="ultrasoundColor",
            value=value_color,
            system=None,
            unit=None,
            type="boolean"
        ):
            ex_list.append(extension_ultrasoundColor)
    except Exception:
        pass

    extension_US.extension = ex_list

    if not extension_US.extension:
        return None

    return extension_US
