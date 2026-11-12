# InkWave: AI-Based Handwriting Replication

Generate new text in **your own handwriting** from just five samples.

InkWave is our Final Year Project for the BS in Computer Science at **Bahria University, Karachi Campus** (2025). It is a full web application built on a few-shot latent diffusion model. You upload five or more images of your handwritten words, type any text, and get it back as handwriting in your style. You can export the result as an image or a PDF.

> **Built on DiffusionPen.** The generation model is based on [DiffusionPen: Towards Controlling the Style of Handwritten Text Generation](https://arxiv.org/abs/2409.06065) by Konstantina Nikolaidou et al. (ECCV 2024). We use the authors' [official code](https://github.com/koninik/DiffusionPen) (MIT License) and [pretrained weights](https://huggingface.co/konnik/DiffusionPen). Our contribution is adapting that model to new users' handwriting and building a complete application around it. See [What we changed](#what-we-changed).

<!-- Add 2–3 screenshots here: landing page, stylized generation, sample output -->
<!-- ![Stylized generation](docs/screenshots/stylized.png) -->

---

## Features

- **Custom-style generation:** upload ≥5 handwriting samples and generate any word or sentence in that style
- **Pre-trained IAM styles:** generate with one of 339 writer styles from the IAM Handwriting Database
- **Sentence generation:** words are generated individually and composed into a sentence with natural spacing
- **Handwriting recognition:** Microsoft TrOCR reads handwritten images and automatically checks generated output
- **PDF export:** place the generated handwriting on an A4 page
- **User accounts:** sign-up and login with JWT authentication and MongoDB

## What we changed

The original DiffusionPen conditions generation on **IAM writer IDs**, so it can only produce styles seen during training. To support any user's handwriting, we made these changes:

| Area | Original DiffusionPen | InkWave |
|---|---|---|
| Style conditioning | Writer-ID / style-extractor input tied to IAM writers | New path in `UNetModel.forward`: style features from the user's uploaded samples are averaged, projected to the embedding size (`style_lin`, 1280 → 320) and added to the timestep embedding |
| Input handling | Pre-processed IAM tensors | Preprocessing for arbitrary user images: RGB, height 64, aspect-preserving resize, then pad or resize to 256 px width |
| Inference | Research training/sampling script | Standalone generation scripts (`generate_handwriting.py`, `trainCopy.py`) with custom-style and random-style modes, CPU and GPU, configurable output path |
| Output | Single word images | Word-to-sentence composition, PDF export |
| Application | None | FastAPI backend, TrOCR recognition service, React frontend, authentication |

We did **not** retrain the diffusion model. All generation uses the authors' pretrained IAM checkpoint and style encoder.

## How it works

```
User samples (≥5 images) ──► preprocessing ──► style encoder ──► mean style vector ─┐
                                                                                     ▼
Text ──► CANINE character embeddings ──► cross-attention ──► UNet denoiser (DDIM, 50 steps)
                                                                                     │
                                         Stable Diffusion VAE decoder ◄──────────────┘
                                                     │
                                       word images ──► sentence image ──► PNG / PDF
                                                     │
                                              TrOCR legibility check
```

## Tech stack

| Layer | Technology |
|---|---|
| Model | PyTorch, Hugging Face Diffusers (VAE, DDIM), Transformers (CANINE, TrOCR) |
| Backend | FastAPI, Uvicorn, ReportLab, Motor/MongoDB, JWT (python-jose), bcrypt |
| Frontend | React 18, Vite, React Router, Framer Motion |

## API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/word` | Generate a single word in a random IAM style |
| POST | `/api/sentence` | Generate a sentence, word by word |
| POST | `/api/stylized` | Generate text in the style of ≥5 uploaded samples (multipart) |
| POST | `/api/detect` | Recognise text in a handwriting image (TrOCR) |
| POST | `/convert/pdf` | Convert a generated image to an A4 PDF |
| POST | `/auth/signup`, `/auth/login` | Create an account / log in (returns JWT) |
| GET | `/auth/me` | Current user |

Interactive docs are available at `http://127.0.0.1:8000/docs` when the backend is running.

## Getting started

### Prerequisites
- Python 3.10+ and Node.js 18+
- MongoDB (local or Atlas)
- A CUDA GPU is recommended. CPU works but is much slower.

### 1. Clone and install
```bash
git clone <this-repo-url>
cd <repo-folder>
pip install -r requirements.txt
pip install -r requirements_htr.txt   # TrOCR recognition service
npm install
```

### 2. Download the pretrained DiffusionPen weights
Download from [huggingface.co/konnik/DiffusionPen](https://huggingface.co/konnik/DiffusionPen) and place them as follows:
```
diffusionpen_iam_model_path/models/ckpt.pt
style_models/iam_style_diffusionpen.pth
```
The Stable Diffusion VAE (`runwayml/stable-diffusion-v1-5`) and CANINE (`google/canine-c`) download automatically on first run.

### 3. Configure
```bash
cp .env.example .env    # set MONGODB_URI and JWT_SECRET
```

### 4. Run
```bash
# Backend
python -m uvicorn api.main:app --reload --port 8000
# Frontend (new terminal)
npm run dev
```
Open http://localhost:5173. On Windows, `start_servers.bat` starts both.

### Command-line generation (no web app)
```bash
python trainCopy.py --custom_style_folder ./my_samples --text_to_generate "hello world" --device cuda
```

## Results and limitations

- Style (slant, curvature, letter shapes) is reproduced well for **words and short sentences**.
- Style drifts on paragraph-length text, and spacing and alignment degrade over long lines.
- Output quality depends heavily on sample quality. Blurry or faint samples reduce fidelity.
- Generation takes several minutes per sentence on GPU. CPU is considerably slower.
- Evaluation so far is qualitative. Quantitative evaluation (CER via TrOCR, FID) is planned.

**Responsible use:** handwriting synthesis can be misused for forgery. Use it only with your own handwriting or with explicit consent.

## Team

| Member | Contribution |
|---|---|
| **Haris Javed** (team lead) | Model research and selection; adaptation of DiffusionPen to custom user styles (UNet style injection, preprocessing); generation pipeline; FastAPI generation endpoints; TrOCR integration |
| **Hamza Hameed** | React frontend (landing page, dashboard, generation and detection pages), PDF export and Authentication |
| **Zara Arif** | Research, testing and project report |

Supervisor: **Ms. Asia Samreen**, Department of Computer Science, Bahria University Karachi Campus

> Note: the commit history doesn't reflect individual contributions, because the code was consolidated and pushed from a single account. The table above shows who did what.


## Acknowledgements and citation

This project would not exist without DiffusionPen. If you use this work, please cite the original paper:

```bibtex
@inproceedings{nikolaidou2024diffusionpen,
  title     = {DiffusionPen: Towards Controlling the Style of Handwritten Text Generation},
  author    = {Nikolaidou, Konstantina and Retsinas, George and Sfikas, Giorgos and Liwicki, Marcus},
  booktitle = {European Conference on Computer Vision (ECCV)},
  year      = {2024}
}
```

We also use the [IAM Handwriting Database](https://fki.tic.heia-fr.ch/databases/iam-handwriting-database), [Microsoft TrOCR](https://huggingface.co/microsoft/trocr-base-handwritten) and [Google CANINE](https://huggingface.co/google/canine-c).

## License

MIT. See [LICENSE](LICENSE). The original DiffusionPen code is © 2024 Konstantina Nikolaidou, also under the MIT License.
