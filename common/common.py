from pathlib import Path

from PIL import Image
from torchvision import transforms as transforms


def convert_to_rgb(image: Image) -> Image:
    """
    将图像转换成tensor，避免因为图像通道小于3而导致模型计算出错
    :param image: 读取到的图像
    :return: 转换后的tensor
    """
    return image.convert("RGB")


# 图像预处理，尽量不改变图像的颜色、亮度、方位等特征，最大程度保留图像的美学信息
image_transforms = transforms.Compose([
    convert_to_rgb,
    transforms.Resize(512),
    transforms.RandomCrop(256),
    transforms.ToTensor(),
])

base_path = Path(__file__).parent.parent.resolve()  # 项目根目录，即最顶层的aesthetic
data_path = base_path / "data"
output_path = base_path / "outputs"
checkpoint_path = output_path / "checkpoints"
log_path = output_path / "logs"
pretrained_path = base_path / "pretrained"  # 预训练模型存放目录
