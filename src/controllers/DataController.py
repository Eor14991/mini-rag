import os
import re

from fastapi import UploadFile
from models import RespunseSignal

from .BaseController import BaseController
from .ProjectController import ProjectController


class DataController(BaseController):
    def __init__(self):
        super().__init__()
        self.file_scale = 1048576

    def val_uploaded_file(self, file: UploadFile):
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, RespunseSignal.FILE_TYPE_NOT_ALLOWED
        if file.size > (self.app_settings.FILE_MAX_SIZE * self.file_scale):
            return False, RespunseSignal.FILE_SIZE_EXCEEDED
        return True, RespunseSignal.FILE_UPLOAD_SUCCESSFUL

    def generate_unique_filepath(self, orig_file_name, project_id) -> tuple[str, str]:
        random_key = self.generate_random_string()
        project_path = ProjectController().get_project_path(project_id=project_id)
        clean_file_name = self.get_clean_file_name(orig_file_name)
        new_file_path = os.path.join(project_path,
                                     f'{random_key}_{clean_file_name}')

        while (os.path.exists(new_file_path)):
            random_key = self.generate_random_string()
            new_file_path = os.path.join(project_path,
                                         f'{random_key}_{clean_file_name}')
        return new_file_path, f'{random_key}_{clean_file_name}'

    def get_clean_file_name(self, orig_file_name) -> str:
        clean_file_name = re.sub(r'[^\w.]', '_', orig_file_name.strip())
        clean_file_name = clean_file_name.replace(' ', '_')
        return clean_file_name
