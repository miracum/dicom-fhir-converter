import uuid
import argparse
from typing import List
from fhir.resources.R4B.bundle import Bundle, BundleEntry, BundleEntryRequest
from fhir.resources.R4B.resource import Resource

from dicom2fhir import dicom2fhir

# wrapper function to process study
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
            jsonfile = output_path + str(id) + "_imagingStudy.json"
            with open(jsonfile, "w+") as outfile:
                outfile.write(result_resource.json())
        except Exception:
            print("Unable to create ImagingStudy JSON-file (probably missing identifier)")

    #build device
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
            **{"url": f"{resource.resource_type}/{resource.id}", "method": "PUT"}
        )

        entry = BundleEntry.construct()
        entry.request = request
        entry.fullUrl = request.url
        entry.resource = resource

        bundle.entry.append(entry)

    return bundle


def arg_parser():

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-i",
        "--input_path",
        dest="input_path",
        type=str,
        help="The path of the study to be processed."
    )
    parser.add_argument(
        "-o",
        "--output_path",
        dest="output_path",
        type=str,
        help="The path to write the output file in."
    )
    parser.add_argument(
        "-l",
        "--level_instance",
        dest="include_instances",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Option to exclude DICOM instance level from resource"
    )
    parser.add_argument(
        "-b",
        "--build_bundle",
        dest="build_bundle",
        default=False,
        action=argparse.BooleanOptionalAction,
        help="Option to build a FHIR bundle from the result resource"
    )
    parser.add_argument(
        "-d",
        "--create_device",
        dest="create_device",
        default=False,
        action=argparse.BooleanOptionalAction,
        help="Option to create the respective device resource for the performed ImagingStudy"
    )
    return parser


if __name__ == "__main__":

    args = arg_parser().parse_args()

    process_study(args.input_path, args.output_path, args.include_instances, args.build_bundle, args.create_device)
