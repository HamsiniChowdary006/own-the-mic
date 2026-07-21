from flask import current_app
from supabase import create_client, Client

class SupabaseStorageService:
    """Service class interfacing with Supabase Storage bucket operations."""
    
    def __init__(self):
        self._client = None

    @property
    def client(self) -> Client:
        if not self._client:
            url = current_app.config.get('SUPABASE_URL')
            # Prefer Secret Key to ensure we bypass any restricted RLS policies for backend file uploads
            key = current_app.config.get('SUPABASE_SECRET_KEY') or current_app.config.get('SUPABASE_PUBLISHABLE_KEY')
            if not url or not key:
                raise ValueError("Supabase URL and Key/Service Role Key must be configured in environment.")
            self._client = create_client(url, key)
        return self._client

    def upload_file(self, bucket_name: str, file_path: str, file_data: bytes, content_type: str = None) -> str:
        """
        Uploads raw file bytes to a specified Supabase storage bucket.
        Uses x-upsert: true option to overwrite any existing file.
        Returns the public URL of the uploaded file.
        """
        options = {}
        if content_type:
            options["content-type"] = content_type
        options["x-upsert"] = "true"

        current_app.logger.info(f"Uploading file to Supabase Storage: {bucket_name}/{file_path}")
        
        # In supabase-py, upload throws an exception or returns a response object on failure
        res = self.client.storage.from_(bucket_name).upload(
            path=file_path,
            file=file_data,
            file_options=options
        )
        
        # Get public URL
        public_url = self.client.storage.from_(bucket_name).get_public_url(file_path)
        current_app.logger.info(f"Successfully uploaded file. Public URL: {public_url}")
        return public_url

    def delete_file(self, bucket_name: str, file_path: str) -> bool:
        """
        Deletes a file from the specified Supabase storage bucket.
        """
        current_app.logger.info(f"Deleting file from Supabase Storage: {bucket_name}/{file_path}")
        try:
            self.client.storage.from_(bucket_name).remove([file_path])
            return True
        except Exception as e:
            current_app.logger.error(f"Error deleting file from Supabase Storage: {str(e)}")
            return False
