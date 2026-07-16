# IMPORTS
import argparse

import girder_client
import json
import geojson
import sys

# import logging
# # 1. Enable DEBUG logs globally
# logging.basicConfig(level=logging.DEBUG)

# # 2. Force the internal urllib3 logger to output everything
# logging.getLogger("urllib3").setLevel(logging.DEBUG)

#############
# Utilities #
#############

def check_config(config_file:str) -> dict:
    '''
    Ensure configuration file exists and is formatted correctly.

    Parameters
    ----------
    config_file: str
        filepath to the json configuration file
    
    Returns
    ----------
    config: dict
        dictionary object containing parameters for analysis

    '''
    try:
        with open(config_file, 'r') as cf:
            config = json.load(cf)

        if 'global' not in config.keys():
            print("\n*** Configuration file should include a dictionary labeled 'global'. ***\n")
            return None
        
        if 'dsa_server_url' not in config['global'].keys() or config['global']['dsa_server_url'] == '':
            print("\n*** DSA server URL must be defined in the global parameters dictionary! ***\n")
            return None
        
        if 'dsa_api_key' not in config['global'].keys() or config['global']['dsa_api_key'] == '':
            print("\n*** DSA API key must be defined in the global parameters dictionary! ***\n")
            return None
        
    except Exception as e:
        print("\n*** Error reading config file ***\n", e)
        return None

    return config

def _init_DSA_client(config:dict) -> girder_client.GirderClient:
    '''
    Connect to DSA API with URL and API Key

    Parameters
    ----------
    config: dict
        dictionary containing configuration parameters
    
    Returns
    ----------
    gc: girder_client.GirderClient
        girder client connection to perform api calls through

    '''
    url = config['global']['dsa_server_url']
    key = config['global']['dsa_api_key']

    try:
        gc = girder_client.GirderClient(apiUrl = url)
        gc.authenticate(apiKey = key)
    except Exception as e:
        print("\n*** Error initializing DSA connection. Canceling script. ***\n", e)
        sys.exit()
    
    return gc

def _get_file_id(gc:girder_client.GirderClient, config:dict) -> str:
    '''
    
    '''
    # try to get with id
    try:
        fileID = gc.get(f'item/{config['global']['item_id']}')['largeImage']['fileId']
    except Exception as e:
        try:
            print("Image file not found with image item id value. Trying with image name.")
            fileID = gc.get('item', parameters = {'name': config['global']['item_id'], 'folderId': config['global']['root_folder_id'], 'limit': 1})['largeImage']['fileId']
        except Exception as e:
            print("Image file not found with image item id or name. Testing if file id was passed.")
            fileID = gc.get(f'file/{config['global']['item_id']}')['_id']
    print("file id: ", fileID)
    return fileID

def json_to_roi(roi_filename:str):
    '''
    
    '''
    with open(roi_filename, 'r') as f:
        annotation = geojson.load(f)

    feature_iter = iter(annotation)
    if type(annotation) == geojson.feature.FeatureCollection:
        feature_iter = iter(annotation.features)

    rois = []

    for f in feature_iter:
        coordinates = f['geometry']['coordinates']
        
        for coord in coordinates:
            if isinstance(coord[0], list) and isinstance(coord[0][0], (int, float)):            # One Element in Feature
                for c in coord:
                    rois.extend(c)
                    # rois.extend([-1,-1])
            else:                                                                               # Multiple Elements in Feature
                for i in range(len(coord)):
                    component = coord[i]
                    for c in component:
                        rois.extend(c)
                    rois.extend([-1,-1])
            rois.extend([-1,-1])

    roi = [r for r in rois if r != 0]
    while roi[-1] == -1:
        roi.pop()

    return roi

def run_NFT(config:dict):
    '''
    
    
    '''
    gc = _init_DSA_client(config)

    if config['global']['batch']:
        # img_file_id = r'^slide_.*\.svs$'
        img_file_id = r'\.svs$'
    else:
        img_file_id = _get_file_id(gc, config)

    if config['NFT-detection'].get('region','').endswith('.json') or config['NFT-detection'].get('region','').endswith('.geojson'):
        new_region = json_to_roi(config['NFT-detection']['region'])
        config['NFT-detection']['region'] = str(new_region)
    
    nft_params = {
        'in_file': img_file_id,
        'in_file_folder': config['global'].get("root_folder_id", ""),
        'docname': config['NFT-detection'].get("docname", "NFTs"),
        'mask_mag': config['NFT-detection'].get("mask_mag", 2),
        'max_det': config['NFT-detection'].get("max_det", 300),
        'iou_thr': config['NFT-detection'].get("iou_thr", 0.4),
        'conf_thr': config['NFT-detection'].get("conf_thr", 0.2),
        'contained_thr': config['NFT-detection'].get("contained_thr", 0.6),
        'mask_thr': config['NFT-detection'].get("mask_thr", 0.2),
        'mag': config['NFT-detection'].get("mag", 20),
        'tissueAnnotationFile_folder': config['NFT-detection'].get("tissueAnnotationFile_folder", config['global']['root_folder_id']),
        'tissueAnnotationFile': config['NFT-detection'].get("tissueAnnotationFile", "tissueAnnotationFile.anot"),
        'device': config['NFT-detection'].get("device", "cuda"),
        'region': config['NFT-detection'].get("region", "[-1,-1,-1,-1]")
    }
    
    return gc.post('slicer_cli_web/jvizcar_neurotk_archive/NFTDetection/run', parameters = nft_params)

##############
#    Main    #
##############

def main(config_path:str, 
         root_folder:str = None, 
         item_name:str = None, 
         batch:bool = False, 
         analysis:str = None):

    # Configure Environment:

    config = check_config(config_file = config_path)

    if not config:
        print("\nFatal error occured in config file check. Please check documentation for format and variable requirements.")
        sys.exit()

    if not item_name:
        if config['global']['item_id']:
            item_name = config['global']['item_id']
        elif not batch:
            if not config['global']['batch']:
                print("\nIf not running on all items in a DSA folder, then an item name must be provided. Canceling script.")
                sys.exit()
            else:
                batch = True
        elif not root_folder:
            if not config['global']['root_folder_id']:
                print("\nFolder Girder ID is required to run analysis. Canceling script.")
                sys.exit()
            else:
                root_folder = config['global']['root_folder_id']
        else:
            print("\nRunning analysis on all items found in parent folder on the DSA.\n")
    else:
        config['global']['item_id'] = item_name
        print(f"\nRunning analysis only on {item_name}.\n")

    if analysis:
        analyses = analysis.split(',')
    else:
        print("\nNo analyses provided. Please check documentation for avaliable analysis options.") 
        sys.exit()

    # Run Analysis:
    for a in analyses:
        match a:
            case 'NFT-detection':
                nft_response = run_NFT(config)
                print(nft_response)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog = "HistomicsUI CLI", description = "Run HistomicsUI Analyses via Command Line and Girder API.")

    parser.add_argument('--config', required = True, help = "Path to JSON configuration file.")
    parser.add_argument('--root-folder-id', default = None, help = "Girder ID of the parent folder containing images to analyze.")
    parser.add_argument('--item-name', default = None, help = "Item name saved in DSA. Used to get Girder ID value.")
    parser.add_argument('--batch', default = False, choices = [True, False], help = "Run analysis on items in the parent folder.")
    parser.add_argument('--analyses', choices = [None, 'NFT-detection'], default = None, help = "Which analysis/analyses to run. If multiple, use a comma separated list.")
    args = parser.parse_args()

    main(
        config_path = args.config,
        root_folder = args.root_folder_id,
        item_name = args.item_name,
        batch = args.batch,
        analysis = args.analyses,
    )