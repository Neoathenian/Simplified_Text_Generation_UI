import argparse
import glob
import hashlib
import os
import platform
import re
import signal
import site
import subprocess
import sys

script_dir = os.getcwd()
conda_env_path = os.path.join(script_dir, "installer_files", "env")

# Command-line flags
cmd_flags_path = os.path.join(script_dir, "CMD_FLAGS.txt")
if os.path.exists(cmd_flags_path):
    with open(cmd_flags_path, 'r') as f:
        CMD_FLAGS = ' '.join(line.strip().rstrip('\\').strip() for line in f if line.strip().rstrip('\\').strip() and not line.strip().startswith('#'))
else:
    CMD_FLAGS = ''

flags = f"{' '.join([flag for flag in sys.argv[1:] if flag != '--update'])} {CMD_FLAGS}"


def signal_handler(sig, frame):
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)



def is_windows():
    return sys.platform.startswith("win")

def is_installed():
    site_packages_path = None
    for sitedir in site.getsitepackages():
        if "site-packages" in sitedir and conda_env_path in sitedir:
            site_packages_path = sitedir
            break
    print(conda_env_path)
    #if site_packages_path:
    #    return os.path.isfile(os.path.join(site_packages_path, 'torch', '__init__.py'))
    #else:
    return os.path.isdir(conda_env_path)


def check_env():
    # If we have access to conda, we are probably in an environment
    conda_exist = run_cmd("conda", environment=True, capture_output=True).returncode == 0
    if not conda_exist:
        print("Conda is not installed. Exiting...")
        sys.exit(1)

    # Ensure this is a new environment and not the base environment
    if os.environ["CONDA_DEFAULT_ENV"] == "base":
        print("Create an environment for this project and activate it. Exiting...")
        sys.exit(1)


def clear_cache():
    run_cmd("conda clean -a -y", environment=True)
    run_cmd("python -m pip cache purge", environment=True)


def print_big_message(message):
    message = message.strip()
    lines = message.split('\n')
    print("\n\n*******************************************************************")
    for line in lines:
        if line.strip() != '':
            print("*", line)

    print("*******************************************************************\n\n")


def calculate_file_hash(file_path):
    p = os.path.join(script_dir, file_path)
    if os.path.isfile(p):
        with open(p, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    else:
        return ''


def run_cmd(cmd, assert_success=False, environment=False, capture_output=False, env=None):
    # Use the conda environment
    if environment:
        if is_windows():
            conda_bat_path = os.path.join(script_dir, "installer_files", "conda", "condabin", "conda.bat")
            cmd = "\"" + conda_bat_path + "\" activate \"" + conda_env_path + "\" >nul && " + cmd
        else:
            conda_sh_path = os.path.join(script_dir, "installer_files", "conda", "etc", "profile.d", "conda.sh")
            cmd = ". \"" + conda_sh_path + "\" && conda activate \"" + conda_env_path + "\" && " + cmd

    # Run shell commands
    result = subprocess.run(cmd, shell=True, capture_output=capture_output, env=env)

    # Assert the command ran successfully
    if assert_success and result.returncode != 0:
        print("Command '" + cmd + "' failed with exit status code '" + str(result.returncode) + "'.\n\nExiting now.\nTry running the start/update script again.")
        sys.exit(1)

    return result


def install_webui():
    install_git = "conda install -y -k ninja git"

    run_cmd(f"{install_git}", assert_success=True, environment=True)
    #run_cmd(f"{install_git} && python -m pip install py-cpuinfo==9.0.0", assert_success=True, environment=True)
    # Install the webui requirements
    update_requirements(initial_installation=True)


def update_requirements(initial_installation=False):
    # Create .git directory if missing
    #if not os.path.isdir(os.path.join(script_dir, ".git")):
    #    git_creation_cmd = 'git init -b main && git remote add origin https://github.com/oobabooga/text-generation-webui && git fetch && git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main && git reset --hard origin/main && git branch --set-upstream-to=origin/main'
    #    run_cmd(git_creation_cmd, environment=True, assert_success=True)

    files_to_check = [
        'start_linux.sh', 'start_macos.sh', 'start_windows.bat', 'start_wsl.bat',
        'update_linux.sh', 'update_macos.sh', 'update_windows.bat', 'update_wsl.bat',
        'one_click.py'
    ]

    before_pull_hashes = {file_name: calculate_file_hash(file_name) for file_name in files_to_check}
    run_cmd("git pull --autostash", assert_success=True, environment=True)
    after_pull_hashes = {file_name: calculate_file_hash(file_name) for file_name in files_to_check}

    # Check for differences in installation file hashes
    for file_name in files_to_check:
        if before_pull_hashes[file_name] != after_pull_hashes[file_name]:
            print_big_message(f"File '{file_name}' was updated during 'git pull'. Please run the script again.")
            exit(1)

    # Extensions requirements are installed only during the initial install by default.
    # That can be changed with the INSTALL_EXTENSIONS environment variable.
    install = initial_installation
    if "INSTALL_EXTENSIONS" in os.environ:
        install = os.environ["INSTALL_EXTENSIONS"].lower() in ("yes", "y", "true", "1", "t", "on")

    if install:
        print_big_message("Installing extensions requirements.")
        skip = ['superbooga', 'superboogav2', 'coqui_tts']  # Fail to install on Windows
        extensions = [foldername for foldername in os.listdir('extensions') if os.path.isfile(os.path.join('extensions', foldername, 'requirements.txt'))]
        extensions = [x for x in extensions if x not in skip]
        for i, extension in enumerate(extensions):
            print(f"\n\n--- [{i+1}/{len(extensions)}]: {extension}\n\n")
            extension_req_path = os.path.join("extensions", extension, "requirements.txt")
            run_cmd("python -m pip install -r " + extension_req_path + " --upgrade", assert_success=False, environment=True)
    elif initial_installation:
        print_big_message("Will not install extensions due to INSTALL_EXTENSIONS environment variable.")

    base_requirements = "requirements_cpu_only" + ".txt"
 
    requirements_file = base_requirements
    print_big_message(f"Installing webui requirements from file: {requirements_file}")

    ### Prepare the requirements file
    textgen_requirements = open(requirements_file).read().splitlines()
    print(textgen_requirements)
    textgen_requirements = [req for req in textgen_requirements if 'jllllll/flash-attention' not in req]

    print_big_message("Installing temp_requirements")
    with open('temp_requirements.txt', 'w') as file:
        file.write('\n'.join(textgen_requirements))

    # Workaround for git+ packages not updating properly.
    git_requirements = [req for req in textgen_requirements if req.startswith("git+")]
    for req in git_requirements:
        url = req.replace("git+", "")
        package_name = url.split("/")[-1].split("@")[0].rstrip(".git")
        run_cmd("python -m pip uninstall -y " + package_name, environment=True)
        print(f"Uninstalled {package_name}")

    # Make sure that API requirements are installed (temporary)
    extension_req_path = os.path.join("extensions", "openai", "requirements.txt")
    if os.path.exists(extension_req_path):
        run_cmd("python -m pip install -r " + extension_req_path + " --upgrade", environment=True)

    # Install/update the project requirements
    run_cmd("python -m pip install -r temp_requirements.txt --upgrade", assert_success=True, environment=True)
    os.remove('temp_requirements.txt')

    if not os.path.exists("repositories/"):
        os.mkdir("repositories")

    clear_cache()


def launch_webui():
    run_cmd(f"python server.py {flags}", environment=True)


if __name__ == "__main__":
    # Verifies we are in a conda environment
    check_env()

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--update', action='store_true', help='Update the web UI.')
    args, _ = parser.parse_known_args()

    if args.update:
        update_requirements()
    else:
        # If webui has already been installed, skip and run
        if not is_installed():
            print("HOLLLLLLLLLLLLLLLLLLLL")
            install_webui()
            os.chdir(script_dir)

        if os.environ.get("LAUNCH_AFTER_INSTALL", "").lower() in ("no", "n", "false", "0", "f", "off"):
            print_big_message("Install finished successfully and will now exit due to LAUNCH_AFTER_INSTALL.")
            sys.exit()

        # Check if a model has been downloaded yet
        if '--model-dir' in flags:
            # Splits on ' ' or '=' while maintaining spaces within quotes
            flags_list = re.split(' +(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)|=', flags)
            model_dir = [flags_list[(flags_list.index(flag) + 1)] for flag in flags_list if flag == '--model-dir'][0].strip('"\'')
        else:
            model_dir = 'models'

        # Workaround for llama-cpp-python loading paths in CUDA env vars even if they do not exist
        conda_path_bin = os.path.join(conda_env_path, "bin")
        if not os.path.exists(conda_path_bin):
            os.mkdir(conda_path_bin)

        # Launch the webui
        launch_webui()
