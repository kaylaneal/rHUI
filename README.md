# Remote HistomicsUI (rHUI)

rHUI is a commands line program that runs analyses traditionally done in Histomics UI remotely via the Digital Slide Archive's (DSA) API. 

## Installation

**Environment Requirements:**
- girder-client
- geojson

1. Clone Repository
```
git clone https://github.com/kaylaneal/
cd 
```

2. Run
```
python run.py --config config.json --analyses NFT-detection
```


## Usage

Running requires a configuration file. Examples can be found [here](/example_config/)

**Minimum Configuration File Requirements:**
- Global Parameters Dictionary
    - dsa_server_url
    - dsa_api_key
    - root_folder_id
        - id of the folder containing the image files
    - item_id
        - item name or the id of the .svs file
        - *notably this is NOT the id of the DSA item, but the item file*
    - batch
        - `true` or `false`
- Analysis Parameters Dictionary
    - varies based on analysis, parameters can be found on HistomicsUI 

**Available Analyses:**
- NFT-detection