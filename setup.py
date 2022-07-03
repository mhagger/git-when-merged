"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""


from pathlib import Path

import setuptools


if __name__ == "__main__":
    setuptools.setup(
        name="git-when-merged",
        description="Determine when a particular commit was merged into a git branch",
        long_description=Path("README.md").read_text(),
        long_description_content_type="text/markdown",
        author="Michael Haggerty",
        author_email="mhagger@alum.mit.edu",
        license="GPLv2+",
        url="https://pypi.org/project/git-when-merged",
        project_urls={
            "Code": "https://github.com/mhagger/git-when-merged",
            "Issues": "https://github.com/mhagger/git-when-merged/issues",
        },
        package_dir={"": "src"},
        packages=setuptools.find_packages("src"),
        include_package_data=True,
        py_modules=[path.stem for path in Path(__file__).parent.glob("src/*.py")],
        python_requires=">= 3.7",
        install_requires=[],
        entry_points={"console_scripts": ["git-when-merged = git_when_merged:main"]},
        classifiers=[
            "License :: OSI Approved"
            " :: GNU General Public License v2 or later (GPLv2+)",
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "Intended Audience :: End Users/Desktop",
            "Topic :: Software Development :: Version Control",
            "Topic :: Software Development :: Version Control :: Git",
            "Topic :: Utilities",
            "Environment :: Console",
        ],
    )
