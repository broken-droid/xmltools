import sys
from lxml import etree
from xmlmerge import open_xml, write_xml
import yaml
import os

# Rename channel id's from jibberish to something recognizable
# from  <channel id="673247127d5da5000817b4d6">
#           <display-name>Pluto TV Trending Now</display-name>
# to <channel id="Pluto.TV.Trending.Now.pluto">
# and <programme channel="Pluto.TV.Trending.Now.pluto">

def change_pluto_ids():
    # Load sources config
    sources_path = os.environ.get('EPG_SOURCES_PATH', 'epg_sources.yaml')
    with open(sources_path, 'r', encoding='utf-8') as f:
        sources = yaml.safe_load(f)['sources']

    cache_path = 'cache/' # path to stored input files
    output_path = 'cache/' # path to output file, I want to merge this with other files

    # Load Pluto FR mapping
    mapping_path = os.environ.get('PLUTO_FR_MAPPING_PATH', 'pluto_fr_mapping.yaml')
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping = yaml.safe_load(f).get('mappings', {})

    for source in sources:
        file = source['url']
        suffix = source['suffix']
        outpath = source['output']
        output_programs = []  # Reset for each file
        tree = etree.Element('tv')
        try:
            root = open_xml(file, cache_path)
            channels = root.findall('channel')
            tree.extend(channels)
            for channel in channels:
                old_id = channel.get('id')
                name = channel.find('display-name')
                old_name = name.text
                # Use mapping only for PlutoTV source
                if file == 'https://i.mjh.nz/PlutoTV/fr.xml.gz' and old_id in mapping:
                    mapped_name = mapping[old_id].replace(' ', '.')
                    id = f"{mapped_name}.pluto"
                else:
                    id = old_name.replace(' ', '.')+suffix
                    id = id.replace('&', '.and.')
                    id = id.replace('..','.')
                channel.set('id', id)
                programs = root.findall(f'programme[@channel="{old_id}"]')
                for program in programs:
                    program.set('channel',id)
                    output_programs.append(program)
            tree.extend(output_programs)
        except Exception as e:
            print(f"Error processing {file}: {e}")
            continue
        gzipped = '.gz' in file
        write_xml(os.path.join(output_path, outpath), gzipped, tree)

if __name__ == '__main__':
    change_pluto_ids()
