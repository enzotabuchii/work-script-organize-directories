import os
import re
import shutil
from pathlib import Path

BASE_DIR = Path("./teste_bucket/profile-documents")

# Exemplo: 0003ecb1-1835-445a-9b4f-59138-2024-04-09.jpg -> 0003ecb1-1835-445a-9b4f-59138...
UUID_PATTERN = re.compile(
    r"^([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)

def extrair_id_pasta(nome_arquivo: str) -> str | None:
    """Extrai o UUID correspondente ao nome da pasta."""
    match = UUID_PATTERN.match(nome_arquivo)
    if match:
        return match.group(1)

    partes = nome_arquivo.split("-")
    if len(partes) >= 5:
        possivel_id = "-".join(partes[:5])
        return possivel_id

    return None


def criar_cenario_teste():
    """Cria uma estrutura local para testes."""
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
    (BASE_DIR / f"{id_3}-2025-01-07.pdf").touch()

    print("Ambiente de teste criado com sucesso em:", BASE_DIR.resolve())
    print("Arquivos e pastas iniciais:")
    for item in sorted(BASE_DIR.iterdir()):
        print(f" - [{'PASTA' if item.is_dir() else 'ARQUIVO'}] {item.name}")
    print("-" * 50)


def organizar_diretorio_local(dry_run: bool = False):
    """Varre os arquivos soltos e move para suas respectivas pastas."""
    print(f"\nIniciando organização {'(MODO SIMULAÇÃO / DRY-RUN)' if dry_run else ''}...")

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

        if dry_run:
            print(f"[SIMULAÇÃO] Mover: {arquivo.name} -> {pasta_alvo_nome}/{arquivo.name}")
        else:
            pasta_destino.mkdir(parents=True, exist_ok=True)
            destino_final = pasta_destino / arquivo.name
            shutil.move(str(arquivo), str(destino_final))
            print(f"✔ Movido: {arquivo.name} -> {pasta_alvo_nome}/{arquivo.name}")

    print("\nOrganização finalizada!")


if __name__ == "__main__":
    # Gera os dados fake locais
    criar_cenario_teste()

    # Executa a simulação
    organizar_diretorio_local(dry_run=True)

    # Executa a movimentação real localmente
    organizar_diretorio_local(dry_run=False)

    print("\nEstrutura final resultante:")
    for item in sorted(BASE_DIR.iterdir()):
        if item.is_dir():
            conteudo = [f.name for f in item.iterdir()]
            print(f" {item.name}/ ({len(conteudo)} itens: {conteudo})")
