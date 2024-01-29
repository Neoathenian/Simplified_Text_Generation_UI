# Text generation web UI

Simplified UI from Oobabooga

## How to install

1) Clone or [download](https://github.com/oobabooga/text-generation-webui/archive/refs/heads/main.zip) the repository.
2) Run the `start_linux.sh`, `start_windows.bat`, `start_macos.sh`, or `start_wsl.bat` script depending on your OS.
3) Select your GPU vendor when asked.
4) Once the installation ends, browse to `http://localhost:7860/?__theme=dark`.
5) Have fun!

To restart the web UI in the future, just run the `start_` script again. This script creates an `installer_files` folder where it sets up the project's requirements. In case you need to reinstall the requirements, you can simply delete that folder and start the web UI again.

The script accepts command-line flags. Alternatively, you can edit the `CMD_FLAGS.txt` file with a text editor and add your flags there.

To get updates in the future, run `update_linux.sh`, `update_windows.bat`, `update_macos.sh`, or `update_wsl.bat`.

<details>
<summary>
Setup details and information about installing manually
</summary>

### One-click-installer

The script uses Miniconda to set up a Conda environment in the `installer_files` folder.

If you ever need to install something manually in the `installer_files` environment, you can launch an interactive shell using the cmd script: `cmd_linux.sh`, `cmd_windows.bat`, `cmd_macos.sh`, or `cmd_wsl.bat`.

* There is no need to run any of those scripts (`start_`, `update_`, or `cmd_`) as admin/root.
* For additional instructions about AMD and WSL setup, consult [the documentation](https://github.com/oobabooga/text-generation-webui/wiki).
* For automated installation, you can use the `GPU_CHOICE`, `USE_CUDA118`, `LAUNCH_AFTER_INSTALL`, and `INSTALL_EXTENSIONS` environment variables. For instance: `GPU_CHOICE=A USE_CUDA118=FALSE LAUNCH_AFTER_INSTALL=FALSE INSTALL_EXTENSIONS=FALSE ./start_linux.sh`.

### Manual installation using Conda

Recommended if you have some experience with the command-line.

#### 0. Install Conda

https://docs.conda.io/en/latest/miniconda.html

On Linux or WSL, it can be automatically installed with these two commands ([source](https://educe-ubc.github.io/conda.html)):

```
curl -sL "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh" > "Miniconda3.sh"
bash Miniconda3.sh
```

#### 1. Create a new conda environment

```
conda create -n textgen python=3.11
conda activate textgen
```

#### 2. Install Pytorch

| System | GPU | Command |
|--------|---------|---------|
| Linux/WSL | NVIDIA | `pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121` |
| Linux/WSL | CPU only | `pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu` |
| Linux | AMD | `pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.6` |
| MacOS + MPS | Any | `pip3 install torch torchvision torchaudio` |
| Windows | NVIDIA | `pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121` |
| Windows | CPU only | `pip3 install torch torchvision torchaudio` |

The up-to-date commands can be found here: https://pytorch.org/get-started/locally/.

For NVIDIA, you also need to install the CUDA runtime libraries:

```
conda install -y -c "nvidia/label/cuda-12.1.1" cuda-runtime
```

If you need `nvcc` to compile some library manually, replace the command above with

```
conda install -y -c "nvidia/label/cuda-12.1.1" cuda
```

#### 3. Install the web UI

```
git clone https://github.com/oobabooga/text-generation-webui
cd text-generation-webui
pip install -r <requirements file according to table below>
```

### Start the web UI

```
conda activate textgen
cd text-generation-webui
python server.py
```

Then browse to

`http://localhost:7860/?__theme=dark`

##### Manual install

The `requirements*.txt` above contain various wheels precompiled through GitHub Actions. If you wish to compile things manually, or if you need to because no suitable wheels are available for your hardware, you can use `requirements_nowheels.txt` and then install your desired loaders manually.

## Documentation

https://github.com/oobabooga/text-generation-webui/wiki

## Acknowledgment

In August 2023, [Andreessen Horowitz](https://a16z.com/) (a16z) provided a generous grant to encourage and support my independent work on this project. I am **extremely** grateful for their trust and recognition.
