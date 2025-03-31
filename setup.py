from setuptools import setup, find_packages

setup(
    name="Tools_for_LMs",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'requests',
        'googlesearch-python==1.3.0',
        'whoosh==2.7.4',
        'torch==2.6.0',
        'faiss-cpu',
        'sentence-transformers'
    ]
)