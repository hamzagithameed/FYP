# generate_handwriting.py  ←  FINAL WORKING SCRIPT
import argparse
import glob
import os
from pathlib import Path

import torch
from PIL import Image, ImageOps
import torchvision.transforms as transforms
from diffusers import AutoencoderKL, DDIMScheduler
from transformers import CanineTokenizer, CanineModel

from feature_extractor import ImageEncoder
from unet import UNetModel


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--text_to_generate', type=str, default='world', help='Text to render in the target handwriting style')
    parser.add_argument('--style_dir', type=str, default='imgs/IAM_Words_Images', help='Directory containing reference handwriting images')
    parser.add_argument('--output_path', type=str, default='MY_HANDWRITING.png', help='Where to store the generated image')
    parser.add_argument('--max_reference_images', type=int, default=100, help='Maximum reference images to load for style extraction')
    return parser.parse_args()


def preprocess(path, transform):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    new_w = int(w * 64 / h)
    img = img.resize((new_w, 64), Image.LANCZOS)
    if new_w > 256:
        img = img.resize((256, 64), Image.LANCZOS)
    if new_w < 256:
        img = ImageOps.pad(img, (256, 64), color="white")
    return transform(img)


def collect_reference_images(style_dir, transform, device, limit):
    patterns = ("*.png", "*.jpg", "*.jpeg", "*.bmp")
    paths = []
    for pattern in patterns:
        paths.extend(glob.glob(os.path.join(style_dir, pattern)))
    paths = [p for p in paths if os.path.isfile(p)]
    if not paths:
        raise ValueError(f"No reference images found inside {style_dir}")
    print(f"Found {len(paths)} reference images, using up to {limit}")
    tensors = [preprocess(p, transform).to(device) for p in paths[:limit]]
    return torch.stack(tensors)


def main():
    args = parse_args()
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {DEVICE}")

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])

    tokenizer = CanineTokenizer.from_pretrained("google/canine-c")
    text_encoder = CanineModel.from_pretrained("google/canine-c").to(DEVICE)

    class InferenceArgs:
        interpolation = False
        img_feat = False
        latent = True
        color = True
        mix_rate = None
        device = DEVICE

    unet = UNetModel(
        image_size=(64, 256),
        in_channels=4,
        model_channels=320,
        out_channels=4,
        num_res_blocks=1,
        attention_resolutions=(1, 1),
        channel_mult=(1, 1),
        num_heads=4,
        num_classes=339,
        context_dim=320,
        vocab_size=80,
        text_encoder=text_encoder,
        args=InferenceArgs()
    ).to(DEVICE)

    state = torch.load("./diffusionpen_iam_model_path/models/ckpt.pt", map_location=DEVICE)
    if any(k.startswith("module.") for k in state.keys()):
        state = {k.replace("module.", ""): v for k, v in state.items()}
    unet.load_state_dict(state, strict=False)
    unet.eval()

    vae = AutoencoderKL.from_pretrained("runwayml/stable-diffusion-v1-5", subfolder="vae").to(DEVICE)
    scheduler = DDIMScheduler.from_pretrained("runwayml/stable-diffusion-v1-5", subfolder="scheduler")
    scheduler.set_timesteps(50)

    style_extractor = ImageEncoder(model_name='mobilenetv2_100', num_classes=0, pretrained=True, trainable=True)
    style_state = torch.load("./style_models/iam_style_diffusionpen.pth", map_location=DEVICE)
    if any(k.startswith("module.") for k in style_state.keys()):
        style_state = {k.replace("module.", ""): v for k, v in style_state.items()}
    style_extractor.load_state_dict(style_state, strict=False)
    style_extractor.to(DEVICE).eval()

    ref_images = collect_reference_images(args.style_dir, transform, DEVICE, args.max_reference_images)

    text_input = tokenizer(
        args.text_to_generate,
        padding="max_length",
        truncation=True,
        max_length=40,
        return_tensors="pt"
    ).to(DEVICE)

    latents = torch.randn((1, 4, 8, 32), device=DEVICE)
    for t in scheduler.timesteps:
        t_tensor = torch.tensor([t], device=DEVICE)
        with torch.no_grad():
            pred = unet(
                x=latents,
                timesteps=t_tensor,
                context=text_input,
                y=torch.zeros(1, dtype=torch.long, device=DEVICE),
                original_images=ref_images,
                style_extractor_model=style_extractor
            )
        latents = scheduler.step(pred, t, latents).prev_sample

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with torch.no_grad():
        latents = latents / 0.18215
        image = vae.decode(latents).sample
        image = (image / 2 + 0.5).clamp(0, 1)
        image = image[0].cpu().permute(1, 2, 0).numpy()
        Image.fromarray((image * 255).astype("uint8")).save(output_path)
        print(f"SUCCESS! Saved as {output_path}")


if __name__ == "__main__":
    main()