# DICOM-fhir-converter

DICOM FHIR converter is an open source python library that accepts a DICOM directory as an input.
It processes all files (instances) within that directory. It expects that directory will only contain files for a single study.
If multiple studies detected, an exception is raised.
Using the usual convention, if file cannot be read, it will be skipped assuming it is not a DICOM file (no error raised).

This library utilizes the following projects:

- fhir.resources project (https://pypi.org/project/fhir.resources/) - used to create FHIR models
- pyDICOM (https://pyDICOM.github.io/) - used to read DICOM instances

## Usage

### Set your internal settings via settings.py:

dicom_input_path: input path of DICOM study <br>
fhir_output_path: output path to write json-file/bundles in <br>
level_instance: include instance level into ImagingStudy when set to True <br>
build_bundles: builds a FHIR bundle including the ImagingStudy when set <br>
create_device: creates the respective Device FHIR resource(s) which performed the ImagingStudy <br>

### Install dependencied

```bash
uv sync
source .venv/bin/activate
```

### Build terminologies

If you wish and are able to, you can run:

```bash
uv run src/build_terminologies.py
```

This script downloads the respective terminologies in the current version from DICOM NEMA and overwrites them in the directory 'resources/terminologies'.

### Run converter

```bash
uv run main.py
```

## Structure

The FHIR Imaging Study id is being generated internally within the library. If selected, the ImagingStudy will be put into a FHIR Bundle.
The Accession Number is usually used as the "identifier" for the ImagingStudy. If this value is unavailable, the DICOM StudyInstanceUID will be used. If both values are not available, the process will stop with an error message and this study can not be converted.

The model is meant to be self-inclusive (to mimic the DICOM structure), it does not produce separate resources for other resource types.
Instead, it uses references to include all of the supporting data.

### References, IDs and identifiers

The respective systems can be set in settings.py as well and are used in the FHIR conversion.

#### ImagingStudy

- ImagingStudy.id: hash("your-system" + "|" + StudyInstanceUID)
- ImagingStudy.identifier: AccessionNumber OR (if AccessionNumber is not available) StudyInstanceUID

#### Patient

- patient_id_positions indicates the number of positions which are used from the PatientID (0-n). If you wish to use all positions available, set a higher number (e.g. 50)
- ImagingStudy.subject.identifier.value: PatientID
- ImagingStudy.subject.reference: "Patient/" + hash("your-system" + "|" + PatientID)

#### Device

If set (see Usage), the converter can also create the associated Device ressource(s), which performed the ImagingStudy. To do this, the converter uses the serial number in the DICOM tag “DeviceSerialNumber” and the manufacturer of the device in the “Manufacturer” tag as well as the model name in the “ManufacturerModelName” tag.
Attention: manufacterer can contain whitespaces!

- Device.identifier.system: "your-system"
- Device.identifier.value: deviceSerialNumber
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
