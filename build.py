import PyInstaller.__main__
import shutil
import os

app_path = str(os.path.dirname(os.path.realpath(__file__)) + '\\app.py')
assets_path = str(os.path.dirname(os.path.realpath(__file__)) + '\\assets')
icon_path = str(os.path.dirname(os.path.realpath(__file__)) + '\\assets\\distatus.ico')
build_path = str(os.path.dirname(os.path.realpath(__file__)) + '\\dist\\assets')

def build():
 # Clean previous builds
 shutil.rmtree('dist', ignore_errors=True)
 shutil.rmtree('build', ignore_errors=True)

 # Build the executable
 PyInstaller.__main__.run([
  app_path,
  '--name=distatus',
  '--onefile',
  '--windowed',
  '--icon=' + icon_path,
  '--add-data=' + assets_path + ';assets',
 ])

 # shutil.copyfile(assets_path, build_path)

if __name__ == '__main__':
 build()
 print("Build completed successfully.")
