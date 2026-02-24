import hashlib
from fhir.resources.R4B import device
from fhir.resources.R4B import identifier
from fhir.resources.R4B import meta

from dicom2fhir import dicom2fhirutils
from settings import settings

SERIAL_NUMBER_SYS = "http://dicom.nema.org/resources/ontology/DCM"


def create_device(manufacturer, manufacturerModelName, deviceSerialNumber) -> device.Device:

    data = {}

    m = meta.Meta(profile=[settings.fhir.device_meta_profile])
    data["meta"] = m
    data["status"] = "active"
    data["deviceName"] = create_deviceName(manufacturerModelName)
    data["manufacturer"] = manufacturer
    ident = identifier.Identifier()
    ident.system = settings.fhir.device_identifier_system
    ident.type = dicom2fhirutils.gen_codeable_concept(
        ["SNO"], SERIAL_NUMBER_SYS)
    ident.value = deviceSerialNumber
    ident_id = deviceSerialNumber + "|" + manufacturer
    hashedIdentifier = hashlib.sha256(
        ident_id.encode('utf-8')).hexdigest()
    data["identifier"] = [ident]
    data["id"] = hashedIdentifier

    dev = device.Device(**data)

    return dev, hashedIdentifier


def create_deviceName(manufacturerModelName):

    data = {}

    data["name"] = manufacturerModelName
    data["type"] = "model-name"

    return [data]


def create_device_resource(manufacturer, manufacturerModelName, deviceSerialNumber):

    result_resource, id = create_device(
        manufacturer, manufacturerModelName, deviceSerialNumber)

    return result_resource, id
