import uuid
from typing import List
from fhir.resources.R4B.bundle import Bundle, BundleEntry, BundleEntryRequest
from fhir.resources.R4B.resource import Resource
#import kafka_client

from dicom2fhir import dicom2fhir

input_path = "C:/Users/iancuaa/Desktop/study_MEO-2024096495/" #add input path of dicom study
output_path = "C:/Users/iancuaa/Desktop/output/" #add output path for json-files


# wrapper function to process study
def process_study(root_path, output_path):
    
    result_resource, study_instance_uid, accession_nr = dicom2fhir.process_dicom_2_fhir(
        str(root_path)
    )

    # build bundle
    # result_list = []
    # result_list.append(result_resource)
    # result_bundle = build_from_resources(result_list, study_instance_uid)

    # send to Kafka
    # kafka_client.send_to_topic(output_topic, result_bundle, study_instance_uid)

    try:
        jsonfile = output_path + str(accession_nr) + "_imagingStudy.json"
        with open(jsonfile, "w+") as outfile:
            outfile.write(result_resource.json())
    except Exception:
        print("Unable to create JSON-file (probably missing identifier)")


# build FHIR bundle from resource
def build_from_resources(resources: List[Resource], id: str | None) -> Bundle:
    bundle_id = id

    if bundle_id is None:
        bundle_id = str(uuid.uuid4())

    bundle = Bundle(**{"id": bundle_id, "type": "transaction", "entry": []})

    for resource in resources:
        request = BundleEntryRequest(
            **{"url": f"{resource.resource_type}/{resource.id}", "method": "PUT"}
        )

        entry = BundleEntry.construct()
        entry.request = request
        entry.fullUrl = request.url
        entry.resource = resource

        bundle.entry.append(entry)

    return bundle

process_study(input_path, output_path)
