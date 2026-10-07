import os
import uuid
import pyodbc
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

def db_connection():
    """Connection with DB"""
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")

    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password}"
    )
    return pyodbc.connect(conn_str)

def oid_fromm_db(file_name: str, cursor) -> tuple[str | None, str | None]:
    """Get oid and url_bucket from database of reg_documents based on pk_id in reg_document_contents"""
    query = """
      SELECT d.fk_reg_persons_oid, c.url_bucket
      FROM reg_document_contents c
      INNER JOIN reg_documents d ON c.fk_reg_documents_id = d.pk_id
      WHERE c.url_bucket LIKE ?
    """

    cursor.execute(query, f"%{file_name}%")

    result = cursor.fetchone()
    if result:
        return str(result[0]), str(result[1])

    return None, None

def main():
    """Testing using DRY RUN"""
    bucket_name = os.getenv("GCP_BUCKET_NAME")
    prefix = os.getenv("GCP_PREFIX", "profile-documents/")

    print(f"\nStarting organization on GCP (DRY-RUN ONLY)...")
    print(f"Bucket: {bucket_name} | Target prefix: {prefix}")

    project_id = os.getenv("GCP_PROJECT_ID")
    client = storage.Client(project=project_id)

    bucket = client.bucket(bucket_name)

    print("Connecting to SQL Server...")
    conn = db_connection()
    cursor = conn.cursor()
    print("Database connection successfully!\n")

    blobs = list(bucket.list_blobs(prefix=prefix))

    if not prefix.endswith('/'):
        prefix += '/'

    loose_files = []
    for blob in blobs:
        if blob.name.endswith('/'):
            continue

        relative_path = blob.name[len(prefix):]
        if '/' not in relative_path:
            loose_files.append(blob)

    # Sort files by creation date in descending order (newest first)
    loose_files.sort(key=lambda b: b.time_created, reverse=True)

    if not loose_files:
        print("No loose files found to organize in this prefix.")
        conn.close()
        return

    for blob in loose_files:
        file_name_with_ext = os.path.basename(blob.name)

        fk_reg_persons_oid, db_url_bucket = oid_fromm_db(file_name_with_ext, cursor)

        if not fk_reg_persons_oid:
            # print(f"[SKIPPED] Could not find relationship in the database for the file: {blob.name}")
            continue

        file_name, file_ext = os.path.splitext(file_name_with_ext)

        new_uuid = str(uuid.uuid4())

        new_file_name = f"{file_name}_{new_uuid}{file_ext}"
        final_destination_name = f"{prefix}{fk_reg_persons_oid}/{new_file_name}"

        if db_url_bucket and final_destination_name not in db_url_bucket:
             print(f"[DB ERROR] The NEW url ({final_destination_name}) is different from the one in the database: {db_url_bucket}")

        print(f"[SIMULATION] Move: {blob.name}")
        print(f"            -> To: {final_destination_name}\n")

    print("Organization (Dry-Run) completed!")
    conn.close()

if __name__ == "__main__":
    required_variables = ["GCP_PROJECT_ID", "GCP_BUCKET_NAME", "DB_SERVER", "DB_DATABASE", "DB_USERNAME", "DB_PASSWORD"]
    missing = [v for v in required_variables if not os.getenv(v)]

    if missing:
        print(f"ERROR: Configure the following variables in the .env file: {', '.join(missing)}")
    else:
        main()
