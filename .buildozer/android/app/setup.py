from setuptools import setup, find_packages

setup(
    name='JarvisPrime',
    version='0.1',
    description='Jarvis Prime AI Assistant',
    author='Zachary Gaudet',
    packages=find_packages(include=['core', 'dfs', 'traid', 'swarm']),  # Include main modules
    include_package_data=True,
    install_requires=[
        # Add dependencies if needed, e.g., 'requests', 'pandas'
    ],
)
