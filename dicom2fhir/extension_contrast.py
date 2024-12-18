from dicom2fhir import dicom2fhirutils

def gen_extension(ds):

    ex_list = []

    try:
        extension_contrast = dicom2fhirutils.gen_extension(
            url="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-ex-bildgebung-kontrastmittel"
            )
    except Exception:
        pass

    #contrastBolus
    try:
        extension_contrastBolus = dicom2fhirutils.gen_extension(
            url="contrastBolus"
            )
    except Exception:
        pass
    try:
        if (ds[0x0018, 0x0010].value is None) or (len(ds[0x0018, 0x0010].value) == 0):
            valueContrast = False
        else:
            valueContrast = True

        if dicom2fhirutils.add_extension_value(
            e = extension_contrastBolus,
            url = "contrastBolus",
            value=valueContrast,
            system=None,
            unit= None,
            type="boolean"
        ):
            ex_list.append(extension_contrastBolus)
    except Exception:
        return None
    
    #contrastBolusDetails
    try:
        display_value = ds[0x0018, 0x0010].value
        extension_contrastBolusDetails = dicom2fhirutils.gen_extension(
            url="contrastBolusDetails"
            )
        if dicom2fhirutils.add_extension_value(
            e = extension_contrastBolusDetails,
            url = "contrastBolusDetails",
            value= None,
            system=None,
            unit= None,
            display=display_value,
            type="reference"
        ):
            ex_list.append(extension_contrastBolusDetails)
    except Exception:
        pass
    
    extension_contrast.extension = ex_list

    try:
        if not extension_contrast.extension:
            raise ValueError("The instance extension has no nested extensions.")
    except Exception as e:
        print(f"Info: {e}")
        return None

    return extension_contrast