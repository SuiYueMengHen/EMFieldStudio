import json
import os
from datetime import datetime
from typing import Optional

import numpy as np

from .logger import get_logger

logger = get_logger()


class IOHandler:

    @staticmethod
    def export_image(filepath: str, intensity: np.ndarray,
                     colormap_name: str = 'hot', dpi: int = 300,
                     metadata: dict = None):
        ext = os.path.splitext(filepath)[1].lower()

        if ext in ('.png', '.jpg', '.jpeg', '.bmp'):
            IOHandler._export_standard_image(filepath, intensity, colormap_name, dpi)
        elif ext in ('.tif', '.tiff'):
            IOHandler._export_tiff(filepath, intensity, metadata)
        elif ext == '.h5':
            IOHandler._export_hdf5(filepath, intensity, metadata)
        else:
            logger.warning(f"Unknown image format: {ext}, defaulting to PNG")
            IOHandler._export_standard_image(filepath + '.png', intensity, colormap_name, dpi)

    @staticmethod
    def _export_standard_image(filepath: str, intensity: np.ndarray,
                                colormap_name: str, dpi: int):
        try:
            from PIL import Image

            normalized = IOHandler._normalize_for_display(intensity)
            rgb = IOHandler._apply_colormap(normalized, colormap_name)
            rgb_uint8 = (rgb * 255).astype(np.uint8)

            img = Image.fromarray(rgb_uint8)
            img.save(filepath, dpi=(dpi, dpi))
            logger.info(f"Image exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export image: {e}")

    @staticmethod
    def _export_tiff(filepath: str, intensity: np.ndarray, metadata: dict = None):
        try:
            import tifffile
            tifffile.imwrite(filepath, intensity.astype(np.float32),
                             metadata=metadata)
            logger.info(f"TIFF exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export TIFF: {e}")

    @staticmethod
    def _export_hdf5(filepath: str, intensity: np.ndarray, metadata: dict = None):
        try:
            import h5py
            with h5py.File(filepath, 'w') as f:
                f.create_dataset('intensity', data=intensity)
                if metadata:
                    meta_group = f.create_group('metadata')
                    for key, value in metadata.items():
                        meta_group.attrs[key] = str(value)
            logger.info(f"HDF5 exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export HDF5: {e}")

    @staticmethod
    def export_data(filepath: str, x: np.ndarray, y: np.ndarray,
                    x_label: str = 'x', y_label: str = 'y'):
        ext = os.path.splitext(filepath)[1].lower()

        if ext == '.csv':
            IOHandler._export_csv(filepath, x, y, x_label, y_label)
        elif ext == '.h5':
            IOHandler._export_profile_hdf5(filepath, x, y, x_label, y_label)
        else:
            IOHandler._export_csv(filepath, x, y, x_label, y_label)

    @staticmethod
    def _export_csv(filepath: str, x: np.ndarray, y: np.ndarray,
                    x_label: str, y_label: str):
        try:
            import csv
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([x_label, y_label])
                for xi, yi in zip(x, y):
                    writer.writerow([xi, yi])
            logger.info(f"CSV data exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")

    @staticmethod
    def _export_profile_hdf5(filepath: str, x: np.ndarray, y: np.ndarray,
                              x_label: str, y_label: str):
        try:
            import h5py
            with h5py.File(filepath, 'w') as f:
                f.create_dataset(x_label, data=x)
                f.create_dataset(y_label, data=y)
            logger.info(f"HDF5 data exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export HDF5 data: {e}")

    @staticmethod
    def _normalize_for_display(data: np.ndarray) -> np.ndarray:
        data_log = np.log1p(data)
        d_min, d_max = data_log.min(), data_log.max()
        if d_max > d_min:
            return (data_log - d_min) / (d_max - d_min)
        return np.zeros_like(data_log)

    @staticmethod
    def _apply_colormap(normalized: np.ndarray, colormap_name: str) -> np.ndarray:
        from gui.colormaps import get_colormap
        cmap = get_colormap(colormap_name)
        return cmap(normalized)
