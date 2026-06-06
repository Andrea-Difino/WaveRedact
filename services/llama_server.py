import urllib.request
import zipfile
import os

class LlamaServerService:

    def __init__(self):
        self.destination_folder = "./files/server/"
        self.exe_path = os.path.join(self.destination_folder, "llama-server.exe")

        self._init_server()
    
    def _init_server(self) -> None:
        if os.path.exists(self.exe_path):
            return None
            
        print("Download del motore AI (llama.cpp) in corso...")
        os.makedirs(self.destination_folder, exist_ok=True)

        url_zip = "https://github.com/ggml-org/llama.cpp/releases/download/b9538/cudart-llama-bin-win-cuda-12.4-x64.zip"
        percorso_zip = os.path.join(self.destination_folder, "llama.zip")
        
        urllib.request.urlretrieve(url_zip, percorso_zip)

        with zipfile.ZipFile(percorso_zip, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if "llama-server.exe" in file:
                    zip_ref.extract(file, self.destination_folder)

        os.remove(percorso_zip)
        print("✅ Motore AI installato con successo!")

    def start_server(self):
        ...

