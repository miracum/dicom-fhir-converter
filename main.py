import uuid
from typing import List
from fhir.resources.R4B.bundle import Bundle, BundleEntry, BundleEntryRequest
from fhir.resources.R4B.resource import Resource
from src.settings import settings

from src import dicom2fhir


def process_study(root_path, output_path, include_instances, build_bundle, create_device):

    result_resource, study_instance_uid, accession_nr, dev_list = dicom2fhir.process_dicom_2_fhir(
        str(root_path), include_instances
    )

    study_id = accession_nr
    if accession_nr is None:
        study_id = str(study_instance_uid)
        if study_instance_uid is None:
            raise ValueError(
                "No suitable ID in DICOM file available to set the identifier")

    # build imagingstudy bundle
    if build_bundle:
        result_list = []
        result_list.append(result_resource)
        result_bundle = build_from_resources(result_list, study_instance_uid)
        try:
            jsonfile = output_path + str(study_id) + "_bundle.json"
            with open(jsonfile, "w+") as outfile:
                outfile.write(result_bundle.json())
        except Exception:
            print("Unable to create ImagingStudy JSON-file (probably missing identifier)")
    else:
        try:
            jsonfile = output_path + str(study_id) + "_imagingStudy.json"
            with open(jsonfile, "w+") as outfile:
                outfile.write(result_resource.json())
        except Exception:
            print("Unable to create ImagingStudy JSON-file (probably missing identifier)")

    # build device
    if create_device:
        for dev in dev_list:
            dev_id = dev[1]
            dev_resource = dev[0]
            try:
                jsonfile = output_path + "Device_" + str(dev_id) + ".json"
                with open(jsonfile, "w+") as outfile:
                    outfile.write(dev_resource.json())
            except Exception:
                print("Unable to create device JSON-file")

# build FHIR bundle from resource


def build_from_resources(resources: List[Resource], id: str | None) -> Bundle:
    bundle_id = id

    if bundle_id is None:
        bundle_id = str(uuid.uuid4())

    bundle = Bundle(**{"id": bundle_id, "type": "transaction", "entry": []})

    for resource in resources:
        request = BundleEntryRequest(
            **{"url": f"{resource.__resource_type__}/{resource.id}", "method": "PUT"}
        )

        entry = BundleEntry.model_construct()
        entry.request = request
        entry.fullUrl = request.url
        entry.resource = resource

        bundle.entry.append(entry)

    return bundle


if __name__ == "__main__":

    process_study(settings.dicom_input_path, settings.fhir_output_path,
                  settings.level_instance, settings.build_bundles, settings.create_device)
