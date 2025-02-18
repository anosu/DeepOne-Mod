import re
import sys
from pathlib import Path

import httpx
from packaging.version import Version

from util import fs

from util.crypto import hash_md5

BASE_DIR = Path('./games/mod/deepone')
FONT_PATH = 'res/raw-assets/c6/c6fd2960-337d-47ea-8e1b-95e6e4fe38ee/Humming-D.ttf'
SCRIPT_URL = "https://dmm-api.ntr.best/mod/deepone/script/"
LOAD_ADV_PATTERN = r'loadAdvFileEx: ?function\((.), ?(.), ?(.), ?.\) ?{[^:]*}'
LOAD_FILE_CALL_PATTERN = r'this\.loadFileExInner\(., ?., ?(.),'
IS_RES_NEED_UPDATE_CALL_PATTERN = r'var (\S) ?= ?this.isResNeedUpdate\(., ?., ?(.), ?.\);'
MOD_MANIFEST = {
    "packageUrl": "https://dmm-api.ntr.best/mod/deepone/assets/",
    "remoteManifestUrl": "https://dmm-api.ntr.best/mod/deepone/assets/project.manifest",
    "remoteVersionUrl": "https://dmm-api.ntr.best/mod/deepone/assets/version.manifest"
}

proxy = sys.argv[1].strip('"')
client = httpx.Client(proxy=proxy)


def replacer(match: re.Match[str]) -> str:
    function = match.group()
    name_id, path_id, md5_id = match.groups()
    nested_match = re.search(LOAD_FILE_CALL_PATTERN, function)
    url_id = nested_match.group(1)
    nested_index = nested_match.start()
    mod_segment = (
        f'if ({name_id}.startsWith("download/adv/text/")) {{\n'
        f'{url_id} = "{SCRIPT_URL}" + {name_id} + "?path=" + {path_id} + "&md5=" + {md5_id};'
        f'\n}}\n'
    )
    return f'{function[:nested_index]}{mod_segment}{function[nested_index:]}'


def insert_mod_segment(src: str) -> str:
    mod_src = re.sub(LOAD_ADV_PATTERN, replacer, src)
    call_sentence = re.search(IS_RES_NEED_UPDATE_CALL_PATTERN, mod_src)
    end_index = call_sentence.end()
    result_id, name_id = call_sentence.groups()
    mod_segment = (
        f'\nif ({name_id}.startsWith("adv/text/")) {{\n'
        f'{result_id}.need = true;'
        f'\n}}'
    )
    return f'{mod_src[:end_index]}{mod_segment}{mod_src[end_index:]}'


def update_mod():
    local_manifest = fs.read_json(BASE_DIR / 'assets' / 'version.manifest')
    local_version = local_manifest['version']
    remote_version_url = local_manifest['originalRemoteVersionUrl']

    remote_manifest = client.get(remote_version_url).json()
    remote_version = remote_manifest['version']

    print(f'Local version: {local_version}')
    print(f'Remote version: {remote_version}')

    need_update = Version(remote_version) > Version(local_version)
    if not need_update:
        print('No need to update')
        return

    package_url = remote_manifest['packageUrl']
    remote_manifest_url = remote_manifest['remoteManifestUrl']

    remote_manifest['originalPackageUrl'] = remote_manifest['packageUrl']
    remote_manifest['originalRemoteManifestUrl'] = remote_manifest['remoteManifestUrl']
    remote_manifest['originalRemoteVersionUrl'] = remote_manifest['remoteVersionUrl']

    project_js = client.get(package_url + 'src/project.js')
    mod_project_js = insert_mod_segment(project_js.text).encode()

    project_js_size = len(mod_project_js)
    project_js_md5 = hash_md5(mod_project_js).hex()

    font = (BASE_DIR / 'assets' / FONT_PATH).read_bytes()
    font_size = len(font)
    font_md5 = hash_md5(font).hex()

    project_manifest = client.get(remote_manifest_url).json()
    project_manifest['assets']['src/project.js']['size'] = project_js_size
    project_manifest['assets']['src/project.js']['md5'] = project_js_md5
    project_manifest['assets'][FONT_PATH]['size'] = font_size
    project_manifest['assets'][FONT_PATH]['md5'] = font_md5

    print(f'Mod project.js size: {project_js_size}')
    print(f'Mod project.js md5: {project_js_md5}')

    remote_manifest.update(MOD_MANIFEST)
    project_manifest.update(MOD_MANIFEST)

    fs.write_bytes(BASE_DIR / 'assets' / 'src' / 'project.js', mod_project_js)
    fs.write_json(BASE_DIR / 'assets' / 'version.manifest', remote_manifest)
    fs.write_json(BASE_DIR / 'assets' / 'project.manifest', project_manifest, indent=None, separators=(',', ':'))


if __name__ == '__main__':
    update_mod()
    print('Finished')
