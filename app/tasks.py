import os
import sys
import logging
import torch
import time

sys.path.append("/home/mshan/study/fast-api/projects/itn_serving_server")

from typing import List
from hydra import initialize, compose
from hydra.core.config_store import ConfigStore
from omegaconf import DictConfig, OmegaConf

from app.celery_config import celery_app
from app.helpers import ITN_MODEL, instantiate_model_and_trainer
from nemo.collections.nlp.data.text_normalization_as_tagging.utils import (
    spoken_preprocessing,
)
from nemo.core.config import hydra_runner
from nemo.utils import logging


# @celery_app.task
# def send_email(recipient: str, subject: str, body: str):
#     # 이메일 전송 작업 모방
#     time.sleep(5)
#     return f"Email sent to {recipient} with subject '{subject}', {body}"


# @celery_app.task
# def process_file(file_path: str):
#     # 파일 처리 작업 모방
#     time.sleep(10)
#     return f"File at {file_path} processed"


def load_config_and_model():
    with initialize(config_path="conf", job_name="infer"):
        cfg = compose(config_name="thutmose_tagger_itn_config")

        logging.debug(f"Config Params: {OmegaConf.to_yaml(cfg)}")

        if cfg.pretrained_model is None:
            raise ValueError("A pre-trained model should be provided.")

        _, model = instantiate_model_and_trainer(cfg, ITN_MODEL, False)
        model.eval()
        return cfg, model


@celery_app.task
def infer(sents: List[str]):
    cfg, model = load_config_and_model()

    batch_size = cfg.inference.get("batch_size", 8)
    all_preds = []
    batch = []

    for i, sent in enumerate(sents):
        s = spoken_preprocessing(sent)
        batch.append(s.strip())
        if len(batch) == batch_size or i == len(sents) - 1:
            with torch.no_grad():
                outputs = model._infer(batch)
            all_preds.extend(outputs)
            batch = []

    return all_preds
