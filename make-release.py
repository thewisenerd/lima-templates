from urllib import request

import yaml

releases = {
    '18.04': 'release-20230607',
    '20.04': 'release-20230714',
    '22.04': 'release-20230729',
}

img_url = 'https://cloud-images.ubuntu.com/releases/{}/{}/ubuntu-{}-server-cloudimg-{}.img'
sha_url = 'https://cloud-images.ubuntu.com/releases/{}/{}/SHA256SUMS'

lima_arch_map = {
    'amd64': 'x86_64',
    'arm64': 'aarch64',
}


def format_url_template(version: str, release: str, arch: str) -> str:
    return img_url.format(version, release, version, arch)


def format_sha_template(version: str, release: str) -> str:
    return sha_url.format(version, release)


def fetch_url(url: str) -> str:
    with request.urlopen(url) as response:
        return response.read().decode('utf-8')


def fetch_hashes(version: str, release: str) -> dict:
    manifest_raw = fetch_url(format_sha_template(version, release))
    lines = [x.strip().split() for x in manifest_raw.splitlines()]
    hashes = {}
    for line in lines:
        file = line[1].removeprefix('*')
        hashes[file] = line[0]
    return hashes


def make_template(version: str, release: str) -> str:
    hashes = {
        'release': fetch_hashes(version, 'release'),
        release: fetch_hashes(version, release),
    }

    images = []
    for x_rel in [release, 'release']:
        for arch in ['amd64', 'arm64']:
            images.append({
                'location': format_url_template(version, x_rel, arch),
                'arch': lima_arch_map[arch],
                'digest': 'sha256:' + hashes[x_rel]['ubuntu-{}-server-cloudimg-{}.img'.format(version, arch)],
            })

    template = {
        'images': images,
        'mounts': [
            {
                'location': '/tmp/lima',
                'writable': True,
            }
        ]
    }

    return template


def main():
    for version in releases:
        release = releases[version]
        template = make_template(version, release)
        with open(f'{version}.yaml', 'w') as fp:
            yaml.dump(template, fp, default_flow_style=False, sort_keys=False)


if __name__ == '__main__':
    main()
