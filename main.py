# Import packages
import requests
import pandas as pd
import json
from pathlib import Path
import match_meta

# Base url for dlcs
dlcs_base = "https://dlc.services/iiif-resource/7/string1string2string3/{}/{}/{}"
# Base url for github
manifest_url = "https://raw.githubusercontent.com/tu-delft-library/waterstaatskaarten-iiif/main/Output/Manifests/{}"

# Import data
df_photo_loc = pd.read_csv('Input/waterstaatskaart.csv')
df_photo_dlcs = pd.read_csv('Input/waterstaatskaart-dlcs.csv')
df_meta = pd.read_csv('Input/meta_sheet.csv')

# Replace na for "1"
df_photo_dlcs['Reference3'].fillna(1, inplace=True)

# Extract filename from url and insert in new column
for index, meta_file in df_meta.iterrows():
    if not pd.isnull(meta_file['urls']):
        meta_filename = meta_file['urls'].split('/')[-1]
        df_meta.loc[index, 'filename'] = meta_filename.replace(' ', '-')

# Group dlcs data by references
df_photo_group = df_photo_dlcs.groupby(['Reference1', 'Reference2', 'Reference3']).indices

# empty list for collection manifest
json_collect = []

# Start loop through grouped data to match metadata with dlcs data and generate .json manifests
for i, group in enumerate(df_photo_group.keys()):
    # Get index numbers of the dlcs images in the group
    dlcs_group = df_photo_group[group]
    # Get data of first dlcs image in group to get the reference data
    photo_init = df_photo_dlcs.loc[dlcs_group[0]]

    # Extract reference data
    ref1 = photo_init['Reference1']
    ref2 = photo_init['Reference2']
    ref3 = photo_init['Reference3']

    # Check if it is a "BIS" edition to match with meta data
    if int(ref3) == 2:
        edition = str(ref2) + "BIS"
    else:
        edition = str(ref2)

    # Get specific edition group from metadata for matching
    group_meta = df_meta[df_meta['editie'] == edition]

    # Start matching loop
    for j, photo_nr in enumerate(dlcs_group):
        # Get data from specific image
        photo_instance = df_photo_dlcs.loc[photo_nr]
        # Extract filename
        filename = photo_instance['Origin'].split('/')[-1]

        # Find the closest match in the metadata set
        i_match = match_meta.match_file(filename, list(group_meta['filename']))
        # Extract the metadata of the closest match
        meta_match = group_meta.iloc[i_match]

        # Add metadata to dlcs dataframe
        df_photo_dlcs.loc[photo_nr, list(meta_match.index)] = list(meta_match.values)

    # Generate url form dlcs .json request
    if ref2 == 4 or ref2 == 5:
        dlcs_url = dlcs_base.format(ref1, int(ref2), "")
    else:
        dlcs_url = dlcs_base.format(ref1, int(ref2), int(ref3))

    # Perfrom .json request
    json_manifest = requests.get(dlcs_url).json()

    # Get specific group rows from dlcs dataframe
    df_group = df_photo_dlcs.loc[dlcs_group]

    # Create metadata
    meta_json = [
        {"label": "Titel",
         "value": ref1.capitalize()},
        {"label": "Editie",
         "value": edition},
        {"label": "Jaren",
         "value": str(df_group['jaar van uitgave'].min()).lstrip("[").rstrip("]") + "-"
                  + str(df_group['jaar van uitgave'].max()).lstrip("[").rstrip("]")}
    ]

    # Insert metadata
    json_manifest['metadata'] = meta_json

    # Loop through each image instance from .json to insert label tag
    for j, image in enumerate(json_manifest['sequences'][0]['canvases']):
        # Extract id number from url in .json file
        json_id = int(image['images'][0]['on'].split('=')[-1])

        # Find specific photo in dlcs dataframe using id number
        image_dlcs = df_photo_dlcs[df_photo_dlcs['NumberReference1'] == json_id]
        # Extract image title from dataframe
        image_title = image_dlcs['display_title']
        # Insert image title to .json file
        json_manifest['sequences'][0]['canvases'][j]['label'] = image_title.values[0]

    # Generate filename
    filename = "editie_{}.json".format(edition)
    # Generate specific url of .json manifest
    ref_url = manifest_url.format(filename)
    # Insert data of current .json manifest for collection manifest
    json_collect.append({
        "@id": ref_url,
        "label": "Editie {}".format(edition),
        "@type": "sc:Manifest"
    })

    # Output .json manifest file
    json_out = json.dumps(json_manifest, indent=8)
    Path("Output/Manifests").mkdir(parents=True, exist_ok=True)
    with open("Output/Manifests/{}".format(filename), "w") as outfile:
        outfile.write(json_out)

# Collection manifest name
collection_name = "Waterstaatskaarten_collection.json"
# Insert data into collection manifest
json_collection = {"label": "Waterstaatskaarten",
                   # "metadata": meta,
                   "@id": manifest_url.format(collection_name),
                   "@type": "sc:Collection",
                   "@context": "http://iiif.io/api/presentation/2/context.json",
                   "manifests": json_collect}

# Export .json collection manifest
json_collect_out = json.dumps(json_collection, indent=8)
Path("Output/Manifests").mkdir(parents=True, exist_ok=True)
with open("Output/Manifests/{}".format(collection_name), "w") as outfile:
    outfile.write(json_collect_out)
