from app.extensions import db
from app.models.resume import ResumeMetadata
from app.services.storage.supabase_storage import SupabaseStorageService
from werkzeug.utils import secure_filename
import uuid

class ResumeService:
    """Service to handle resume upload, database tracking, and deletion using Supabase Storage."""
    
    def __init__(self):
        self.storage_service = SupabaseStorageService()
        self.bucket_name = "resumes"

    def upload_resume(self, user_id: int, filename: str, file_data: bytes, content_type: str = "application/pdf") -> ResumeMetadata:
        """
        Uploads a new resume for a user to Supabase storage.
        Deletes any pre-existing resume for that user before saving the new one.
        """
        # 1. Clean filename and generate a secure unique storage path
        safe_filename = secure_filename(filename)
        # Use UUID to prevent name collisions and secure the path
        unique_id = uuid.uuid4().hex
        storage_path = f"user_{user_id}/{unique_id}_{safe_filename}"
        
        # 2. Upload file to Supabase
        public_url = self.storage_service.upload_file(
            bucket_name=self.bucket_name,
            file_path=storage_path,
            file_data=file_data,
            content_type=content_type
        )
        
        # 3. Check for existing resume and delete old file
        existing_resume = ResumeMetadata.query.filter_by(user_id=user_id).first()
        if existing_resume:
            self._delete_file_from_url(existing_resume.file_path)
            # Update database record
            existing_resume.filename = safe_filename
            existing_resume.file_path = public_url
            db.session.commit()
            return existing_resume
        
        # 4. Create new metadata record
        new_resume = ResumeMetadata(
            user_id=user_id,
            filename=safe_filename,
            file_path=public_url
        )
        db.session.add(new_resume)
        db.session.commit()
        return new_resume

    def delete_resume(self, user_id: int) -> bool:
        """
        Deletes a user's resume from Supabase Storage and database.
        """
        resume = ResumeMetadata.query.filter_by(user_id=user_id).first()
        if not resume:
            return False
            
        # Delete from Supabase Storage
        self._delete_file_from_url(resume.file_path)
        
        # Delete record from Postgres
        db.session.delete(resume)
        db.session.commit()
        return True

    def _delete_file_from_url(self, file_url: str):
        """Helper to extract relative storage path from public URL and delete the file."""
        if not file_url:
            return
            
        # Extract everything after the bucket name to get the relative storage path
        bucket_marker = f"/{self.bucket_name}/"
        if bucket_marker in file_url:
            relative_path = file_url.split(bucket_marker)[-1]
            self.storage_service.delete_file(self.bucket_name, relative_path)
