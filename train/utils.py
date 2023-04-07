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
    loguru.logger.add(
        log_path / f"train_optim={config.optimizer}_chan={config.channels}_size={config.kernel_size}.log",
        level="INFO"
    )
    return loguru.logger


def log_metrics(engine: Engine, tag: str) -> None:
    metrics_format = f"{tag}, [{engine.state.epoch}/{engine.state.iteration}]: {engine.state.metrics}"
    engine.logger.info(metrics_format)


def resume_from(
        to_load: Mapping, checkpoint: Path, train_logger: "loguru.Logger", strict: bool = True
) -> None:
    if not checkpoint.exists():
        raise FileNotFoundError(f"Given {str(checkpoint)} does not exist.")

    checkpoint = torch.load(checkpoint, map_location="cpu")
    Checkpoint.load_objects(to_load=to_load, checkpoint=checkpoint, strict=strict)
    train_logger.info(f"Successfully resumed from a checkpoint: {checkpoint}.")
