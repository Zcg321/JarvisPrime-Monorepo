from setuptools import setup, find_packages


setup(
    name="JarvisPrime",
    version="0.1",
    description="Jarvis Prime AI Assistant",
    author="Zachary Gaudet",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    install_requires=[
        # Add dependencies if needed, e.g., 'requests', 'pandas'
    ],
)
