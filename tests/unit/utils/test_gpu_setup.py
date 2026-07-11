import os
import pytest
from unittest.mock import patch, MagicMock
from waveredact.utils.gpu_setup import GPUEnvironmentManager

MODULE_PATH = "waveredact.utils.gpu_setup"


class TestGPUEnvironmentManager:

    @patch(f"{MODULE_PATH}.sys.platform", "linux")
    @patch(f"{MODULE_PATH}.os.makedirs")
    def test_ensure_gpu_ready_skips_on_non_windows(self, mock_makedirs):
        manager = GPUEnvironmentManager()

        manager.ensure_gpu_ready()

        mock_makedirs.assert_not_called()

    @patch(f"{MODULE_PATH}.sys.platform", "win32")
    @patch(f"{MODULE_PATH}.os.makedirs")
    @patch(f"{MODULE_PATH}.os.path.exists")
    @patch.object(GPUEnvironmentManager, '_download_and_extract_dlls')
    @patch.object(GPUEnvironmentManager, '_inject_dlls')
    def test_ensure_gpu_ready_windows_dll_exists(
        self, mock_inject, mock_download, mock_exists, mock_makedirs
    ):
        manager = GPUEnvironmentManager()
        manager.device = "cuda"

        mock_exists.return_value = True

        manager.ensure_gpu_ready()

        mock_makedirs.assert_called_once_with(manager.dll_folder, exist_ok=True)

        mock_download.assert_not_called()
        mock_inject.assert_called_once()

    @patch(f"{MODULE_PATH}.sys.platform", "win32")
    @patch(f"{MODULE_PATH}.os.makedirs")
    @patch(f"{MODULE_PATH}.os.path.exists")
    @patch.object(GPUEnvironmentManager, '_download_and_extract_dlls')
    @patch.object(GPUEnvironmentManager, '_inject_dlls')
    def test_ensure_gpu_ready_windows_dll_missing(
        self, mock_inject, mock_download, mock_exists, mock_makedirs
    ):
        manager = GPUEnvironmentManager()
        manager.device = "cuda"

        mock_exists.return_value = False

        manager.ensure_gpu_ready()

        mock_makedirs.assert_called_once()
        mock_download.assert_called_once()
        mock_inject.assert_called_once()

    @patch(f"{MODULE_PATH}.urllib.request.urlretrieve")
    @patch(f"{MODULE_PATH}.zipfile.ZipFile")
    @patch(f"{MODULE_PATH}.os.remove")
    def test_download_and_extract_dlls(self, mock_remove, mock_zip, mock_urlretrieve):
        manager = GPUEnvironmentManager()

        manager._download_and_extract_dlls()

        mock_urlretrieve.assert_called_once()

        mock_zip.assert_called_once()
        mock_remove.assert_called_once()

    @patch(f"{MODULE_PATH}.os.add_dll_directory", create=True)
    def test_inject_dlls_success(self, mock_add_dll):
        manager = GPUEnvironmentManager()
        manager.dll_folder = "C:\\fake\\dll\\path"
        
        with patch.dict(os.environ, {"PATH": "C:\\Original\\Path"}, clear=True):
            manager._inject_dlls()

            mock_add_dll.assert_called_once_with("C:\\fake\\dll\\path")
            
            assert os.environ["PATH"] == "C:\\fake\\dll\\path;C:\\Original\\Path"

    @patch(f"{MODULE_PATH}.os.add_dll_directory", create=True)
    @patch(f"{MODULE_PATH}.logger.warning")
    def test_inject_dlls_handles_exception(self, mock_logger, mock_add_dll):
        manager = GPUEnvironmentManager()
        
        mock_add_dll.side_effect = Exception("Access denied")

        try:
            manager._inject_dlls()
        except Exception:
            pytest.fail("Exception not handled correctly in _inject_dlls!")

        mock_logger.assert_called_once()