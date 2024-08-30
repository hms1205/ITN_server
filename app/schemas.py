from pydantic import BaseModel
from typing import Optional, List


# class EmailRequest(BaseModel):
#     recipient: str
#     subject: str
#     body: str


# class FileRequest(BaseModel):
#     file_path: str


class InferRequest(BaseModel):
    sents: List[str] = []


class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: List[str] = []
