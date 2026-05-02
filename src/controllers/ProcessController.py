import os
from typing import Dict, Type, Tuple, Any

from langchain_community.document_loaders import TextLoader
from langchain_core.document_loaders.base import BaseLoader
from langchain_core.documents import Document
from langchain_docling.loader import DoclingLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from models import ProcessingEnums

from .BaseController import BaseController
from .ProjectController import ProjectController


class DocumentLoaderFactory:
    _loaders: Dict[str, Tuple[Type[BaseLoader], Dict[str, Any]]] = {
        ProcessingEnums.TXT.value: (TextLoader, {"encoding": "utf-8"}),
        ProcessingEnums.PDF.value: (DoclingLoader, {})
    }

    @classmethod
    def create(cls, file_extension: str, file_path: str) -> BaseLoader:
        loader_info = cls._loaders.get(file_extension)
        if not loader_info:
            raise ValueError(f"Unsupported file extension: {file_extension}")

        loader_class, kwargs = loader_info

        return loader_class(file_path, **kwargs)


class ProcessController(BaseController):
    def __init__(self, project_id: str) -> None:
        super().__init__()
        self.project_id = project_id
        self.project_controller = ProjectController()
        self.project_path = self.project_controller.get_project_path(self.project_id)

    def get_file_loader(self, file_id: str) -> BaseLoader:

        file_extension = os.path.splitext(file_id)[-1]
        file_path = os.path.join(self.project_path, file_id)

        if not os.path.exists(file_path):
            return None

        return DocumentLoaderFactory.create(file_extension, file_path)

    def get_content(self, file_id: str) -> list[Document]:
        loader = self.get_file_loader(file_id)
        return loader.load()

    def process_file_content(self, file_content: list[Document], file_id: str,
                             chunk_size: int = 100, overlap_size: int = 20) -> list[Document]:
        full_text = '\n\n'.join([page.page_content for page in file_content])

        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4")
        ]

        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False
        )

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap_size,
            separators=["\n\n", "\n", " ", ""],
            length_function=len,
        )

        md_docs = markdown_splitter.split_text(full_text)

        for doc in md_docs:
            doc.metadata["file_id"] = file_id

        chunks = text_splitter.split_documents(md_docs)

        return chunks
