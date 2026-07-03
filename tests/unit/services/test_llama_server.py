import os
import pytest
from unittest.mock import patch, MagicMock
import requests
from waveredact.services.llama_server import LlamaServerService

MODULE_PATH = "waveredact.services.llama_server"

@pytest.fixture
def mock_atexit():
    """Prevents atexit to register the closing of the server during tests."""
    with patch(f"{MODULE_PATH}.atexit.register") as mock:
        yield mock

@pytest.fixture(autouse=True)
def mock_platform():
    """
    Inganna la classe facendole credere di girare su Windows.
    Risolve il problema dei nomi dei file (.exe) e previene il crash di
    os.stat quando _make_executable cerca di modificare percorsi finti su Linux.
    """
    with patch(f"{MODULE_PATH}.platform.system", return_value="Windows"):
        yield

class TestLlamaServerService:

    @patch(f"{MODULE_PATH}.os.path.exists")
    @patch(f"{MODULE_PATH}.os.walk")
    def test_init_skips_download_if_executable_exists(self, mock_walk, mock_exists, mock_atexit):
        mock_exists.return_value = True
        mock_walk.return_value = [("/fake/path", [], ["llama-server.exe", "altro.txt"])]

        with patch(f"{MODULE_PATH}.urllib.request.urlretrieve") as mock_urlretrieve:
            service = LlamaServerService("fake_model.gguf")

        mock_urlretrieve.assert_not_called()
        assert service.exe_path == os.path.join("/fake/path", "llama-server.exe")

    @patch(f"{MODULE_PATH}.os.path.exists")
    @patch(f"{MODULE_PATH}.os.walk")
    @patch(f"{MODULE_PATH}.urllib.request.urlretrieve")
    @patch(f"{MODULE_PATH}.zipfile.ZipFile")
    @patch(f"{MODULE_PATH}.os.remove")
    @patch(f"{MODULE_PATH}.os.makedirs")
    def test_init_downloads_and_extracts_if_missing(
        self, mock_makedirs, mock_remove, mock_zip, mock_urlretrieve, mock_walk, mock_exists, mock_atexit
    ):
        mock_exists.return_value = True
        mock_walk.side_effect = [
            [("/fake/path", [], [])],
            [("/fake/path", [], ["llama-server.exe"])]
        ]

        service = LlamaServerService("fake_model.gguf")

        mock_makedirs.assert_called_once_with(service.destination_folder, exist_ok=True)
        mock_urlretrieve.assert_called_once()
        mock_zip.assert_called_once()
        mock_remove.assert_called_once()
        assert service.exe_path == os.path.join("/fake/path", "llama-server.exe")

    @patch(f"{MODULE_PATH}.os.path.exists")
    @patch(f"{MODULE_PATH}.os.walk")
    @patch(f"{MODULE_PATH}.urllib.request.urlretrieve")
    @patch(f"{MODULE_PATH}.zipfile.ZipFile")
    @patch(f"{MODULE_PATH}.os.remove")
    @patch(f"{MODULE_PATH}.os.makedirs")
    def test_init_raises_error_if_extraction_fails(
        self, mock_makedirs, mock_remove, mock_zip, mock_urlretrieve, mock_walk, mock_exists, mock_atexit
    ):
        mock_exists.return_value = True
        mock_walk.side_effect = [
            [("/fake/path", [], [])],
            [("/fake/path", [], [])]
        ]

        with pytest.raises(FileNotFoundError, match="Critical error: llama-server.exe not found"):
            LlamaServerService("fake_model.gguf")

    @patch(f"{MODULE_PATH}.LlamaServerService._init_server") 
    @patch(f"{MODULE_PATH}.os.path.exists")
    @patch(f"{MODULE_PATH}.os.walk")
    def test_find_executable_success(self, mock_walk, mock_exists, mock_init, mock_atexit):
        mock_exists.return_value = True

        mock_walk.return_value = [("/fake/destination", [], ["llama-server.exe", "altro_file.txt"])]
        
        service = LlamaServerService("fake_model.gguf")
        exe_path = service._find_executable()

        assert exe_path == os.path.join("/fake/destination", "llama-server.exe")

    @patch(f"{MODULE_PATH}.LlamaServerService._find_executable", return_value="/fake/exe")
    @patch(f"{MODULE_PATH}.subprocess.Popen")
    @patch(f"{MODULE_PATH}.requests.get")
    def test_start_server_success(self, mock_get, mock_popen, mock_find_exe, mock_atexit):
        service = LlamaServerService("fake_model.gguf")
        
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_get.side_effect = [requests.exceptions.ConnectionError, mock_response_ok]

        service.start_server()

        mock_popen.assert_called_once()

        assert mock_get.call_count == 2
        assert service.process == mock_process

    @patch(f"{MODULE_PATH}.LlamaServerService._find_executable", return_value="/fake/exe")
    @patch(f"{MODULE_PATH}.subprocess.Popen")
    @patch(f"{MODULE_PATH}.requests.get")
    @patch(f"{MODULE_PATH}.time.sleep") 
    def test_start_server_timeout(self, mock_sleep, mock_get, mock_popen, mock_find_exe, mock_atexit):
        service = LlamaServerService("fake_model.gguf")
        mock_popen.return_value = MagicMock()

        mock_get.side_effect = requests.exceptions.ConnectionError

        with pytest.raises(RuntimeError, match="Server didn't start in time"):
            service.start_server()

        assert mock_get.call_count == 30
        assert mock_sleep.call_count == 30

    @patch(f"{MODULE_PATH}.LlamaServerService._find_executable", return_value="/fake/exe")
    def test_stop_server(self, mock_find_exe, mock_atexit):
        service = LlamaServerService("fake_model.gguf")

        mock_process = MagicMock()
        service.process = mock_process

        service.stop_server()

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        assert service.process is None

    @patch(f"{MODULE_PATH}.LlamaServerService._find_executable", return_value="/fake/exe")
    def test_stop_server_no_process(self, mock_find_exe, mock_atexit):
        service = LlamaServerService("fake_model.gguf")
        service.process = None

        service.stop_server()