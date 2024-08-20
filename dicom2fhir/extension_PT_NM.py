from dicom2fhir import dicom2fhirutils

def gen_extension(ds):

    ex_list = []

    try:
        extension_PT_NM = dicom2fhirutils.gen_extension(
            url="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-ex-bildgebung-modalitaet-pt-nm"
            )
    except Exception:
        pass

    #RadiopharmaceuticalStartTime
    try:
        extension_radiopharmaceuticalStartTime = dicom2fhirutils.gen_extension(
            url="radiopharmaceuticalStartTime"
            )
    except Exception:
        pass
    try:
        dicom2fhirutils.add_extension_value(
            e = extension_radiopharmaceuticalStartTime,
            url = "radiopharmaceuticalStartTime",
            value= ds[0x0054, 0x0016][0][0x0018,0x1072].value,
            system= None,
            unit= None,
            type= "datetime"
        )
        ex_list.append(extension_radiopharmaceuticalStartTime)
    except Exception:
        pass

    #Radiopharmakon
    try:
        extension_radiopharmaceutical = dicom2fhirutils.gen_extension(
            url="radiopharmaceutical"
            )
    except Exception:
        pass
    try:
        dicom2fhirutils.add_extension_value(
            e = extension_radiopharmaceutical,
            url = "radiopharmaceutical",
            value= ds[0x0054, 0x0016][0][0x0018,0x0031].value,
            system= "http://snomed.info/sct",
            unit= None,
            type= "codeableconcept"
        )
        ex_list.append(extension_radiopharmaceutical)
    except Exception:
        pass

    #radionuclideTotalDose
    try:
        extension_radionuclideTotalDose = dicom2fhirutils.gen_extension(
            url="radionuclideTotalDose"
            )
    except Exception:
        pass
    try:

        dose = ds[0x0054, 0x0016][0][0x0018,0x1074].value
        if ds[0x0008,0x0060] == "PT":
            dose /= 1000

        dicom2fhirutils.add_extension_value(
            e = extension_radionuclideTotalDose,
            url = "radionuclideTotalDose",
            value= dose,
            system= "http://unitsofmeasure.org",
            unit= "Megabecquerel",
            type= "quantity"
        )
        ex_list.append(extension_radionuclideTotalDose)
    except Exception:
        pass

    #radionuclideHalfLife
    try:
        extension_radionuclideHalfLife = dicom2fhirutils.gen_extension(
            url="radionuclideHalfLife"
            )
    except Exception:
        pass
    try:
        dicom2fhirutils.add_extension_value(
            e = extension_radionuclideHalfLife,
            url = "radionuclideHalfLife",
            value= ds[0x0054, 0x0016][0][0x0018,0x1075].value,
            system= "http://unitsofmeasure.org",
            unit= "Seconds",
            type= "quantity"
        )
        ex_list.append(extension_radionuclideHalfLife)
    except Exception:
        pass
    

    extension_PT_NM.extension = ex_list

    return extension_PT_NM