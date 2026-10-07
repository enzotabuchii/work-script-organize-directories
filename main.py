import os
import secrets
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

def load_all_db_relations(cursor) -> list:
    """Load all relevant relations from DB into memory for fast lookup to avoid N+1 queries."""
    query = """
      SELECT d.fk_reg_persons_oid, c.url_bucket
      FROM reg_document_contents c
      INNER JOIN reg_documents d ON c.fk_reg_documents_id = d.pk_id
      WHERE c.url_bucket IS NOT NULL
    """
    cursor.execute(query)
    return [(str(row[0]) if row[0] else None, str(row[1])) for row in cursor.fetchall() if row[1]]

def get_oid_from_memory(file_name: str, db_relations: list) -> tuple[str | None, str | None]:
    """Find oid and url_bucket in memory based on file_name matching part of the url_bucket."""
    for oid, url in db_relations:
        if file_name in url:
            return oid, url
    return None, None

def main():
    """Testing using DRY RUN"""
    bucket_name = os.getenv("GCP_BUCKET_NAME")
    prefix = os.getenv("GCP_PREFIX", "profile-documents/")

    print(f"\nStarting organization...")
    print(f"Bucket: {bucket_name} | Target prefix: {prefix}")

    project_id = os.getenv("GCP_PROJECT_ID")
    client = storage.Client(project=project_id)

    bucket = client.bucket(bucket_name)

    print("Connecting to DB...")
    conn = db_connection()
    cursor = conn.cursor()
    print("DB connection successfully!\n")

    print("Loading database relations into memory...")
    db_relations = load_all_db_relations(cursor)
    print(f"Loaded {len(db_relations)} relations from database.\n")

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

    loose_files.sort(key=lambda b: b.time_created, reverse=True)

    if not loose_files:
        print("No loose files found to organize in this prefix.")
        conn.close()
        return

    moved_blobs = []
    DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("true", "1", "t", "yes")

    if DRY_RUN:
        print("DRY-RUN MODE")
    else:
        print("EXECUTION MODE")

    try:
        for blob in loose_files:
            file_name_with_ext = os.path.basename(blob.name)

            fk_reg_persons_oid, db_url_bucket = get_oid_from_memory(file_name_with_ext, db_relations)

            if not fk_reg_persons_oid:
                print(f"[SKIPPED] Could not find relationship in the database for the file: {blob.name}")
                continue

            file_name, file_ext = os.path.splitext(file_name_with_ext)
            randomBytes = secrets.token_hex(5)
            new_file_name = f"{file_name}_{randomBytes}{file_ext}"
            final_destination_name = f"{prefix}{fk_reg_persons_oid}/{new_file_name}"

            if db_url_bucket and final_destination_name not in db_url_bucket:
                 print(f"[DB ERROR] The NEW url ({final_destination_name}) is different from the one in the database: {db_url_bucket}")

            if DRY_RUN:
                print(f"[SIMULATION] Move: {blob.name}")
                print(f"            -> To: {final_destination_name}\n")
            else:
                # print(f"[UPDATING] Moving: {blob.name}")
                # print(f"         -> To: {final_destination_name}")

                # new_blob = bucket.rename_blob(blob, final_destination_name)

                # moved_blobs.append((new_blob, blob.name))

                # cursor.execute("UPDATE ... SET url_bucket = ? WHERE ...", new_url_bucket)

                print(f"         [OK] Success.\n")

        if not DRY_RUN:
            print("Execution successfully completed.")
        else:
            print("Organization completed!")

    except Exception as e:
        print(f"\nAn error occurred during execution: {e}")
        if not DRY_RUN and moved_blobs:
            print("Initiating rollback of moved files in GCP...")
            for new_blob, original_name in reversed(moved_blobs):
                try:
                    print(f"  - Undoing: {new_blob.name} -> {original_name}")
                    bucket.rename_blob(new_blob, original_name)
                except Exception as rollback_err:
                    print(f"  Failed to rollback {new_blob.name}: {rollback_err}")

            print("Rollback completed. Database operations were cancelled.")

    finally:
        conn.close()

if __name__ == "__main__":
    required_variables = ["GCP_PROJECT_ID", "GCP_BUCKET_NAME", "DB_SERVER", "DB_DATABASE", "DB_USERNAME", "DB_PASSWORD"]
    missing = [v for v in required_variables if not os.getenv(v)]

    if missing:
        print(f"ERROR: Configure the following variables in the .env file: {', '.join(missing)}")
    else:
        main()
