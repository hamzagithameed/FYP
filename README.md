---
license: mit
language:
- en
base_model:
- stable-diffusion-v1-5/stable-diffusion-v1-5
tags:
- HTG
- stable-diffusion
- handwritten-text-generation
metrics:
- cer
pipeline_tag: text-to-image
---

# DiffusionPen: Towards Controlling the Style of Handwritten Text Generation


Link to paper: <a href="https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/11492_ECCV_2024_paper.php">*DiffusionPen: Towards Controlling the Style of Handwritten Text Generation (ECCV 2024)*</a>

Git repo: https://github.com/koninik/DiffusionPen

**Model Description**

This release includes pretrained models for DiffusionPen method. The repo includes:
- IAM pre-processed dataset in .pt for direct loading in <a href="https://huggingface.co/konnik/DiffusionPen/tree/main/saved_iam_data">saved_iam_data</a>
- Style weights for the style encoder (also DiffusionPen-class and DiffusionPen-triplet) in <a href="https://huggingface.co/konnik/DiffusionPen/tree/main/style_models">style_models</a>
- DiffusionPen weights for IAM in <a href="https://huggingface.co/konnik/DiffusionPen/tree/main/diffusionpen_iam_model_path/models">diffusionpen_iam_model_path/models</a>

For VAE and DDIM we use stable-diffusion-v1-5/stable-diffusion-v1-5.
More info on how to utilize weights and data files can be found in the git repo.

**ArXiv**

Nikolaidou, K., Retsinas, G., Sfikas, G. and Liwicki, M., 2024. DiffusionPen: Towards Controlling the Style of Handwritten Text Generation. arXiv preprint arXiv:2409.06065.