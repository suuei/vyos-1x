# Copyright 2019 VyOS maintainers and contributors <maintainers@vyos.io>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.

from copy import deepcopy

from vyos import ConfigError
from vyos.ifconfig.interface import Interface


@Interface.register
class VXLANIf(Interface):
    """
    The VXLAN protocol is a tunnelling protocol designed to solve the
    problem of limited VLAN IDs (4096) in IEEE 802.1q. With VXLAN the
    size of the identifier is expanded to 24 bits (16777216).

    VXLAN is described by IETF RFC 7348, and has been implemented by a
    number of vendors.  The protocol runs over UDP using a single
    destination port.  This document describes the Linux kernel tunnel
    device, there is also a separate implementation of VXLAN for
    Openvswitch.

    Unlike most tunnels, a VXLAN is a 1 to N network, not just point to
    point. A VXLAN device can learn the IP address of the other endpoint
    either dynamically in a manner similar to a learning bridge, or make
    use of statically-configured forwarding entries.

    For more information please refer to:
    https://www.kernel.org/doc/Documentation/networking/vxlan.txt
    """

    default = {
        'type': 'vxlan',
        'vni': 0,
        'dev': '',
        'group': '',
        'remote': '',
        'port': 8472,   # The Linux implementation of VXLAN pre-dates
                        # the IANA's selection of a standard destination port
    }
    definition = {
        **Interface.definition,
        **{
            'section': 'vxlan',
            'prefixes': ['vxlan', ],
            'bridgeable': True,
        }
    }
    options = ['group', 'remote', 'dev', 'port', 'vni']

    mapping = {
        'ifname': 'add',
        'vni':    'id',
        'port':   'dstport',
    }

    def _create(self):
        cmdline = set()
        if self.config['remote']:
            cmdline = ('ifname', 'type', 'remote', 'dev', 'vni', 'port')
        elif self.config['group'] and self.config['dev']:
            cmdline = ('ifname', 'type', 'group', 'dev', 'vni', 'port')
        else:
            intf = self.config['intf']
            raise ConfigError(
                f'VXLAN "{intf}" is missing mandatory underlay interface for a multicast network.')

        cmd = 'ip link'
        for key in cmdline:
            value = self.config.get(key, '')
            if not value:
                continue
            cmd += ' {} {}'.format(self.mapping.get(key, key), value)

        self._cmd(cmd)

    @classmethod
    def get_config(cls):
        """
        VXLAN interfaces require a configuration when they are added using
        iproute2. This static method will provide the configuration dictionary
        used by this class.

        Example:
        >> dict = VXLANIf().get_config()
        """
        return deepcopy(cls.default)
