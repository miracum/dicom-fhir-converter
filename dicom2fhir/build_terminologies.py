#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd

BODYSITE_SNOMED_MAPPING_URL = "https://dicom.nema.org/medical/dicom/current/output/chtml/part16/chapter_L.html"
VIEWPOSITION_MG_SNOMED_MAPPING_URL = "https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4014.html"
VIEWPOSITION_DX_SNOMED_MAPPING_URL = "https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4010.html"
RADIONUCLIDE_NM_MAPPING_URL = "https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_18.html"
RADIOPHARMACEUTICAL_NM_MAPPING_URL = "https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_25.html"
RADIOPHARMACEUTICAL_PT_MAPPING_URL = "https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4021.html"
RADIONUCLIDE_PT_MAPPING_URL = "https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4020.html"


def download_body_part_mapping(url=BODYSITE_SNOMED_MAPPING_URL):
    print(f"Downloading: {url}")
    dfs = pd.read_html(url, converters={"Code Value": str})
    df = dfs[2][["Code Value", "Code Meaning", "Body Part Examined"]]
    df = df.dropna(subset=["Body Part Examined"])
    return df, "bodysite_snomed"


def download_viewposition_MG_mapping(url=VIEWPOSITION_MG_SNOMED_MAPPING_URL):
    print(f"Downloading: {url}")
    dfs = pd.read_html(url, converters={
        "Code Value": str,
        "SNOMED-RT ID": str
    })
    df = dfs[2][["Code Value", "Code Meaning",
                 "ACR MQCM 1999 Equivalent", "SNOMED-RT ID"]]
    return df, "viewposition_MG"


def download_other_mappings(url):
    print(f"Downloading: {url}")
    dfs = pd.read_html(url, converters={
        "Code Value": str,
        "SNOMED-RT ID": str
    })
    df = dfs[2][["Code Value", "Code Meaning", "SNOMED-RT ID"]]
    df = df.dropna(subset=["Code Value"])
    return df


def save_json(df, name):
    out_dir = os.path.join("resources", "terminologies")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{name}.json")
    df.to_json(path, orient="records", force_ascii=False)
    print(f"Saved {len(df)} entries to {path}")


def main():
    mappings = []
    df_bp = download_body_part_mapping()
    mappings.append(df_bp)
    df_vpmg = download_viewposition_MG_mapping()
    mappings.append(df_vpmg)
    df_vpdx = [download_other_mappings(
        url=VIEWPOSITION_DX_SNOMED_MAPPING_URL), "viewposition_DX"]
    mappings.append(df_vpdx)
    df_rn1 = [download_other_mappings(
        url=RADIONUCLIDE_NM_MAPPING_URL), "radionuclide_NM"]
    mappings.append(df_rn1)
    df_rn2 = [download_other_mappings(
        url=RADIONUCLIDE_PT_MAPPING_URL), "radionuclide_PT"]
    mappings.append(df_rn2)
    df_rp1 = [download_other_mappings(
        url=RADIOPHARMACEUTICAL_NM_MAPPING_URL), "radiopharmaceutical_NM"]
    mappings.append(df_rp1)
    df_rp2 = [download_other_mappings(
        url=RADIOPHARMACEUTICAL_PT_MAPPING_URL), "radiopharmaceutical_PT"]
    mappings.append(df_rp2)

    for mapping in mappings:
        save_json(mapping[0], mapping[1])
    print("All terminologies built.")


if __name__ == "__main__":
    main()
