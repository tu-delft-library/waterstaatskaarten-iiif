import requests
import pandas as pd
import match_meta
import json
from pathlib import Path

# Base url for dlcs
dlcs_base = "https://dlc.services/iiif-resource/7/string1string2string3/{}/{}/{}"

manifest_url = "https://raw.githubusercontent.com/tu-delft-library/waterstaatskaarten-iiif/main/Output/Manifests/{}"

df_photo_loc = pd.read_csv('Input/waterstaatskaart.csv')
df_photo_dlcs = pd.read_csv('Input/waterstaatskaart-dlcs.csv')
df_meta = pd.read_csv('Input/meta_sheet.csv')

df_photo_dlcs['Reference3'].fillna(1, inplace=True)

for index, meta_file in df_meta.iterrows():
    if not pd.isnull(meta_file['urls']):
        meta_filename = meta_file['urls'].split('/')[-1]
        df_meta.loc[index, 'filename'] = meta_filename.replace(' ', '-')

df_photo_group = df_photo_dlcs.groupby(['Reference1', 'Reference2', 'Reference3']).indices

json_collect = []

for i, group in enumerate(df_photo_group.keys()):
    dlcs_group = df_photo_group[group]
    photo_init = df_photo_dlcs.loc[dlcs_group[0]]

    ref1 = photo_init['Reference1']
    ref2 = photo_init['Reference2']
    ref3 = photo_init['Reference3']

    if int(ref3) == 2:
        edition = str(ref2) + "BIS"
    else:
        edition = str(ref2)

    group_meta = df_meta[df_meta['editie'] == edition]

    for j, photo_nr in enumerate(dlcs_group):
        photo_instance = df_photo_dlcs.loc[photo_nr]
        filename = photo_instance['Origin'].split('/')[-1]

        i_match = match_meta.match_file(filename, list(group_meta['filename']))
        meta_match = group_meta.iloc[i_match]

        df_photo_dlcs.loc[photo_nr, list(meta_match.index)] = list(meta_match.values)

    if ref2 == 4 or ref2 == 5:
        dlcs_url = dlcs_base.format(ref1, int(ref2), "")
    else:
        dlcs_url = dlcs_base.format(ref1, int(ref2), int(ref3))

    json_manifest = requests.get(dlcs_url).json()

    df_group = df_photo_dlcs.loc[dlcs_group]

    meta_json = [
        {"label": "Titel",
         "value": ref1.capitalize()},
        {"label": "Editie",
         "value": edition},
        {"label": "Jaren",
         "value": str(df_group['jaar van uitgave'].min()).lstrip("[").rstrip("]") + "-"
                  + str(df_group['jaar van uitgave'].max()).lstrip("[").rstrip("]")}
    ]

    json_manifest['metadata'] = meta_json

    for j, image in enumerate(json_manifest['sequences'][0]['canvases']):
        json_id = int(image['images'][0]['on'].split('=')[-1])

        image_dlcs = df_photo_dlcs[df_photo_dlcs['NumberReference1'] == json_id]
        image_title = image_dlcs['display_title']

        json_manifest['sequences'][0]['canvases'][j]['label'] = image_title.values[0]

    filename = "editie_{}.json".format(edition)
    ref_url = manifest_url.format(filename)
    json_collect.append({
        "@id": ref_url,
        "label": "Editie {}".format(edition),
        "@type": "sc:Manifest"
    })

    json_out = json.dumps(json_manifest, indent=8)
    Path("Output/Manifests").mkdir(parents=True, exist_ok=True)
    with open("Output/Manifests/{}".format(filename), "w") as outfile:
        outfile.write(json_out)

collection_name = "Waterstaatskaarten_collection.json"
# Insert data into collection manifest
json_collection = {"label": "Waterstaatskaarten",
                   # "metadata": meta,
                   "@id": manifest_url.format(collection_name),
                   "@type": "sc:Collection",
                   "@context": "http://iiif.io/api/presentation/2/context.json",
                   "manifests": json_collect}

json_collect_out = json.dumps(json_collection, indent=8)
Path("Output/Manifests").mkdir(parents=True, exist_ok=True)
with open("Output/Manifests/{}".format(collection_name), "w") as outfile:
    outfile.write(json_collect_out)

# for i, photo in df_photo_dlcs.iterrows():
#     ref1 = photo['Reference1']
#     ref2 = photo['Reference2']
#
#     dlcs_url = dlcs_base.format(ref1, ref2)
#     json_manifest = requests.get(dlcs_url)
