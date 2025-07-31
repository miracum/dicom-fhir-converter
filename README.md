# DICOM-fhir-converter

DICOM FHIR converter is an open source python library that accepts a DICOM directory as an input.
It processes all files (instances) within that directory. It expects that directory will only contain files for a single study.
If multiple studies detected, an exception is raised.
Using the usual convention, if file cannot be read, it will be skipped assuming it is not a DICOM file (no error raised).

This library utilizes the following projects:

- fhir.resources project (https://pypi.org/project/fhir.resources/) - used to create FHIR models
- pyDICOM (https://pyDICOM.github.io/) - used to read DICOM instances

## Usage

### Build terminologies

If you wish and are able to, you can run:

```bash
python3 build_terminologies.py
```

This script downloads the respective terminologies in the current version from DICOM NEMA and overwrites them in the directory 'resources/terminologies'.

### Run Python script and give command line arguments as follows:

-i "input_path" (mandatory, input path of DICOM study) <br>
-o "output_path" (mandatory, output path to write json-file in) <br>
--no-level_instance (optional, does not include instance level into ImagingStudy when set) <br>
--build_bundle (optional, builds a FHIR bundle including the ImagingStudy when set) <br>
--create_device (optional, creates the respective Device FHIR resource(s) which performed the ImagingStudy) <br>

### Sample call

```bash
python3 dicom2fhir_wrapper.py -i "my_input_path" -o "my_output_path" --no-level_instance --create_device
```

This call would convert the DICOM study in "my_input_path" into a FHIR Imaging study without building a bundle and without including the instance level. Addiotionally, it would create the associated Device FHIR resource(s) and write the json-files in "my_output_path".

The DICOM file represents a single instance within DICOM study. A study is a collection of instances grouped by series.
The assumption is that all instances are copied into a single folder prior to calling this function. The flattened structure is then consolidated into a single FHIR Imaging Study resource.

## Structure

The FHIR Imaging Study id is being generated internally within the library. If selected, the ImagingStudy will be put into a FHIR Bundle.
The Accession Number is usually used as the "identifier" for the ImagingStudy. If this value is unavailable, the DICOM StudyInstanceUID will be used. If both values are not available, the process will stop with an error message and this study can not be converted.

The model is meant to be self-inclusive (to mimic the DICOM structure), it does not produce separate resources for other resource types.
Instead, it uses references to include all of the supporting data.

### References, IDs and identifiers

#### ImagingStudy

- ImagingStudy.id: hash("https://fhir.diz.uk-erlangen.de/identifiers/imagingstudy-id|" + StudyInstanceUID)
- ImagingStudy.identifier: AccessionNumber OR (if AccessionNumber is not available) StudyInstanceUID

#### Patient

- the converter uses 9-digit Patient IDs
- ImagingStudy.subject.identifier.value: PatientID
- ImagingStudy.subject.reference: "Patient/" + hash("https://fhir.diz.uk-erlangen.de/identifiers/patient-id|" + PatientID)

#### Device

If set (see Usage), the converter can also create the associated Device ressource(s), which performed the ImagingStudy. To do this, the converter uses the serial number in the DICOM tag “DeviceSerialNumber” and the manufacturer of the device in the “Manufacturer” tag as well as the model name in the “ManufacturerModelName” tag.

- Device.identifier: deviceSerialNumber
- Device.id: hash256(deviceSerialnumber + "|" + manufacturer)
- ImagingStudy.series.performer.actor: "Reference/Device" + hash256(deviceSerialnumber + "|" + manufacturer)

### Sample Output

```
{
    "resourceType": "ImagingStudy"
    "id": "011d5e1b-0402-445a-b417-21b86af500dc",
    "meta": {
        "profile": [
            "https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-pr-bildgebung-bildgebungsstudie"
        ]
    },
    "identifier": [
        {
            "type": {
                "coding": [
                    {
                        "code": "ACSN",
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203"
                    }
                ]
            },
            "value": "DAC007_CRLAT"
        },
        {
            "system": "urn:DICOM:uid",
            "value": "urn:oid:1.3.6.1.4.1.5962.99.1.2008629345.2009981611.1359218327649.129.0"
        }
    ],
    "started": "2005-09-06T16:39:26",
    "status": "available",
    "subject": {
        "reference": "Patient/719086612dbb408dc8fa3ea2tzv8",
        "identifier": {
            "type": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code": "MR"
                    }
                ]
            },
            "system": "https://fhir.diz.uk-erlangen.de/identifiers/patient-id",
            "value": "123456789"
        }
    },
    "modality": [
        {
            "code": "CR",
            "system": "http://DICOM.nema.org/resources/ontology/DCM"
        }
    ],
    "numberOfInstances": 1,
    "numberOfSeries": 1,
    "series": [
        {
            "bodySite": {
                "system": "http://snomed.info/sct",
                "code": "69536005",
                "display": "Head"
            },
            "instance": [
                {
                    "number": 1,
                    "sopClass": {
                        "code": "urn:oid:1.2.840.10008.5.1.4.1.1.1",
                        "system": "urn:ietf:rfc:3986"
                    },
                    "uid": "1.3.6.1.4.1.5962.99.1.2008629345.2009981611.1359218327649.128.0"
                }
            ],
            "modality": {
                "code": "CR",
                "system": "http://DICOM.nema.org/resources/ontology/DCM"
            },
            "number": 1,
            "numberOfInstances": 1,
            "started": "2005-09-06T16:39:28",
            "uid": "1.3.6.1.4.1.5962.99.1.2008629345.2009981611.1359218327649.130.0"
        }
    ]
}
```
