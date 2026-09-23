from pydantic import BaseModel, Field
from typing import List

class MarkPosted(BaseModel):
    """Change a content item's status to posted."""
    row_id: str = Field(description="ID of the content item to mark as posted.")

class RetryRow(BaseModel):
    """Retry a failed content item by changing its status back to pending."""
    row_id: str = Field(description="ID of the failed item to retry.")

class PurgeStale(BaseModel):
    """Delete specified stale content items from the queue."""
    row_ids: List[str] = Field(description="List of exact row IDs to purge.")
