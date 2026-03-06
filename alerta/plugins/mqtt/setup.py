from setuptools import setup, find_packages

version = '0.0.1'

setup(
    name="alerta-mqtt",
    version=version,
    description='publish processed alert to Mqtt broker',
    url='https://gitlab.ifremer.fr/amrit/development/notification-center/alerta/',
    license='Apache License 2.0',
    author='Yvan Lubac',
    author_email='yvan.lubac@euro-argo.eu',
    packages=find_packages(),
    py_modules=['alerta_mqtt'],
    install_requires=['paho-mqtt'],
    include_package_data=True,
    zip_safe=True,
    entry_points={
        'alerta.plugins': [
            'mqtt = alerta_mqtt:MqttPublisher'
        ]
    }
)