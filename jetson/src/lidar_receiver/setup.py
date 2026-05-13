from setuptools import setup
import os
from glob import glob

setup(
    name='lidar_receiver',
    version='1.0.0',
    packages=['lidar_receiver'],
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/lidar_receiver']),
        ('share/lidar_receiver', ['package.xml']),
        (os.path.join('share', 'lidar_receiver', 'launch'), glob(os.path.join('launch', '*.*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='ubuntu@todo.com',
    description='Lidar receiver for receiving scan data from Pi3',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'lidar_receiver_node = lidar_receiver.lidar_receiver_node:main',
        ],
    },
)
