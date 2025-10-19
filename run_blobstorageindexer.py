
import logging
import time
import asyncio
from typing import Optional
from dotenv import load_dotenv

from jobs.blob_storage_indexer import (
    BlobStorageDocumentIndexer,
    BlobIndexerConfig,
    BlobStorageDeletedItemsCleaner
)


class UTCFormatter(logging.Formatter):
    converter = time.gmtime

LOG_FORMAT = '[%(asctime)s] [%(levelname)s] [%(module)s] [%(funcName)s] %(message)s'

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt='%H:%M:%S'
)
for handler in logging.getLogger().handlers:
    handler.setFormatter(UTCFormatter(LOG_FORMAT, '%H:%M:%S'))

async def run_blob_index(cfg: Optional[BlobIndexerConfig] = None):
    logging.debug("[blob_index_files] Starting")
    try:
        await BlobStorageDocumentIndexer(cfg=cfg).run()
    except Exception:
        logging.exception("[blob_index_files] Unexpected error")

async def run_blob_purge():
    logging.debug("[blob_purge_deleted_files] Starting")
    try:
        await BlobStorageDeletedItemsCleaner().run()
    except Exception:
        logging.exception("[blob_purge_deleted_files] Unexpected error")

custom_config = BlobIndexerConfig(
    storage_account_name="ecovacsragdocs",
    source_container="documents",
    blob_prefix="ecovacs-pdfs",
    search_endpoint="https://ecovacs-rag-search.search.windows.net",
    search_index_name="gptrag-main-index",
    indexer_name="gptrag-main-indexer",
    number_debug_files=10,
)


if __name__ == "__main__":
    print(load_dotenv())
    asyncio.run(run_blob_index(custom_config))
    