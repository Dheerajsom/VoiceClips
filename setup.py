from setuptools import setup, find_packages

setup(
    name='VoiceClips',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'pyaudio',
        'speech_recognition',
        'opencv-python',
        'moviepy',
        'tkinter',
        'pytest'
    ],
)
