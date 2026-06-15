import sys
import argparse
import os

os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'

_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)


def run_gui():
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from gui.main_window import MainWindow
    from utils.logger import get_logger

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    logger = get_logger()
    logger.info("Starting DiffractionLab GUI...")

    app = QApplication(sys.argv)
    app.setApplicationName("DiffractionLab")
    app.setOrganizationName("DiffractionLab")

    window = MainWindow()
    window.show()

    logger.info("GUI initialized successfully")
    sys.exit(app.exec())


def run_cli(args):
    from core.aperture import ApertureType, ApertureParams, ApertureFactory
    from core.diffraction import DiffractionEngine, SimulationParams, PropagationModel
    from utils.io_handler import IOHandler
    from utils.logger import get_logger

    logger = get_logger()
    logger.info("Running in CLI mode...")

    model_map = {
        'fraunhofer': PropagationModel.FRAUNHOFER,
        'fresnel_asm': PropagationModel.FRESNEL_ASM,
        'fresnel_ir': PropagationModel.FRESNEL_IR,
        'rayleigh_sommerfeld': PropagationModel.RAYLEIGH_SOMMERFELD,
    }

    type_map = {
        'circle': ApertureType.CIRCLE,
        'rectangle': ApertureType.RECTANGLE,
        'triangle': ApertureType.TRIANGLE,
        'hexagon': ApertureType.HEXAGON,
        'annulus': ApertureType.ANNULUS,
        'star': ApertureType.STAR,
        'double_slit': ApertureType.DOUBLE_SLIT,
        'grating': ApertureType.GRATING,
    }

    at = type_map.get(args.aperture, ApertureType.CIRCLE)
    aperture = ApertureFactory.create(at, params={
        'size': args.size,
    })

    sim_params = SimulationParams(
        wavelength=args.wavelength * 1e-9,
        grid_size=args.grid,
        physical_size=args.physical_size * 1e-6,
        propagation_distance=args.distance,
        model=model_map.get(args.model, PropagationModel.FRAUNHOFER),
    )

    engine = DiffractionEngine(use_gpu=False)
    result = engine.compute_diffraction(aperture, sim_params)

    output = args.output or 'result.h5'
    IOHandler.export_image(output, result.intensity, metadata=result.metadata)
    logger.info(f"Result saved to {output}")


def main():
    parser = argparse.ArgumentParser(
        description='DiffractionLab - 衍射仿真软件'
    )
    parser.add_argument('--cli', action='store_true',
                        help='Run in CLI mode')
    parser.add_argument('--aperture', type=str, default='circle',
                        choices=['circle', 'rectangle', 'triangle', 'hexagon',
                                 'annulus', 'star', 'double_slit', 'grating'],
                        help='Aperture type')
    parser.add_argument('--size', type=float, default=50,
                        help='Aperture size (μm)')
    parser.add_argument('--wavelength', type=float, default=532,
                        help='Wavelength (nm)')
    parser.add_argument('--grid', type=int, default=1024,
                        help='Grid size')
    parser.add_argument('--physical-size', type=float, default=200,
                        help='Physical size (μm)')
    parser.add_argument('--distance', type=float, default=0.1,
                        help='Propagation distance (m)')
    parser.add_argument('--model', type=str, default='fraunhofer',
                        choices=['fraunhofer', 'fresnel_asm', 'fresnel_ir',
                                 'rayleigh_sommerfeld'],
                        help='Propagation model')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file path')

    args = parser.parse_args()

    if args.cli:
        run_cli(args)
    else:
        run_gui()


if __name__ == '__main__':
    main()
