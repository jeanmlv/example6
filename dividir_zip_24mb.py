from pathlib import Path
import hashlib
import json

PASTA = Path.home() / 'OneDrive - JNJ' / 'Desktop' / 'ard_data'
ZIP = PASTA / 'QUASAR_ALL_ARD.zip'
DESTINO = PASTA / 'quasar_parts'
TAMANHO_PARTE = 24 * 1024 * 1024
BLOCO = 1024 * 1024


def sha256_file(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(BLOCO), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    if not ZIP.is_file():
        raise FileNotFoundError(f'ZIP nao encontrado: {ZIP}')
    DESTINO.mkdir(parents=True, exist_ok=True)
    if list(DESTINO.glob(f'{ZIP.name}.part*')):
        raise RuntimeError(f'Ja existem partes em {DESTINO}. Mova-as ou apague-as antes de executar novamente.')

    partes = []
    with ZIP.open('rb') as origem:
        numero = 0
        while True:
            numero += 1
            nome = f'{ZIP.name}.part{numero:03d}'
            destino = DESTINO / nome
            bytes_escritos = 0
            with destino.open('wb') as saida:
                while bytes_escritos < TAMANHO_PARTE:
                    chunk = origem.read(min(BLOCO, TAMANHO_PARTE - bytes_escritos))
                    if not chunk:
                        break
                    saida.write(chunk)
                    bytes_escritos += len(chunk)
            if bytes_escritos == 0:
                destino.unlink()
                break
            partes.append({'name': nome, 'size_bytes': bytes_escritos, 'sha256': sha256_file(destino)})
            print(f'Criado: {nome} ({bytes_escritos / (1024 * 1024):.2f} MiB)')

    manifesto = {'zip_name': ZIP.name, 'zip_size_bytes': ZIP.stat().st_size,
                 'zip_sha256': sha256_file(ZIP), 'parts': partes}
    manifest_path = DESTINO / 'manifest.json'
    manifest_path.write_text(json.dumps(manifesto, indent=2), encoding='utf-8')
    print(f'\nTotal: {len(partes)} partes')
    print(f'Manifesto: {manifest_path}')
    print(f'SHA256 ZIP: {manifesto["zip_sha256"]}')


if __name__ == '__main__':
    main()
