from datetime import datetime
from pathlib import Path
from typing import Tuple, Mapping

import loguru
import torch
from ignite.engine import Engine
from ignite.handlers import Checkpoint
from torch.utils.data import random_split, DataLoader

from common import base_path, log_path
from datasets import MTAestheticDataset
from .config import Configuration


def setup_config(filename: str = "config.json") -> Configuration:
    return Configuration.parse_file(path=base_path / filename, content_type="json")


def setup_data(config: Configuration) -> Tuple[DataLoader, DataLoader, DataLoader]:
    dataset = MTAestheticDataset()
    train_dataset, val_dataset, test_dataset = random_split(dataset, lengths=[6000, 2000, 2000])

    # 这里在本地验证时为节省资源，而不设置num_workers
    # train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True, num_workers=4)
    # val_loader = DataLoader(val_dataset, batch_size=config.batch_size, shuffle=True, num_workers=4)
    # test_loader = DataLoader(test_dataset, batch_size=config.batch_size, shuffle=True, num_workers=4)

    train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=config.batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=config.batch_size, shuffle=True)

    return train_loader, val_loader, test_loader


def setup_logger(config: Configuration) -> "loguru.Logger":
    logger = loguru.logger

    logger.add(log_path / f"{datetime.today().date()}.log", level="INFO")

    logger.info(f"Begin training at: {datetime.today()}.")
    logger.info(
        f"Model info: optimizer: {config.optimizer}, channels: {config.channels}, "
        f"kernel size: {config.kernel_size}, learning rate: {config.lr}."
    )
    logger.info(f"Training info: batch size: {config.batch_size}, epoch counts: {config.max_epochs}.")
    logger.info(f"Using amp: {config.use_amp}.")

    return loguru.logger


def log_metrics(engine: Engine, tag: str) -> None:
    logger = engine.logger
    logger.info(f"{tag}, [{engine.state.epoch}/{engine.state.iteration}].")
    logger.info(f"Total loss: {engine.state.metrics['loss']}, "
                f"binary classification accuracy: {engine.state.metrics['bin']}, "
                f"scoring MSE: {engine.state.metrics['score']}, "
                f"multi-label classification report: {engine.state.metrics['attribute']['macro avg']}.")


def resume_from(
        to_load: Mapping, checkpoint: Path, train_logger: "loguru.Logger", strict: bool = True
) -> None:
    if not checkpoint.exists():
        raise FileNotFoundError(f"Given {str(checkpoint)} does not exist.")

    checkpoint = torch.load(checkpoint, map_location="cpu")
    Checkpoint.load_objects(to_load=to_load, checkpoint=checkpoint, strict=strict)
    train_logger.info(f"Successfully resumed from a checkpoint: {checkpoint}.")
