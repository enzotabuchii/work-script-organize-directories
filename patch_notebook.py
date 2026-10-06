import json

with open('directories_organize.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Ensure uuid is imported in the first code cell
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if 'import uuid' not in source and 'import os' in source:
            cell['source'].insert(0, "import uuid\n")
        break

# Update the method cell
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if 'def extrair_id_pasta' in source:
            new_source = """def extrair_id_pasta(nome_arquivo: str) -> str | None:
    \"\"\"Extrai o UUID correspondente ao nome da pasta.\"\"\"
    match = UUID_PATTERN.match(nome_arquivo)
    if match:
        return match.group(1)

    partes = nome_arquivo.split("-")
    if len(partes) >= 5:
        possivel_id = "-".join(partes[:5])
        return possivel_id

    return None


def criar_cenario_teste():
    if BASE_DIR.exists():
        shutil.rmtree(BASE_DIR.parent)

    BASE_DIR.mkdir(parents=True, exist_ok=True)

    id_1 = "00076ac7-fbc2-42f3-9620-8cb4f19bca5e"
    (BASE_DIR / id_1).mkdir(exist_ok=True)
    (BASE_DIR / id_1 / "avatar.png").touch()

    (BASE_DIR / f"{id_1}-2024-05-15.jpg").touch()

    id_2 = "0003ecb1-1835-445a-9b4f-59138d612345"
    id_3 = "0008b6b4-447a-4bba-b1ca-09a7fed7ced8"
    (BASE_DIR / f"{id_2}-2024-04-09.jpg").touch()
    (BASE_DIR / f"{id_3}.pdf").touch() # Simulate just the OID

    print("Ambiente de teste criado com sucesso em:", BASE_DIR.resolve())
    print("Arquivos e pastas iniciais:")
    for item in sorted(BASE_DIR.iterdir()):
        print(f" - [{'PASTA' if item.is_dir() else 'ARQUIVO'}] {item.name}")
    print("-" * 50)


def organizar_diretorio_local(dry_run: bool = False):
    \"\"\"Varre os arquivos soltos e move para suas respectivas pastas com o novo formato.\"\"\"
    print(f"\\nIniciando organização {'(DRY-RUN)' if dry_run else ''}...")

    itens = list(BASE_DIR.iterdir())
    arquivos_soltos = [item for item in itens if item.is_file()]

    if not arquivos_soltos:
        print("Nenhum arquivo solto encontrado para organizar.")
        return

    for arquivo in arquivos_soltos:
        pasta_alvo_nome = extrair_id_pasta(arquivo.name)

        if not pasta_alvo_nome:
            print(f"Não foi possível identificar o ID de: {arquivo.name}")
            continue

        pasta_destino = BASE_DIR / pasta_alvo_nome
        
        # Gerar o novo nome do arquivo: {nome_original}_{uuid}{extensao}
        extensao = arquivo.suffix
        nome_sem_extensao = arquivo.stem
        novo_uuid = str(uuid.uuid4())
        novo_nome_arquivo = f"{nome_sem_extensao}_{novo_uuid}{extensao}"
        
        destino_final = pasta_destino / novo_nome_arquivo

        if dry_run:
            print(f"[SIMULAÇÃO] Mover: {arquivo.name} -> {pasta_alvo_nome}/{novo_nome_arquivo}")
        else:
            pasta_destino.mkdir(parents=True, exist_ok=True)
            shutil.move(str(arquivo), str(destino_final))
            print(f"Movido: {arquivo.name} -> {pasta_alvo_nome}/{novo_nome_arquivo}")

    print("\\nOrganização finalizada!")
"""
            # Convert to notebook lines
            cell['source'] = [line + '\n' for line in new_source.split('\n')][:-1]
            # Replace the last line without \n if we want to be exact, but it's fine.

with open('directories_organize.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
