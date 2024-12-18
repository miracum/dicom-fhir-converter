from dicom2fhir import dicom2fhirutils

def gen_extension(ds):

    ex_list = []

    try:
        extension_instance = dicom2fhirutils.gen_extension(
            url="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-ex-bildgebung-instanz-details"
            )
    except Exception:
        pass

    try: 
        pixelSpacingX = ds[0x0028, 0x0030].value[0]
        pixelSpacingY = ds[0x0028, 0x0030].value[1]
    except Exception:
        pass
    
    #pixelSpacing(x)
    try:
        extension_pixelSpacingX = dicom2fhirutils.gen_extension(
            url="pixelSpacing(x)"
            )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e = extension_pixelSpacingX,
            url = "pixelSpacingX",
            value= pixelSpacingX,
            system= "http://unitsofmeasure.org",
            unit= "millimeter",
            type="quantity"
        ):
            ex_list.append(extension_pixelSpacingX)
    except Exception:
        pass

    #pixelSpacing(y)
    try:
        extension_pixelSpacingY = dicom2fhirutils.gen_extension(
            url="pixelSpacing(y)"
            )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e = extension_pixelSpacingY,
            url = "pixelSpacingY",
            value= pixelSpacingY,
            system= "http://unitsofmeasure.org",
            unit= "millimeter",
            type="quantity"
        ):
            ex_list.append(extension_pixelSpacingY)
    except Exception:
        pass

    #sliceThickness
    try:
        extension_sliceThickness = dicom2fhirutils.gen_extension(
            url="sliceThickness"
            )
    except Exception:
        pass
    try:
        if dicom2fhirutils.add_extension_value(
            e = extension_sliceThickness,
            url = "sliceThickness",
            value= ds[0x0018, 0x0050].value,
            system= "http://unitsofmeasure.org",
            unit= "millimeter",
            type="quantity"
        ):
            ex_list.append(extension_sliceThickness)
    except Exception:
        pass

    #imageType
    try:
        extension_imageType = dicom2fhirutils.gen_extension(
            url="imageType"
            )
    except Exception:
        pass
    try:

        imageType_values = ds[0x0008, 0x0008].value
        imageTypes = []
        for v in imageType_values:
            imageTypes.append(v)

        if dicom2fhirutils.add_extension_value(
            e = extension_imageType,
            url = "imageType",
            value= imageTypes,
            system="https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/CodeSystem/mii-cs-bildgebung-instance-image-type",
            unit= None,
            type="codeableconcept"
        ):
            ex_list.append(extension_imageType)
    except Exception:
        pass

    extension_instance.extension = ex_list

    try:
        if not extension_instance.extension:
            raise ValueError("The instance extension has no nested extensions.")
    except Exception as e:
        print(f"Info: {e}")
        return None

    return extension_instance