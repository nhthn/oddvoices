import setuptools

setuptools.setup(
    name="oddvoices",
    version="0.0.1",
    license="MIT",
    description="Python part of OddVoices, a speech synthesizer.",
    author="Nathan Ho",
    packages=setuptools.find_packages("python"),
    package_dir={"": "python"},
    python_requires=">=3.8",
    install_requires=["numpy", "scipy", "soundfile", "mido"],
    entry_points={
        "console_scripts": [
            "sing = oddvoices.frontend:main",
            "sing-midi = oddvoices.midi_frontend:main",
            "oddvoices-compile = oddvoices.corpus:main",
            "oddvoices-generate-wordlist = oddvoices.phonology:generate_wordlist",
        ],
    },
    package_data={
        "oddvoices": ["cmudict-0.7b"],
    }
)
