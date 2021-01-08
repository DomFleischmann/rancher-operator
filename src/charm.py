#!/usr/bin/env python3

import logging

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, WaitingStatus
from ops.framework import StoredState

from oci_image import OCIImageResource, OCIImageResourceError


class RancherCharm(CharmBase):

    def __init__(self, *args):
        super().__init__(*args)
        if not self.unit.is_leader():
            # We can't do anything useful when not the leader, so do nothing.
            self.model.unit.status = WaitingStatus('Waiting for leadership')
            return
        self.log = logging.getLogger(__name__)
        self.rancher_image = OCIImageResource(self, 'rancher-image')
        for event in [self.on.install,
                      self.on.leader_elected,
                      self.on.upgrade_charm,
                      self.on.config_changed]:
            self.framework.observe(event, self.main)

    def main(self, event):

        try:
            rancher_image_details = self.rancher_image.fetch()
        except OCIImageResourceError as e:
            self.model.unit.status = e.status
            return

        self.model.unit.status = MaintenanceStatus('Setting pod spec')

        self.model.pod.set_spec({
            'version': 3,
            'service': {
                'updateStrategy': {
                    'type': 'RollingUpdate',
                    'rollingUpdate': {'maxUnavailable': 1},
                    },
            },
            'configMaps': {
                'kubernetes-dashboard-settings': {},
            },
            'containers': [
                {
                    'name': self.model.app.name,
                    'imageDetails': rancher_image_details,
                    'imagePullPolicy': 'Always',
                    'ports': [
                        {
                            'name': 'rancher',
                            'containerPort': 80,
                            'protocol': 'TCP',
                        },
                    ],
                    'args': [
                        "--https-listen-port=80",
                        "--https-listen-port=443",
                        "--add-local=true",
                        "--debug",
                        ],
                    'envConfig': {
                            'CATTLE_NAMESPACE': self.model.name,
                            'CATTLE_PEER_SERVICE': self.model.app.name,
                    },
                    'kubernetes': {
                        'livenessProbe': {
                            'httpGet': {
                                'scheme': 'HTTPS',
                                'path': '/healthz',
                                'port': 80,
                                },
                            'initialDelaySeconds': 60,
                            'periodSeconds': 30,
                            },
                        'readinessProbe': {
                            'httpGet': {
                                'scheme': 'HTTPS',
                                'path': '/healthz',
                                'port': 80,
                                },
                            'initialDelaySeconds': 5,
                            'periodSeconds': 30,
                        },
                    },
                },
            ],
            'serviceAccount': {
                'roles': [
                    {
                        'global': True,
                        'rules': [
                            {
                                'apiGroups': ["*"],
                                'resources': ["*"],
                                'verbs': ["*"],
                            },
                            {
                                'nonResourceURLs': ["*"],
                                'verbs': ["*"],
                            },
                        ],
                    }
                ],
            },
        })
        self.model.unit.status = ActiveStatus()


if __name__ == "__main__":
    main(RancherCharm)
