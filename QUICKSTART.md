# 🚀 Quick Start - Running Locally

This guide will get you up and running with the GPT-RAG ingestion pipeline on your local machine in **~15 minutes**.

## Prerequisites Checklist

- [ ] Python 3.12 installed
- [ ] Azure CLI installed
- [ ] Azure resources created:
  - Azure Blob Storage (with a container for documents)
  - Azure AI Foundry / Azure OpenAI (with an embedding deployment)
  - Azure AI Search (service created, index will be created below)
  - Azure Document Intelligence (for PDF processing)
  - Azure App Configuration (optional but recommended)

## Step-by-Step Setup

### 1️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 2️⃣ Authenticate with Azure

```bash
az login
```

### 3️⃣ Configure Your Environment

**Option A: Using the Quick Start Script (Windows)**

```bash
start.bat
```

Follow the menu to:
1. Install dependencies
2. Verify setup
3. Run the pipeline

**Option B: Manual Setup**

```bash
# Copy the example .env file
copy .env.example .env

# Edit .env with your Azure resource values
notepad .env
```

Required values in `.env`:
- `APP_CONFIG_ENDPOINT` - Your Azure App Configuration endpoint
- `STORAGE_ACCOUNT_NAME` - Your storage account name
- `DOCUMENTS_STORAGE_CONTAINER` - Container with documents (e.g., "documents")
- `SEARCH_SERVICE_QUERY_ENDPOINT` - Your AI Search endpoint
- `AI_SEARCH_INDEX_NAME` - Index name (will be created)
- `AZURE_OPENAI_ENDPOINT` - Your Azure OpenAI endpoint
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` - Your embedding deployment name
- `DOCUMENT_INTELLIGENCE_ENDPOINT` - Your Document Intelligence endpoint
- `INGESTION_APP_APIKEY` - Generate a random secure string
- `CRON_RUN_BLOB_INDEX` - Set to `0 * * * *` to run hourly

### 4️⃣ Create the AI Search Index

Use the provided schema template:

```bash
# Edit the index name in sample-index-schema.json
notepad sample-index-schema.json

# Create the index
az search index create ^
  --service-name your-search-service ^
  --name your-index-name ^
  --body @sample-index-schema.json
```

Or create it via Azure Portal:
1. Go to your AI Search service
2. Click "Indexes" → "Add index"
3. Import from `sample-index-schema.json`

### 5️⃣ Upload Documents

Upload some documents to your blob storage container:

```bash
az storage blob upload-batch ^
  --account-name your-storage-account ^
  --destination your-container ^
  --source ./samples/documents
```

### 6️⃣ Verify Your Setup

```bash
python verify_setup.py
```

This will check:
- ✓ Azure CLI authentication
- ✓ All required environment variables
- ✓ Connectivity to Azure resources
- ✓ Permissions

### 7️⃣ Run the Ingestion Pipeline

```bash
python main.py
```

The application will:
1. Start a FastAPI server on `http://localhost:80`
2. Immediately run the blob indexer (if `CRON_RUN_BLOB_INDEX` is set)
3. Schedule future runs based on your CRON expression
4. Process all documents in your container
5. Upload chunks to AI Search with embeddings

## 📊 Monitor Progress

### Console Logs
Watch the console for real-time progress:
```
[blob_index_files] Starting
[blob_index_files] Processing file: sample.pdf
[blob_index_files] Generated 15 chunks
[blob_index_files] Uploaded batch of 15 chunks
```

### Storage Logs
Detailed logs are written to blob storage:
- Container: `{JOBS_LOG_CONTAINER}` (default: "jobs")
- Path: `blob-storage-indexer/runs/YYYY-MM-DD/...`

### AI Search
Check your index in Azure Portal:
1. Go to AI Search service → Indexes
2. Click on your index name
3. View document count (should increase as documents are processed)

## 🎛️ Configuration Options

### Scheduling

Control when indexing runs using CRON expressions:

```env
# Run every hour
CRON_RUN_BLOB_INDEX=0 * * * *

# Run every 15 minutes
CRON_RUN_BLOB_INDEX=*/15 * * * *

# Run daily at 2 AM
CRON_RUN_BLOB_INDEX=0 2 * * *

# Disable scheduling (manual only)
# CRON_RUN_BLOB_INDEX=
```

### Performance Tuning

```env
# Process more files in parallel (uses more memory)
INDEXER_MAX_CONCURRENCY=16

# Upload larger batches to AI Search
INDEXER_BATCH_SIZE=1000
```

### Filtering

Process only specific files:

```env
# Only process files in the "mydata" folder
BLOB_PREFIX=mydata/

# Only process files with specific extension (handled by chunker)
```

## 🔧 Troubleshooting

### "Not authenticated with Azure CLI"
```bash
az login
```

### "Invalid JSON: Expecting value: line 1 column 1"
- Check your `.env` file is properly formatted
- Ensure `APP_CONFIG_ENDPOINT` is set

### "Error generating embeddings"
- Verify your embedding deployment name: `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
- Check deployment quota in Azure Portal
- Ensure you have "Cognitive Services OpenAI User" role

### "Index not found"
- Create the index first using `sample-index-schema.json`
- Verify `AI_SEARCH_INDEX_NAME` matches the created index

### "Storage account not accessible"
- Verify `STORAGE_ACCOUNT_NAME` is correct (no "https://" prefix)
- Check you have "Storage Blob Data Contributor" role
- Ensure container exists: `DOCUMENTS_STORAGE_CONTAINER`

### No documents being processed
- Check files exist in container: `az storage blob list --account-name ... --container-name ...`
- Verify `BLOB_PREFIX` (if set) matches your file paths
- Check console logs for errors

## 📚 Supported File Formats

- **PDFs** - `.pdf` (uses Document Intelligence)
- **Word/PowerPoint** - `.docx`, `.pptx` (requires Document Intelligence 4.0)
- **Images** - `.png`, `.jpg`, `.bmp`, `.tiff` (OCR via Document Intelligence)
- **Text** - `.txt`, `.md`, `.json`, `.csv`
- **Spreadsheets** - `.xlsx`
- **Transcripts** - `.vtt` (video transcriptions)

## 🎯 Next Steps

1. **Test your setup** - Upload a sample PDF and verify it appears in AI Search
2. **Adjust scheduling** - Fine-tune `CRON_RUN_BLOB_INDEX` for your needs
3. **Add purging** - Set `CRON_RUN_BLOB_PURGE` to clean up deleted files
4. **Enable monitoring** - Add `APPLICATIONINSIGHTS_CONNECTION_STRING` for telemetry
5. **Deploy to Azure** - Use Container Apps for production (see main [README.md](README.md))

## 📖 Documentation

- [Complete Local Setup Guide](LOCAL_SETUP_GUIDE.md) - Detailed documentation
- [Blob Data Source](docs/blob_data_source.md) - How blob indexing works
- [NL2SQL Data Source](docs/nl2sql_data_source.md) - Database indexing
- [Main README](README.md) - Architecture and deployment

## 💡 Tips

- **Start small** - Test with 1-2 documents first
- **Check logs** - Both console and blob storage logs are your friends
- **Monitor costs** - Document Intelligence and Azure OpenAI have per-request costs
- **Use prefixes** - `BLOB_PREFIX` helps process specific folders only
- **Incremental updates** - The indexer skips unchanged files automatically

---

**Need help?** Check [LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md) for detailed troubleshooting.
