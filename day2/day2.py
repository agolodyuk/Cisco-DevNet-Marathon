import argparse

from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.functions.text import print_result

from ntc_templates.parse import parse_output

# L3 точка в сети
class EndPoint:
    
    # все найденные эндпоинты в сети
    end_points = {}

    def __init__(self, switch:str, port:str, vlan:str, mac:str):
        self.switch = switch
        self.port = port
        self.vlan = vlan
        self.mac = mac
   
    def __str__(self):
        return f'{self.mac} on {self.switch}.{self.port} vlan-{self.vlan}'

    @staticmethod
    def add(endpoint):
        EndPoint.end_points[endpoint.mac] = endpoint
    
    @staticmethod
    def get(mac):
        return EndPoint.end_points[mac] if mac in EndPoint.end_points else f"{mac} doesn't exist on LAN"
    
    @staticmethod
    def print_all():
        for ep_mac, ep in EndPoint.end_points.items():
            print(ep)

def build_endpoints():
    
    # get interfaces info
    ifaces_raw = nr.run(netmiko_send_command, command_string='show interfaces')
    for sw_name, sw_result in ifaces_raw.items():
        # print(sw_name)
        data = str(sw_result[0])
        ifaces_list = parse_output(platform="cisco_ios", command="show interfaces", data=data)

        for iface in ifaces_list:
            # skip empty interfaces 
            if iface['link_status'] != 'up' or iface['protocol_status'] != 'up':
                print(f'{iface["interface"]} is down')
                continue
            # SVI is endpoint
            if iface['hardware_type'] == 'EtherSVI':
                print(f'{iface["interface"]} is SVI')
                svi_ep = EndPoint(sw_name,'SVI', iface['interface'], iface['address'])
                EndPoint.add(svi_ep)
                continue

    # get switchports info
    sw_access_ports = {}
    ifaces_sw_raw = nr.run(netmiko_send_command, command_string='show interfaces switchport')
    
    for sw_name, sw_result in ifaces_sw_raw.items():

        sw_access_ports[sw_name] = tuple()
        data = str(sw_result[0])
        ifaces_sw_list = parse_output(platform="cisco_ios", command="show interfaces switchport", data=data)

        for iface_sw_entry in ifaces_sw_list:

            # skip mode=down
            if iface_sw_entry['mode'] == "down":
                print(f'skip down {iface_sw_entry["interface"]}')
                continue

            if iface_sw_entry['admin_mode'] == 'static access':
                 sw_access_ports[sw_name] =  sw_access_ports[sw_name] + (iface_sw_entry["interface"], )
            
            # По хорошему - транковые порты тоже могут содержать эндпоинты. 

        print('access ports=',  sw_access_ports[sw_name])

    # get mac_table with check is mac is end_point ?
    mac_table_raw = nr.run(netmiko_send_command, command_string='show mac address-table')
    for sw_name, sw_result in mac_table_raw.items():

        data = str(sw_result[0])
        mac_table_list = parse_output(platform="cisco_ios", command="show mac address-table", data=data)
        for mac_entry in mac_table_list:

            # skip empty STATIC
            if mac_entry['type'] == 'STATIC':
                print('skip static')
                continue
            if mac_entry['destination_port'] in sw_access_ports[sw_name] :
                ep = EndPoint(sw_name, mac_entry['destination_port'] , mac_entry['vlan'] , mac_entry['destination_address'])
                EndPoint.add(ep)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Find MAC in LAN')
    parser.add_argument('--mac', type=str, dest='mac', help='provide MAC', metavar='aaaa.bbbb.cccc')
    args = parser.parse_args()
    mac = args.mac

    nr = InitNornir(config_file="config.yaml")
    build_endpoints()

    # for testing
    print('\n\n ALL ENDPOINTS:')
    print(EndPoint.print_all())

    print('\n\nRESULT:')
    print(EndPoint.get(mac))