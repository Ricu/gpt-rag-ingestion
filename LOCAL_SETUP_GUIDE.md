# Local Setup Guide for GPT-RAG Ingestion

This guide will help you run the GPT-RAG ingestion pipeline locally to build a search index from your blob storage.

## Prerequisites

### 1. Software Requirements
- **Python 3.12** - [Download](https://www.python.org/downloads/release/python-3120/)
- **Azure CLI** - [Install](https://learn.microsoft.com/cli/azure/install-azure-cli)
- **Git** (already installed since you have this repo)

### 2. Azure Resources
You mentioned you already have:
- ✅ **Azure Blob Storage** - for source documents
- ✅ **Azure AI Foundry** (Azure OpenAI) - for embeddings
- ✅ **Azure AI Search** - for the search index

You'll also need:
- **Azure App Configuration** - for storing configuration (recommended) OR you can use environment variables only
- **Azure Document Intelligence** - for processing PDFs (optional but recommended for best results)

### 3. Azure Permissions
Your Azure account needs these roles:

| Resource | Role | Purpose |
|----------|------|---------|
| Storage Account | Storage Blob Data Contributor | Read source files, write logs |
| AI Search | Search Index Data Contributor | Write chunks to index |
| Azure OpenAI | Cognitive Services OpenAI User | Generate embeddings |
| App Configuration | App Configuration Data Reader | Read configuration (if using) |
| Document Intelligence | Cognitive Services User | Process PDFs (if using) |

## Quick Start

### Step 1: Authenticate with Azure

```bash
az login
```

This allows the app to use your Azure credentials locally.

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment

**Option A: Using Azure App Configuration (Recommended)**

1. Create an Azure App Configuration resource if you don't have one
2. Add your settings to App Configuration with label `gpt-rag-ingestion` or `gpt-rag`
3. Create a `.env` file:

```bash
# Copy the example
copy .env.example .env

# Edit .env and set at minimum:
APP_CONFIG_ENDPOINT=https://your-appconfig-name.azconfig.io
```

**Option B: Using Environment Variables Only**

If you don't want to use App Configuration, you can set all variables in `.env`:

```bash
# Copy the example
copy .env.example .env

# Edit .env and set:
allow_environment_variables=true
APP_CONFIG_ENDPOINT=https://dummy.azconfig.io  # Can be a dummy value

# Then fill in ALL the required variables in .env:
# - STORAGE_ACCOUNT_NAME
# - DOCUMENTS_STORAGE_CONTAINER
# - SEARCH_SERVICE_QUERY_ENDPOINT
# - AI_SEARCH_INDEX_NAME
# - AZURE_OPENAI_ENDPOINT
# - AZURE_OPENAI_EMBEDDING_DEPLOYMENT
# - etc.
```

### Step 4: Minimal Configuration

**Essential variables you MUST set:**

```env
# Storage (where your documents are)
STORAGE_ACCOUNT_NAME=yourstorageaccount
DOCUMENTS_STORAGE_CONTAINER=documents

# AI Search (where chunks will be indexed)
SEARCH_SERVICE_QUERY_ENDPOINT=https://your-search-service.search.windows.net
AI_SEARCH_INDEX_NAME=your-index-name

# Azure OpenAI (for embeddings)
AZURE_OPENAI_ENDPOINT=https://your-aoai-resource.openai.azure.com
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Document Intelligence (for PDF processing)
DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-doc-intelligence.cognitiveservices.azure.com

# API Security
INGESTION_APP_APIKEY=generate-a-random-secure-key

# Schedule (run indexer every hour)
CRON_RUN_BLOB_INDEX=0 * * * *
```

### Step 5: Prepare Your Documents

1. Upload documents to your blob storage container
2. Supported formats:
   - PDFs (`.pdf`)
   - Word/PowerPoint (`.docx`, `.pptx`) - with Document Intelligence API 4.0
   - Images (`.png`, `.jpg`, `.bmp`, `.tiff`)
   - Text files (`.txt`, `.md`, `.json`, `.csv`)
   - Spreadsheets (`.xlsx`)
   - Transcripts (`.vtt`)

### Step 6: Create the Search Index

The ingestion service expects an existing AI Search index. Here's a minimal schema:

```json
{
  "name": "your-index-name",
  "fields": [
    {"name": "id", "type": "Edm.String", "key": true, "filterable": true},
    {"name": "parent_id", "type": "Edm.String", "filterable": true},
    {"name": "chunk_id", "type": "Edm.String", "filterable": true},
    {"name": "content", "type": "Edm.String", "searchable": true},
    {"name": "title", "type": "Edm.String", "searchable": true, "filterable": true},
    {"name": "filepath", "type": "Edm.String", "filterable": true},
    {"name": "url", "type": "Edm.String"},
    {"name": "metadata", "type": "Edm.String"},
    {"name": "contentVector", "type": "Collection(Edm.Single)", "searchable": true, 
     "vectorSearchDimensions": 1536, "vectorSearchProfileName": "vector-profile"}
  ],
  "vectorSearch": {
    "algorithms": [
      {"name": "vector-config", "kind": "hnsw"}
    ],
    "profiles": [
      {"name": "vector-profile", "algorithm": "vector-config"}
    ]
  }
}
```

Create it via Azure Portal or Azure CLI:

```bash
az search index create --service-name your-search-service --name your-index-name --body @index-schema.json
```

### Step 7: Run the Application

**For testing/one-time run:**

```bash
python main.py
```

The app will:
1. Start the FastAPI server on `http://localhost:80`
2. Run the blob indexer immediately (if `CRON_RUN_BLOB_INDEX` is set)
3. Schedule future runs based on your CRON expression

**To manually trigger indexing via API:**

```bash
# You can also call the document-chunking endpoint directly
curl -X POST http://localhost:80/document-chunking \
  -H "X-API-KEY: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "values": [{
      "recordId": "1",
      "data": {
        "documentUrl": "https://yourstorageaccount.blob.core.windows.net/documents/sample.pdf",
        "documentContentType": "application/pdf"
      }
    }]
  }'
```

### Step 8: Monitor Progress

The app logs progress to:
1. **Console output** - real-time logging
2. **Blob storage** - detailed logs in `{JOBS_LOG_CONTAINER}/blob-storage-indexer/`

Check logs:
```bash
# View in Azure Portal: Storage Account > Containers > jobs > blob-storage-indexer > runs
```

## Troubleshooting

### Authentication Issues

**Error: "The service is not authenticated"**
- Run `az login` and ensure you're logged in
- Check that you have permissions on all resources

### Missing Configuration

**Error: "APP_CONFIG_ENDPOINT must be set"**
- Create a `.env` file with `APP_CONFIG_ENDPOINT`
- OR set `allow_environment_variables=true` and provide all variables directly

### App Configuration Connection Failed

**Error: "Unable to connect to Azure App Configuration"**
- Verify your `APP_CONFIG_ENDPOINT` is correct
- Check you have "App Configuration Data Reader" role
- Alternatively, use environment variables only (see Option B above)

### No Documents Being Processed

- Check your blob storage container has files
- Verify `DOCUMENTS_STORAGE_CONTAINER` name is correct
- Check `BLOB_PREFIX` if you set one - it must match your file paths
- Look at logs in the `jobs` container

### Embeddings Failing

**Error: "Error generating embeddings"**
- Verify `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` are correct
- Check your OpenAI deployment is active and has quota
- Ensure you have "Cognitive Services OpenAI User" role

### PDF Processing Failing

- Verify `DOCUMENT_INTELLIGENCE_ENDPOINT` is set and correct
- Check you have "Cognitive Services User" role on Document Intelligence
- Some PDFs may be malformed - check logs for specific errors

## Minimal Configuration Summary

At minimum, you need these 7 settings to run:

```env
APP_CONFIG_ENDPOINT=https://your-appconfig.azconfig.io
STORAGE_ACCOUNT_NAME=yourstorageaccount
DOCUMENTS_STORAGE_CONTAINER=documents
SEARCH_SERVICE_QUERY_ENDPOINT=https://your-search.search.windows.net
AI_SEARCH_INDEX_NAME=your-index
AZURE_OPENAI_ENDPOINT=https://your-aoai.openai.azure.com
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-doc-intel.cognitiveservices.azure.com
INGESTION_APP_APIKEY=your-secure-key
CRON_RUN_BLOB_INDEX=0 * * * *
```

## Next Steps

Once indexing is working:

1. **Adjust the schedule** - Change `CRON_RUN_BLOB_INDEX` to run as often as you need
2. **Add purging** - Set `CRON_RUN_BLOB_PURGE` to clean up deleted files
3. **Tune performance** - Adjust `INDEXER_MAX_CONCURRENCY` and `INDEXER_BATCH_SIZE`
4. **Add monitoring** - Configure Application Insights via `APPLICATIONINSIGHTS_CONNECTION_STRING`
5. **Deploy to Azure** - Use Container Apps for production (see main README.md)

## Configuration Reference

See `.env.example` for all available configuration options with descriptions.

## Need Help?

- Check the [main README](README.md) for architecture details
- Review [blob data source documentation](docs/blob_data_source.md)
- Check logs in your storage account's `jobs` container
- Review console output for detailed error messages
