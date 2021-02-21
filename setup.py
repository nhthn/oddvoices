import setuptools

setuptools.setup(
    name="oddvoices",
    version="0.0.1",
    license="MIT",
    description="Python part of an indie speech synthesizer.",
    author="Nathan Ho",
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=["numpy", "scipy", "soundfile"],
    entry_points={
        "console_scripts": [
            "sing = oddvoices.frontend:main",
            "oddvoices-compile = oddvoices.corpus:main",
        ],
    },
    package_data={
        "oddvoices": ["cmudict-0.7b"],
    }
)
