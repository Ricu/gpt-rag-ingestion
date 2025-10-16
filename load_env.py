"""
Helper script to load environment variables from .env file.
This makes it easier to run the app locally with environment-based configuration.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

def load_local_env():
    """Load environment variables from .env file if it exists."""
    env_path = Path(__file__).parent / '.env'
    
    if env_path.exists():
        print(f"Loading environment variables from {env_path}")
        load_dotenv(env_path, override=True)
        print("✓ Environment variables loaded")
        
        # Verify critical variables
        critical_vars = [
            'APP_CONFIG_ENDPOINT',
        ]
        
        missing = [var for var in critical_vars if not os.getenv(var)]
        if missing:
            print(f"⚠️  Warning: Missing critical environment variables: {', '.join(missing)}")
            print("   Make sure to create a .env file based on .env.example")
        else:
            print("✓ Critical environment variables found")
            
        # Check if using env vars only mode
        if os.getenv('allow_environment_variables', '').lower() in ('true', '1', 'yes'):
            print("✓ Using environment variables mode (allow_environment_variables=true)")
            additional_vars = [
                'STORAGE_ACCOUNT_NAME',
                'DOCUMENTS_STORAGE_CONTAINER',
                'SEARCH_SERVICE_QUERY_ENDPOINT',
                'AI_SEARCH_INDEX_NAME',
                'AZURE_OPENAI_ENDPOINT',
                'AZURE_OPENAI_EMBEDDING_DEPLOYMENT',
                'INGESTION_APP_APIKEY'
            ]
            missing_additional = [var for var in additional_vars if not os.getenv(var)]
            if missing_additional:
                print(f"⚠️  Warning: In env-only mode, missing: {', '.join(missing_additional)}")
    else:
        print(f"⚠️  No .env file found at {env_path}")
        print("   Copy .env.example to .env and fill in your Azure resource values")
        print("   Or run: copy .env.example .env")

if __name__ == "__main__":
    load_local_env()
    
    # Show loaded configuration (without secrets)
    print("\n" + "="*60)
    print("Current Configuration (non-sensitive values)")
    print("="*60)
    
    display_vars = [
        'APP_CONFIG_ENDPOINT',
        'STORAGE_ACCOUNT_NAME',
        'DOCUMENTS_STORAGE_CONTAINER',
        'SEARCH_SERVICE_QUERY_ENDPOINT',
        'AI_SEARCH_INDEX_NAME',
        'AZURE_OPENAI_ENDPOINT',
        'DOCUMENT_INTELLIGENCE_ENDPOINT',
        'CRON_RUN_BLOB_INDEX',
        'CRON_RUN_BLOB_PURGE',
        'SCHEDULER_TIMEZONE',
        'INDEXER_MAX_CONCURRENCY',
        'INDEXER_BATCH_SIZE',
        'allow_environment_variables'
    ]
    
    for var in display_vars:
        value = os.getenv(var, '(not set)')
        print(f"{var}: {value}")
    
    print("="*60)
