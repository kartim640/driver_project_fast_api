from sqlalchemy import create_engine, text
from app.config import Config


def run_migrations():
    config = Config()
    engine = create_engine(config.database_url)

    with engine.connect() as connection:
        # Add preview_path column if it doesn't exist
        try:
            connection.execute(text("""
                ALTER TABLE files
                ADD COLUMN preview_path VARCHAR(255) NULL
                AFTER file_path;
            """))
            print("Added preview_path column to files table")
        except Exception as e:
            print(f"Note: {str(e)}")

        # Add file_type column if it doesn't exist
        try:
            connection.execute(text("""
                ALTER TABLE files
                ADD COLUMN file_type VARCHAR(50) NULL
                AFTER preview_path;
            """))
            print("Added file_type column to files table")
        except Exception as e:
            print(f"Note: {str(e)}")


if __name__ == "__main__":
    run_migrations()