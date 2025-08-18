[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16097921.svg)](https://doi.org/10.5281/zenodo.16097921)
[![CC BY-SA 4.0][cc-by-sa-shield]][cc-by-sa]

# Training

This repository contains curated collections of training resources (contained in various CSV files) related to research software quality and general software and data skills from different research domains and infrastructures collected as part of the EVERSE project (WP5).

The [working spreadsheet](https://docs.google.com/spreadsheets/d/1Ufa4M024k2GeRzP9t64_P9uofXePyGRRf7LOF5vRWTg/edit?gid=395425751#gid=395425751) is used as a living document to constantly add and update training resources the content of which is then periodically released in this repository.

## Documents & deliverables

- [MS15 milestone report "Mapping of the stocktake of training materials across the training initiatives in the research communities of WP4 and a first assessment on gaps to be filled"](https://certhgr.sharepoint.com/:b:/r/sites/INAB-CERTH-Bioinformatics/Shared%20Documents/General/04.Projects/EU-Projects/Funded-Running/EVERSE%20(HORIZON-INFRA-2023-EOSC-01-02)/Consortium/3.Deliverables%20and%20Milestones/final-submitted/WP5/MS15_WP5_Mapping%20of%20the%20stocktake%20of%20training%20materials%20across%20the%20training%20initiatives%20in%20the%20research%20communities%20of%20WP4%20and%20a%20first%20assessment%20on%20gaps%20to%20be%20filled.pdf?csf=1&web=1&e=RUGzm5 )
- [March 2025 GAM workshop spreadsheet](https://docs.google.com/spreadsheets/d/1Ufa4M024k2GeRzP9t64_P9uofXePyGRRf7LOF5vRWTg/edit?gid=1045877253#gid=1045877253) - based on the MS15 report above, we started curating the collected training resources further and classifying them according to the reseach domain, resource type, and software quality dimension they address
- [Working spreadsheet](https://docs.google.com/spreadsheets/d/1Ufa4M024k2GeRzP9t64_P9uofXePyGRRf7LOF5vRWTg/edit?usp=sharing) - we are using this spreadsheet for the ongoing curration and collecting of training resources which are then periodically transferred to this repository

## Training resources

### Training repositories & registries

Collection of [training repositories (training hubs or repositories of training materials) and training registries (containing metadata and references to training materials)](https://github.com/EVERSE-ResearchSoftware/training/blob/main/training_repositories_and_registries.csv).

### Training materials & curricula

Collection of [individual training materials (such as a course, handbook, article, guide, tutorial) and curricula (set of several connected training courses, a learning pathway)](https://github.com/EVERSE-ResearchSoftware/training/blob/main/training_materials_and_curricula.csv).

### Training schools & events 

Collection of [training schools, programmes or events](https://github.com/EVERSE-ResearchSoftware/training/blob/main/training_schools_and_events.csv).

### Reports & publications

Collection of [reports and publications](https://github.com/EVERSE-ResearchSoftware/training/blob/main/reports_and_publications.csv).

### Projects & working groups

Collection of [projects and working groups](https://github.com/EVERSE-ResearchSoftware/training/blob/main/projects.csv) with training component.

### Keywords

Collection of [keywords](https://github.com/EVERSE-ResearchSoftware/training/blob/main/keywords.csv) used to describe and curate various training materials to facilitate searching and tagging in various catalogues.

## Workflow

This repository fetches through GitHub Actions training materials from a Google spreadsheet and translates them into a `.json` file.

### Pre-requisites

- Have a Google spreadsheet. If another spreadhsheet is used: get the ID of your spreadsheet and modify `id` in `src/config.yaml`.
- Have a sheet inside it. If another sheet is used than the one provided in `config.yaml`, modify a `spreadsheet:` object or create another one, see below an example.

    ```bash
    spreadsheet:
        - name: "my_other_sheet"
        gid: 123456789
        skip: False
        schemaType: "Dataset"
    ```

- The sheet must have the same column names as `mapping.tess` entries in `src/config.yaml`. E.g., if `mapping.tess` is `Title` then your sheet must have a column called `Title` in order to extract this information.

### Files

```bash
.
├── .github
│   └── workflows
│       └── update_json.yaml
└── src
    ├── config.yaml
    ├── csv_to_json.py
    └── download_csv.py
```

#### `.github/workflows/update_json.yaml`, the main workflow

1. It will run every day at 1:00AM or when a push to the main branch is done
2. `src/download_csv.py` is called and downloads the sheets of a given Google spreadsheet under a newly created `/csv` directory.
3. Then `src/csv_to_json.py` takes the csv's in the `/csv` directory, converts them as `.json` files and stores them in a created `/json` directory.
4. The workflow then add, commits and push the changes to main.

#### `src/config.yaml`, the configuration file

- `id`: Google spreadsheet identifier
- `spreadsheet`: list of objects {name, gid, skip, schemaType}, each of them representing a sheet of the Google spreadsheet
- `spreadsheet.name`: name given to the csv file when getting fetched by `download_csv.py`
- `spreadsheet.gid`: sheet identifier (Google ID)
- `spreadsheet.skip`: when set to `True`, the `download_csv.py` script will skip the download the `gid` sheet (mainly done for `spreadsheet.name == "keywords"`)
- `spreadsheet.schemaType`: following [schema.org](https://schema.org/), we gave the appropriate `type` to the kind of materials
- `mapping`: list of objects {tess, schema} which acts as a dictionnary, `mapping.tess` is the field in TeSS corresponding to `mapping.schema` in schema.org, they are repsectively key-pair values.
- `mapping.tess`: metadata field known by TeSS, it must match the column names, e.g., if you have column `URLs` instead of `URL` in your Google spreadsheet, please change `mapping.tess` to `URLs` instead of current `URL`
- `mapping.schema`: metadata field known by schema.org

## Licence

This work is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License](LICENSE).

[![CC BY-SA 4.0][cc-by-sa-image]][cc-by-sa]

[cc-by-sa]: http://creativecommons.org/licenses/by-sa/4.0/
[cc-by-sa-image]: https://licensebuttons.net/l/by-sa/4.0/88x31.png
[cc-by-sa-shield]: https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg

## Contact

- [EVERSE WP5 mailing list](everse-wp5@lists.certh.gr)
- [Aleksandra Nenadic](a.nenadic@software.ac.uk)
- [David Chamont](david.chamont@ijclab.in2p3.fr)
- [Daniel Garijo](daniel.garijo@upm.es)
- [Stefan Roiser](Stefan.Roiser@cern.ch)
- [Kenneth Rioja](Kenneth.Brian.Rioja@cern.ch)
