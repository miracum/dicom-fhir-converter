import typed_settings as ts


@ts.settings
class FHIRSettings:
    imagingstudy_meta_profile = "https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-pr-bildgebung-bildgebungsstudie"
    device_meta_profile = "https://www.medizininformatik-initiative.de/fhir/ext/modul-bildgebung/StructureDefinition/mii-pr-bildgebung-geraet"
    imagingstudy_identifier_system: str = "https://fhir.diz.uk-erlangen.de/identifiers/imagingstudy-id"
    patient_identifier_system: str = "https://fhir.diz.uk-erlangen.de/identifiers/patient-id"
    patient_id_positions: int = 9
    device_identifier_system = str = "https://fhir.diz.uk-erlangen.de/identifiers/radiology-device-id"


@ts.settings
class Settings:
    fhir: FHIRSettings
    dicom_input_path: str = "C:/Users/iancuaa/Desktop/study/"
    fhir_output_path: str = "C:/Users/iancuaa/Desktop/output/"
    level_instance: bool = True
    build_bundles: bool = True
    create_device: bool = True


loaders = [
    *ts.default_loaders("dicom2fhir", env_prefix=""),
]

settings = ts.load_settings(
    Settings,
    loaders=loaders
)
