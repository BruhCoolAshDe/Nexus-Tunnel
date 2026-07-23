from setuptools import setup, find_packages

setup(
    name='nexus-tunnel',
    version='2.0.0',
    description='Roblox Studio local testing tool with GUI',
    author='BruhCoolAshDe',
    packages=find_packages(),
    python_requires='>=3.10',
    install_requires=[
        'pillow>=9.0.0',
        'customtkinter>=5.0.0',
    ],
    entry_points={
        'console_scripts': [
            'nexus-tunnel=nexus_tunnel.main:main',
        ],
    },
)
