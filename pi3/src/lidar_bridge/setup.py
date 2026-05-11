import os
from glob import glob
from setuptools import setup

package_name = 'lidar_bridge'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('lib/' + package_name, ['lidar_bridge/lidar_bridge_node.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='ubuntu@todo.com',
    description='Lidar bridge for forwarding scan data to Jetson',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'lidar_bridge_node = lidar_bridge.lidar_bridge_node:main',
        ],
    },
)
