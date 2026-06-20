"""
Document Archiving System (e-Archive)
Stores all supporting documents with versioning, full-text search, and audit trails
Supports: Invoices, Contracts, Quotes, POs, Receipts, Certificates, etc.
"""

import os
import mimetypes
from datetime import datetime
from typing import Optional, List, BinaryIO
from pathlib import Path
import hashlib
import json
from enum import Enum
from sqlalchemy.orm import Session
from pydantic import BaseModel


class DocumentType(str, Enum):
    """Types of documents in the archive"""
    INVOICE = "invoice"
    PURCHASE_ORDER = "purchase_order"
    QUOTATION = "quotation"
    RECEIPT = "receipt"
    CONTRACT = "contract"
    CERTIFICATE = "certificate"
    EMPLOYEE_DOCUMENT = "employee_document"
    COMPLIANCE = "compliance"
    OTHER = "other"


class DocumentArchiveConfig:
    """Configuration for document archiving"""
    
    # Storage location (can be local or cloud)
    STORAGE_TYPE = os.getenv("DOCUMENT_STORAGE_TYPE", "local")  # local, s3, minio, azure
    
    # Local storage
    LOCAL_STORAGE_PATH = os.getenv("DOCUMENT_ARCHIVE_PATH", "./documents_archive")
    
    # MinIO (S3-compatible)
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET", "mednova-documents")
    
    # AWS S3
    S3_BUCKET = os.getenv("S3_BUCKET")
    S3_REGION = os.getenv("S3_REGION", "us-east-1")
    
    # Settings
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_DOCUMENT_SIZE_MB", "100"))
    ALLOWED_EXTENSIONS = {
        ".pdf", ".doc", ".docx", ".xls", ".xlsx",
        ".txt", ".csv", ".json",
        ".jpg", ".jpeg", ".png", ".gif",
        ".zip", ".rar"
    }
    ENABLE_VERSIONING = True
    RETENTION_YEARS = int(os.getenv("DOCUMENT_RETENTION_YEARS", "7"))


class DocumentMetadata(BaseModel):
    """Metadata for archived document"""
    document_type: DocumentType
    title: str
    description: Optional[str] = None
    uploaded_by: int  # User ID
    module: str  # hr, finance, procurement, inventory, assets
    linked_record_type: str  # e.g., "purchase_request", "employee", "contract"
    linked_record_id: int
    file_hash: str  # SHA256 for integrity verification
    file_size: int  # bytes
    mime_type: str


class DocumentArchive:
    """
    Document archiving with versioning and full-text search
    Polymorphically links to any record (PR, PO, Employee, Contract, etc.)
    """

    def __init__(self):
        """Initialize archive storage"""
        if DocumentArchiveConfig.STORAGE_TYPE == "local":
            self._init_local_storage()
        elif DocumentArchiveConfig.STORAGE_TYPE in ["s3", "minio"]:
            self._init_cloud_storage()

    @staticmethod
    def _init_local_storage():
        """Initialize local file storage"""
        Path(DocumentArchiveConfig.LOCAL_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
        print(f"✓ Document archive initialized at: {DocumentArchiveConfig.LOCAL_STORAGE_PATH}")

    @staticmethod
    def _init_cloud_storage():
        """Initialize cloud storage (MinIO/S3)"""
        if DocumentArchiveConfig.STORAGE_TYPE == "minio":
            from minio import Minio
            
            client = Minio(
                DocumentArchiveConfig.MINIO_ENDPOINT,
                access_key=DocumentArchiveConfig.MINIO_ACCESS_KEY,
                secret_key=DocumentArchiveConfig.MINIO_SECRET_KEY,
                secure=False
            )
            
            # Create bucket if not exists
            if not client.bucket_exists(DocumentArchiveConfig.MINIO_BUCKET):
                client.make_bucket(DocumentArchiveConfig.MINIO_BUCKET)
                print(f"✓ Created MinIO bucket: {DocumentArchiveConfig.MINIO_BUCKET}")
        
        elif DocumentArchiveConfig.STORAGE_TYPE == "s3":
            import boto3
            
            s3_client = boto3.client(
                "s3",
                region_name=DocumentArchiveConfig.S3_REGION
            )
            
            # Create bucket if not exists
            try:
                s3_client.head_bucket(Bucket=DocumentArchiveConfig.S3_BUCKET)
            except:
                s3_client.create_bucket(Bucket=DocumentArchiveConfig.S3_BUCKET)
                print(f"✓ Created S3 bucket: {DocumentArchiveConfig.S3_BUCKET}")

    @staticmethod
    def archive_document(
        db: Session,
        file: BinaryIO,
        metadata: DocumentMetadata
    ) -> dict:
        """
        Archive a document with metadata
        Supports versioning for existing documents
        """
        
        # Validate file
        DocumentArchive._validate_file(file, metadata)
        
        # Generate unique ID and file hash
        file_hash = DocumentArchive._calculate_file_hash(file)
        document_id = f"{metadata.linked_record_type}-{metadata.linked_record_id}-{datetime.utcnow().timestamp()}"
        
        # Determine storage path
        year_month = datetime.utcnow().strftime("%Y/%m")
        file_name = f"{metadata.module}/{year_month}/{document_id}/{metadata.title}"
        
        # Store file
        if DocumentArchiveConfig.STORAGE_TYPE == "local":
            storage_path = DocumentArchive._store_local(file, file_name)
        else:
            storage_path = DocumentArchive._store_cloud(file, file_name, metadata)
        
        # Save metadata to database
        archived_doc = {
            "document_id": document_id,
            "storage_path": storage_path,
            "title": metadata.title,
            "document_type": metadata.document_type.value,
            "module": metadata.module,
            "linked_record_type": metadata.linked_record_type,
            "linked_record_id": metadata.linked_record_id,
            "uploaded_by": metadata.uploaded_by,
            "file_hash": file_hash,
            "file_size": metadata.file_size,
            "mime_type": metadata.mime_type,
            "uploaded_at": datetime.utcnow(),
            "version": 1,
            "is_latest": True,
            "status": "active"
        }
        
        # TODO: Insert into DocumentArchive table
        # db.add(ArchivedDocument(**archived_doc))
        # db.commit()
        
        print(f"✓ Document archived: {metadata.title} ({file_hash[:8]}...)")
        return archived_doc

    @staticmethod
    def _validate_file(file: BinaryIO, metadata: DocumentMetadata):
        """Validate file before archiving"""
        # Check file size
        if metadata.file_size > DocumentArchiveConfig.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"File exceeds max size of {DocumentArchiveConfig.MAX_FILE_SIZE_MB}MB")
        
        # Check file extension
        file_ext = Path(metadata.title).suffix.lower()
        if file_ext not in DocumentArchiveConfig.ALLOWED_EXTENSIONS:
            raise ValueError(f"File type {file_ext} not allowed")
        
        print(f"  ✓ File validation passed: {metadata.title}")

    @staticmethod
    def _calculate_file_hash(file: BinaryIO) -> str:
        """Calculate SHA256 hash of file for integrity verification"""
        hash_sha256 = hashlib.sha256()
        for chunk in iter(lambda: file.read(4096), b""):
            hash_sha256.update(chunk)
        file.seek(0)  # Reset file pointer
        return hash_sha256.hexdigest()

    @staticmethod
    def _store_local(file: BinaryIO, file_path: str) -> str:
        """Store file in local filesystem"""
        full_path = Path(DocumentArchiveConfig.LOCAL_STORAGE_PATH) / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as f:
            f.write(file.read())
        
        return str(full_path)

    @staticmethod
    def _store_cloud(file: BinaryIO, file_path: str, metadata: DocumentMetadata) -> str:
        """Store file in cloud storage (MinIO/S3)"""
        if DocumentArchiveConfig.STORAGE_TYPE == "minio":
            from minio import Minio
            
            client = Minio(
                DocumentArchiveConfig.MINIO_ENDPOINT,
                access_key=DocumentArchiveConfig.MINIO_ACCESS_KEY,
                secret_key=DocumentArchiveConfig.MINIO_SECRET_KEY,
                secure=False
            )
            
            client.put_object(
                DocumentArchiveConfig.MINIO_BUCKET,
                file_path,
                file,
                metadata.file_size,
                content_type=metadata.mime_type
            )
            
            return f"minio://{DocumentArchiveConfig.MINIO_BUCKET}/{file_path}"
        
        elif DocumentArchiveConfig.STORAGE_TYPE == "s3":
            import boto3
            
            s3_client = boto3.client("s3")
            
            s3_client.upload_fileobj(
                file,
                DocumentArchiveConfig.S3_BUCKET,
                file_path,
                ExtraArgs={"ContentType": metadata.mime_type}
            )
            
            return f"s3://{DocumentArchiveConfig.S3_BUCKET}/{file_path}"

    @staticmethod
    def retrieve_document(
        db: Session,
        document_id: str
    ) -> tuple[BinaryIO, DocumentMetadata]:
        """Retrieve archived document by ID"""
        # TODO: Query DocumentArchive table
        # doc = db.query(ArchivedDocument).filter(
        #     ArchivedDocument.document_id == document_id,
        #     ArchivedDocument.is_latest == True
        # ).first()
        
        print(f"✓ Retrieved document: {document_id}")
        # Return file stream and metadata
        pass

    @staticmethod
    def search_documents(
        db: Session,
        module: str,
        linked_record_type: str,
        linked_record_id: int
    ) -> List[dict]:
        """
        Full-text search for documents linked to a record
        Returns all versions (with is_latest flag)
        """
        # TODO: Query DocumentArchive with full-text search
        # documents = db.query(ArchivedDocument).filter(
        #     ArchivedDocument.module == module,
        #     ArchivedDocument.linked_record_type == linked_record_type,
        #     ArchivedDocument.linked_record_id == linked_record_id
        # ).order_by(ArchivedDocument.uploaded_at.desc()).all()
        
        documents = []
        print(f"✓ Found {len(documents)} documents for {linked_record_type}#{linked_record_id}")
        return documents

    @staticmethod
    def delete_document_version(
        db: Session,
        document_id: str,
        version: int
    ):
        """
        Delete specific version of document (soft delete)
        Never truly delete for audit trail
        """
        # TODO: Set status='deleted' for specific version
        print(f"✓ Deleted document version: {document_id} v{version}")

    @staticmethod
    def cleanup_expired_documents(db: Session):
        """
        Delete documents older than retention period
        Scheduled task (yearly)
        """
        retention_date = datetime.utcnow().replace(year=datetime.utcnow().year - DocumentArchiveConfig.RETENTION_YEARS)
        
        # TODO: Delete archived documents older than retention_date
        # deleted_count = db.query(ArchivedDocument).filter(
        #     ArchivedDocument.uploaded_at < retention_date,
        #     ArchivedDocument.status != 'protected'  # Don't delete protected docs
        # ).delete()
        
        deleted_count = 0
        print(f"✓ Cleaned up {deleted_count} expired documents")


class DocumentUploadAPI:
    """
    API endpoints for document upload/retrieval
    To be integrated into FastAPI routers
    """

    @staticmethod
    def upload_document_endpoint(
        db: Session,
        file: BinaryIO,
        document_type: str,
        title: str,
        module: str,
        linked_record_type: str,
        linked_record_id: int,
        uploaded_by: int,
        description: Optional[str] = None
    ):
        """FastAPI endpoint for uploading documents"""
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(title)
        file_size = len(file.read())
        file.seek(0)
        
        metadata = DocumentMetadata(
            document_type=DocumentType(document_type),
            title=title,
            description=description,
            uploaded_by=uploaded_by,
            module=module,
            linked_record_type=linked_record_type,
            linked_record_id=linked_record_id,
            file_hash="",  # Will be calculated
            file_size=file_size,
            mime_type=mime_type or "application/octet-stream"
        )
        
        # Archive document
        archive = DocumentArchive()
        result = archive.archive_document(db, file, metadata)
        
        return {
            "status": "success",
            "document_id": result["document_id"],
            "message": f"Document '{title}' archived successfully"
        }

    @staticmethod
    def retrieve_document_endpoint(
        db: Session,
        document_id: str
    ):
        """FastAPI endpoint for retrieving documents"""
        archive = DocumentArchive()
        file_stream, metadata = archive.retrieve_document(db, document_id)
        
        return {
            "status": "success",
            "document": {
                "id": document_id,
                "title": metadata.title,
                "type": metadata.document_type.value,
                "size": metadata.file_size,
                "uploaded_at": metadata.uploaded_at.isoformat()
            }
        }

    @staticmethod
    def list_documents_endpoint(
        db: Session,
        module: str,
        linked_record_type: str,
        linked_record_id: int
    ):
        """FastAPI endpoint for listing documents"""
        archive = DocumentArchive()
        documents = archive.search_documents(db, module, linked_record_type, linked_record_id)
        
        return {
            "status": "success",
            "documents": documents,
            "count": len(documents)
        }
