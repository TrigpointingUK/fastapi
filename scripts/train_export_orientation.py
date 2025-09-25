"""
Train a tiny 4-class rotation classifier (0/90/180/270) and export to ONNX.

Self-supervised approach: take input images and create 4 rotated variants.
This keeps data prep simple and avoids labelling.

Usage:
  python scripts/train_export_orientation.py \
      --data ./res/orientation_data \
      --output ./res/models/orientation_classifier.onnx \
      --epochs 3 --batch-size 64 --lr 1e-3

Notes:
  - Only required for training/export. Runtime only needs onnxruntime and numpy.
  - Images are resized to 224x224. Model is MobileNetV2 backbone with a 4-way head.
"""

from __future__ import annotations

import argparse
import os
import random
from pathlib import Path
from typing import Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


class RotationDataset(Dataset):
    def __init__(self, root_dir: str | Path, image_size: int = 224):
        self.root_dir = Path(root_dir)
        self.paths = [
            p
            for p in self.root_dir.rglob("*")
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}
        ]
        if not self.paths:
            raise RuntimeError(f"No images found in {self.root_dir}")
        self.base_transform = transforms.Compose(
            [transforms.Resize((image_size, image_size)), transforms.ToTensor()]
        )

    def __len__(self) -> int:
        # Each image is used once per batch with a random rotation label
        return len(self.paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        path = self.paths[idx]
        with Image.open(path) as img:
            img = img.convert("RGB")
            x = self.base_transform(img)
        # Generate a random rotation label and rotate tensor accordingly
        label = random.randint(0, 3)  # 0,1,2,3 -> 0,90,180,270
        # Rotate by 90° increments: rotate channels last then back
        x = torch.rot90(x, k=label, dims=(1, 2))
        return x, label


def build_model(num_classes: int = 4) -> nn.Module:
    backbone = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V2)
    for p in backbone.parameters():
        p.requires_grad = False
    # Replace classifier head
    in_feats = backbone.classifier[1].in_features
    backbone.classifier[1] = nn.Linear(in_feats, num_classes)
    return backbone


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    opt: optim.Optimizer,
    criterion: nn.Module,
) -> float:
    model.train()
    running_loss = 0.0
    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)
        opt.zero_grad()
        logits = model(images)
        loss = criterion(logits, labels)
        loss.backward()
        opt.step()
        running_loss += float(loss.item()) * images.size(0)
    return running_loss / len(loader.dataset)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True, help="Path to images root")
    parser.add_argument("--output", type=str, required=True, help="Output ONNX path")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    set_seed(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ds = RotationDataset(args.data)
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=True, num_workers=2)

    model = build_model().to(device)
    criterion = nn.CrossEntropyLoss()
    opt = optim.Adam(model.parameters(), lr=args.lr)

    for epoch in range(args.epochs):
        loss = train_one_epoch(model, loader, device, opt, criterion)
        print(f"epoch={epoch + 1} loss={loss:.4f}")

    # Export to ONNX (batch=1, 3x224x224)
    model.eval()
    dummy = torch.randn(1, 3, 224, 224, device=device)
    out_dir = Path(args.output).parent
    os.makedirs(out_dir, exist_ok=True)
    torch.onnx.export(
        model,
        dummy,
        args.output,
        input_names=["input"],
        output_names=["logits"],
        opset_version=12,
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
    )
    print(f"Exported ONNX to {args.output}")


if __name__ == "__main__":
    main()
