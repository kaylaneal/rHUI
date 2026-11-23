## Using rHUI

Running requires a configuration file. Examples can be found [here](/example_config/)

**Minimum Configuration File Requirements:**
- Global Parameters Dictionary
    - dsa_server_url
    - dsa_api_key
    - root_folder_id
        - id of the folder containing the image files
        - *empty string for single run with batch set to false*
    - item_id
        - item name or the id of the .svs file
        - *notably this is NOT the id of the DSA item, but the item file*
    - batch
        - `true` or `false`
- Analysis Parameters Dictionary
    - varies based on analysis, parameters can be found on HistomicsUI 

**Available Analyses:**
- NFT-detection via [jvizcar/neurotk docker image](https://hub.docker.com/r/jvizcar/neurotk)