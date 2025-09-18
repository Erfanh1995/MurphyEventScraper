import PyInstaller.__main__
import platform
import os

# --- Configuration ---
SCRIPT_NAME = 'murphy_event_scraper.py'
EXECUTABLE_NAME = 'murphy_event_scraper'
ICON_WINDOWS = 'murphy-logo.ico' 
ICON_MACOS = 'murphy-logo.icns'   
# ---------------------

def main():
    """Builds the executable using PyInstaller."""
    
    # Common PyInstaller arguments
    # '--onefile' creates a single executable
    # '--windowed' prevents the console window from appearing on run
    # Use '--console' instead of '--windowed' if you need to debug
    pyinstaller_args = [
        '--name=%s' % EXECUTABLE_NAME,
        '--onefile',
        '--clean',
        '--windowed',
    ]

    # Add any hidden imports that PyInstaller might miss
    # pytz is often a tricky one for PyInstaller
    pyinstaller_args.extend(['--hidden-import=pytz.zoneinfo'])

    # Add platform-specific arguments
    if platform.system() == 'Windows' and ICON_WINDOWS:
        pyinstaller_args.append(f'--icon={ICON_WINDOWS}')
    elif platform.system() == 'Darwin' and ICON_MACOS: # macOS
        pyinstaller_args.append(f'--icon={ICON_MACOS}')

    # Add the script to be bundled
    pyinstaller_args.append(SCRIPT_NAME)

    print(f"Building application for {platform.system()}...")
    print(f"Running command: pyinstaller {' '.join(pyinstaller_args)}")

    try:
        # Execute the PyInstaller command
        PyInstaller.__main__.run(pyinstaller_args)
        print("\nBuild complete!")
        print(f"Executable created in the '{os.path.join(os.getcwd(), 'dist')}' folder.")
    except Exception as e:
        print(f"\nAn error occurred during the build process: {e}")

if __name__ == '__main__':
    main()
