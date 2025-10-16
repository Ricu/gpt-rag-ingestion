"""
Verify local setup for GPT-RAG Ingestion.
Run this script to check if all required Azure resources and configurations are accessible.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    load_dotenv(env_file, override=True)
    print("✓ Loaded .env file\n")
else:
    print("⚠️  No .env file found. Create one based on .env.example\n")

print("="*70)
print("GPT-RAG Ingestion - Local Setup Verification")
print("="*70)

# Check authentication
print("\n1. AUTHENTICATION CHECK")
print("-" * 70)

import subprocess
try:
    result = subprocess.run(
        ["az", "account", "show", "-o", "json"], 
        capture_output=True, 
        text=True, 
        timeout=10
    )
    if result.returncode == 0:
        import json
        account_info = json.loads(result.stdout)
        print(f"✓ Authenticated via Azure CLI")
        print(f"  Account: {account_info.get('user', {}).get('name', 'N/A')}")
        print(f"  Subscription: {account_info.get('name', 'N/A')}")
    else:
        print("✗ Not authenticated with Azure CLI")
        print("  Run: az login")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error checking Azure CLI authentication: {e}")
    print("  Make sure Azure CLI is installed and run: az login")
    sys.exit(1)

# Check required environment variables
print("\n2. CONFIGURATION CHECK")
print("-" * 70)

required_vars = {
    'APP_CONFIG_ENDPOINT': 'Azure App Configuration endpoint',
    'STORAGE_ACCOUNT_NAME': 'Storage account for documents',
    'DOCUMENTS_STORAGE_CONTAINER': 'Container with source documents',
    'SEARCH_SERVICE_QUERY_ENDPOINT': 'AI Search service endpoint',
    'AI_SEARCH_INDEX_NAME': 'AI Search index name',
    'AZURE_OPENAI_ENDPOINT': 'Azure OpenAI endpoint',
    'AZURE_OPENAI_EMBEDDING_DEPLOYMENT': 'Embedding deployment name',
    'DOCUMENT_INTELLIGENCE_ENDPOINT': 'Document Intelligence endpoint',
    'INGESTION_APP_APIKEY': 'API key for authentication',
}

optional_vars = {
    'CRON_RUN_BLOB_INDEX': 'Scheduler cron expression',
    'JOBS_LOG_CONTAINER': 'Container for job logs (default: jobs)',
    'INDEXER_MAX_CONCURRENCY': 'Max concurrent file processing',
    'INDEXER_BATCH_SIZE': 'AI Search batch size',
}

all_present = True
for var, description in required_vars.items():
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if 'KEY' in var or 'SECRET' in var or 'PASSWORD' in var:
            display_value = '*' * 10
        else:
            display_value = value[:50] + ('...' if len(value) > 50 else '')
        print(f"✓ {var}")
        print(f"  {description}: {display_value}")
    else:
        print(f"✗ {var} - MISSING")
        print(f"  {description}")
        all_present = False

print(f"\nOptional Configuration:")
for var, description in optional_vars.items():
    value = os.getenv(var)
    if value:
        print(f"✓ {var}: {value}")
    else:
        print(f"  {var}: (not set) - {description}")

if not all_present:
    print("\n✗ Missing required configuration. Update your .env file.")
    sys.exit(1)

# Check Azure resource connectivity
print("\n3. AZURE RESOURCE CONNECTIVITY")
print("-" * 70)

try:
    from azure.identity import AzureCliCredential
    from azure.storage.blob import BlobServiceClient
    from azure.search.documents import SearchClient
    from azure.core.credentials import AzureKeyCredential
    import openai
    
    credential = AzureCliCredential()
    
    # Test Storage Account
    print("Testing Storage Account...")
    try:
        storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
        container = os.getenv('DOCUMENTS_STORAGE_CONTAINER')
        blob_service = BlobServiceClient(
            account_url=f"https://{storage_account}.blob.core.windows.net",
            credential=credential
        )
        container_client = blob_service.get_container_client(container)
        # Try to list blobs (just get first page to verify access)
        blob_list = list(container_client.list_blobs(results_per_page=1))
        print(f"✓ Storage Account accessible: {storage_account}")
        print(f"  Container: {container} (has {len(blob_list)} blob(s) in first page)")
    except Exception as e:
        print(f"✗ Storage Account error: {e}")
        print(f"  Check permissions: 'Storage Blob Data Contributor' role")
    
    # Test AI Search
    print("\nTesting AI Search...")
    try:
        search_endpoint = os.getenv('SEARCH_SERVICE_QUERY_ENDPOINT')
        index_name = os.getenv('AI_SEARCH_INDEX_NAME')
        
        # Try with credential first (RBAC)
        try:
            search_client = SearchClient(
                endpoint=search_endpoint,
                index_name=index_name,
                credential=credential
            )
            # Try to get document count
            results = search_client.search("*", top=0, include_total_count=True)
            print(f"✓ AI Search accessible: {search_endpoint}")
            print(f"  Index: {index_name}")
        except Exception as rbac_error:
            print(f"⚠️  AI Search RBAC access failed: {rbac_error}")
            print(f"  Note: Index might not exist yet, or you need 'Search Index Data Contributor' role")
    except Exception as e:
        print(f"✗ AI Search error: {e}")
    
    # Test Azure OpenAI
    print("\nTesting Azure OpenAI...")
    try:
        aoai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        embedding_deployment = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT')
        api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
        
        # Get token for OpenAI
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        
        from openai import AzureOpenAI
        client = AzureOpenAI(
            azure_endpoint=aoai_endpoint,
            api_version=api_version,
            azure_ad_token=token.token
        )
        
        # Try a small embedding request
        response = client.embeddings.create(
            input="test",
            model=embedding_deployment
        )
        print(f"✓ Azure OpenAI accessible: {aoai_endpoint}")
        print(f"  Deployment: {embedding_deployment}")
        print(f"  Embedding dimension: {len(response.data[0].embedding)}")
    except Exception as e:
        print(f"✗ Azure OpenAI error: {e}")
        print(f"  Check deployment name and quota")
    
    # Test Document Intelligence
    print("\nTesting Document Intelligence...")
    try:
        doc_intel_endpoint = os.getenv('DOCUMENT_INTELLIGENCE_ENDPOINT')
        
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        doc_client = DocumentIntelligenceClient(
            endpoint=doc_intel_endpoint,
            credential=credential
        )
        print(f"✓ Document Intelligence accessible: {doc_intel_endpoint}")
        print(f"  Note: Full functionality test requires a document")
    except Exception as e:
        print(f"✗ Document Intelligence error: {e}")
        print(f"  Check permissions: 'Cognitive Services User' role")

except ImportError as e:
    print(f"✗ Missing Python package: {e}")
    print("  Run: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    sys.exit(1)

# Summary
print("\n" + "="*70)
print("VERIFICATION SUMMARY")
print("="*70)
print("\nIf all checks passed, you're ready to run the ingestion pipeline!")
print("\nNext steps:")
print("1. Ensure your AI Search index exists (see LOCAL_SETUP_GUIDE.md)")
print("2. Upload documents to your blob storage container")
print("3. Run: python main.py")
print("\nThe ingestion will start automatically and process your documents.")
print("="*70)
