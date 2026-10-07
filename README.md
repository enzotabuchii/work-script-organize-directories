# Organização de Documentos GCP

Este script tem como objetivo organizar arquivos "soltos" em um bucket do Google Cloud Storage.

## Como Funciona

1. O script se conecta ao bucket do GCP utilizando as credenciais definidas.
2. Para cada arquivo encontrado, o script conecta ao banco de dados SQL Server e faz uma busca utilizando o nome do arquivo. A busca tenta encontrar a qual pessoa aquele arquivo pertence (buscando o `fk_reg_persons_oid` na tabela `reg_documents`).
3. Se o banco de dados retornar o OID, o script gera um novo nome de arquivo adicionando um random byte (para garantir que o nome será único) e define que o novo caminho do arquivo será dentro de uma pasta nomeada com o OID (`prefixo/OID/arquivo_<random-byte>.ext`).
4. Caso o arquivo não seja encontrado no banco, ele será ignorado.
5. O script imprime na tela o "De" (caminho atual) e "Para" (novo caminho) de cada arquivo processado.

## Pré-requisitos

- **Python 3.x**
- As dependências listadas no `requirements.txt` devem estar instaladas.

```bash
pip install -r requirements.txt
```

## Configuração (.env)

Crie um arquivo `.env` na raiz do projeto (use o `.env.example` como base se houver) contendo as seguintes variáveis de ambiente:

```env
GCP_PROJECT_ID=seu_project_id
GCP_BUCKET_NAME=nome_do_bucket
GCP_PREFIX=profile-documents/  # Opcional, o padrão é 'profile-documents/'

DB_SERVER=endereco_do_servidor_sql
DB_DATABASE=nome_do_banco
DB_USERNAME=usuario_do_banco
DB_PASSWORD=senha_do_banco

DRY_RUN=True # TRUE para quando quiser simular
```

_Também é necessário ter as credenciais do GCP configuradas no seu ambiente (por exemplo, exportando a variável `GOOGLE_APPLICATION_CREDENTIALS` apontando para o seu arquivo `.json` de chave de serviço, ou estando autenticado localmente usando a gcloud cli)._

## Como Executar

Basta rodar o arquivo principal através do Python:

```bash
python main.py
```

Caso queira guardar os logs do terminal por ter muitos arquivos...

Em linux:

```bash
python main.py | tee resp.txt
```
