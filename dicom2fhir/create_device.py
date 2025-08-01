import hashlib
from fhir.resources import R4B as fr
from fhir.resources.R4B import device
from fhir.resources.R4B import identifier
from fhir.resources.R4B import meta

from dicom2fhir import dicom2fhirutils


def create_device(manufacturer, manufacturerModelName, deviceSerialNumber) -> device.Device:

    data = {}

    manufacturer_cleaned = "".join(manufacturer.split())

    m = meta.Meta(profile=[
                  "https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-pr-bildgebung-geraet"])
    data["meta"] = m
    data["status"] = "active"
    data["deviceName"] = create_deviceName(manufacturerModelName)
    data["manufacturer"] = manufacturer
    ident = identifier.Identifier()
    ident.system = "https://fhir.diz.uk-erlangen.de/identifiers/radiology-device-id"
    ident.type = dicom2fhirutils.gen_codeable_concept(
        ["SNO"], "http://terminology.hl7.org/CodeSystem/v2-0203")
    ident.value = manufacturer_cleaned + deviceSerialNumber
    ident_id = manufacturer_cleaned + deviceSerialNumber
    hashedId = hashlib.sha256(
        ident_id.encode('utf-8')).hexdigest()
    data["identifier"] = [ident]
    data["id"] = hashedId

    dev = device.Device(**data)

    return dev, hashedId


def create_deviceName(manufacturerModelName):

    data = {}

    data["name"] = manufacturerModelName
    data["type"] = "model-name"

    return [data]


def create_device_resource(manufacturer, manufacturerModelName, deviceSerialNumber):

    result_resource, id = create_device(
        manufacturer, manufacturerModelName, deviceSerialNumber)

    return result_resource, id
