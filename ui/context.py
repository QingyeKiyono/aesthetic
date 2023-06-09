from pathlib import Path
from urllib.parse import urlparse

import torch
from PIL import Image
from PySide6.QtCore import QObject, Slot, Signal
from torch import Tensor
from torch.nn.functional import softmax

from common import image_transforms, TensorData, AssessResult, new_attribute_result, pretrained_path
from models import MTAesthetic
from train import resume_from


def process_output(output_tensor: TensorData) -> AssessResult:
    """
    将模型的输出转化成方便传送给QML页面的形式
    :param output_tensor: 模型的输出
    :return: 处理好的图像美学评价结果
    """

    result_binary: bool = output_tensor["binary"].item() > 0.2

    scores = torch.tensor([i for i in range(1, 11)], dtype=torch.float)
    result_score: Tensor = softmax(output_tensor["score"].squeeze(0), dim=0)
    result_score: Tensor = torch.dot(result_score, scores)
    result_score: float = round(result_score.item(), 3)

    result_attribute: Tensor = output_tensor["attribute"].squeeze(0) > 4e-4
    result_attribute: list = result_attribute.tolist()

    return AssessResult(
        binary=result_binary,
        score=result_score,
        attribute=new_attribute_result(result_attribute)
    )


def load_model(use_attention: bool, kernel_size: int, use_dwa: bool) -> MTAesthetic:
    """
    从保留的权重文件中加载预训练的模型，参见config.json文件
    :param use_attention: 是否使用Attention机制
    :param kernel_size: 卷积核的大小
    :param use_dwa: 是否使用DWA机制
    :return: 加载好的模型
    """

    to_load = {"model": MTAesthetic(channels=1024, kernel_size=kernel_size, use_attention=use_attention)}
    resume_from(to_load, pretrained_path / f"{int(use_attention)}{kernel_size}{int(use_dwa)}.pt")
    return to_load["model"]


class Context(QObject):
    """
    QML页面所使用的的上下文，包括必要的信号和槽、应用双向沟通使用的变量和模型的参数等信息
    """

    def __init__(self):
        super().__init__()
        # 设置默认参数：使用attention，kernel size为5，不使用DWA
        self.use_attention = True
        self.kernel_size = 3
        self.use_dwa = True
        # 加载模型
        self.model = load_model(self.use_attention, self.kernel_size, self.use_dwa)

    @Slot(str)
    def assess_image(self, image_url: str) -> None:
        """
        槽函数，当选择一张新的图片时被调用
        :param image_url: 图像的所在路径
        :return: None
        """
        image_path = urlparse(image_url, scheme="file").path.removeprefix("/")
        image_path = Path(image_path).absolute()

        # 如果图片不存在，直接返回（虽然可能性不大）
        if not image_path.exists():
            return

        image = Image.open(image_path)
        image_tensor: Tensor = image_transforms(image).unsqueeze(0)
        input_tensor: TensorData = TensorData(binary=image_tensor, attribute=image_tensor, score=image_tensor)
        output_tensor: TensorData = self.model(input_tensor)
        print(output_tensor["binary"])

        # 将输出转换成对应的类型，并传递给页面
        assess_result = process_output(output_tensor)
        self.send_result(assess_result)

    @Slot(bool, int, bool)
    def change_model(self, use_attention: bool, kernel_size: int, use_dwa: bool) -> None:
        """
        更换使用的模型，参数同load_model
        :param use_attention: 是否使用注意力机制
        :param kernel_size: 卷积核大小
        :param use_dwa: 是否使用DWA
        :return: None
        """
        self.model = load_model(use_attention, kernel_size, use_dwa)

    def send_result(self, assess_result: AssessResult) -> None:
        """
        向页面发送图像美学质量评价的结果，调用QML页面中Signal的handler
        :param assess_result: 评价好的结果
        :return: None
        """
        self.setBinary.emit(assess_result["binary"])
        self.setScore.emit(assess_result["score"])
        self.setBalancingElement.emit(assess_result["attribute"]["balancing_element"])
        self.setContent.emit(assess_result["attribute"]["content"])
        self.setColorHarmony.emit(assess_result["attribute"]["color_harmony"])
        self.setDepthOfField.emit(assess_result["attribute"]["depth_of_field"])
        self.setLighting.emit(assess_result["attribute"]["lighting"])
        self.setMotionBlur.emit(assess_result["attribute"]["motion_blur"])
        self.setObjectEmphasis.emit(assess_result["attribute"]["object_emphasis"])
        self.setRuleOfThirds.emit(assess_result["attribute"]["rule_of_thirds"])
        self.setVividColor.emit(assess_result["attribute"]["vivid_color"])
        self.setRepetition.emit(assess_result["attribute"]["repetition"])
        self.setSymmetry.emit(assess_result["attribute"]["symmetry"])

    # Signals
    setBinary = Signal(bool)
    setScore = Signal(float)

    setBalancingElement = Signal(bool)
    setContent = Signal(bool)
    setColorHarmony = Signal(bool)
    setDepthOfField = Signal(bool)
    setLighting = Signal(bool)
    setMotionBlur = Signal(bool)
    setObjectEmphasis = Signal(bool)
    setRuleOfThirds = Signal(bool)
    setVividColor = Signal(bool)
    setRepetition = Signal(bool)
    setSymmetry = Signal(bool)
