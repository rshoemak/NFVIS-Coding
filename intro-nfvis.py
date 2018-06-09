import requests
import json
import os
import nfvis_payload
import time

import nfvis_setup

NFVIS_USERNAME = nfvis_setup['username']
NFVIS_PASSWORD = nfvis_setup['password']
NFVIS = nfvis_setup['host']
new_bridge = "svc-br"
new_network = "svc-net"

requests.packages.urllib3.disable_warnings()

def nvfis_getgcred():
    login = NFVIS_USERNAME
    password = NFVIS_PASSWORD
    url = "https://" + NFVIS
    nip = NFVIS
    return nip, url, login, password

def nfv_get_image_configuration(s, url):
    u = url + '/api/config/vm_lifecycle/images?deep'
    image_configurations = s.get(u)
    r_image_configuration = json.loads(image_configurations.content)

    return r_image_configuration

def nfv_verify_device_deployment(s, url):
    s.headers = ({'Content-type': 'application/vnd.yang.data+json',
                      'Accept': 'application/vnd.yang.collection+json'})
    u = url + '/api/operational/vm_lifecycle/opdata/tenants/tenant/admin/deployments/'
    asa_deployment_page = s.get(u)

    if asa_deployment_page.status_code != 200:
        # Set headers back to default
        s.headers = ({'Content-type': 'application/vnd.yang.data+json', 'Accept': 'application/vnd.yang.data+json'})
        return False
    else:
        r_asa_deployment_page = json.loads(asa_deployment_page.content)
        # Set headers back to default
        s.headers = ({'Content-type': 'application/vnd.yang.data+json', 'Accept': 'application/vnd.yang.data+json'})
        return r_asa_deployment_page

def nfv_get_count_of_vm_deployments(s, url):
    u = url + '/api/config/vm_lifecycle/tenants/tenant/admin/deployments'
    count_vm_deployed_page = s.get(u)
    r_count_vm_deployed_page = json.loads(count_vm_deployed_page.content)

    for iv in r_count_vm_deployed_page.values():
        vm_deployed_count = len(iv['deployment'])
        return vm_deployed_count

def nfv_create_newbridge(s, url, new_bridge):
    u = url + "/api/config/bridges"
    make_bridge_payload = '{ "bridge": {"name": "%s" }}' % new_bridge
    r_create_bridge = s.post(u, data=make_bridge_payload)
    if '201' in r_create_bridge:
        return True
    else:
        return r_create_bridge

def nfv_create_new_network(s, url, new_network, new_bridge):
    u = url + "/api/config/networks"
    createnet_payload = '{ "network": {"name": "%s" , "bridge": "%s" }}' % (new_network, new_bridge)
    r_create_net = s.post(u, data=createnet_payload)
    return r_create_net

def nfv_deploy_vm(s, url, data):
    u = url + "/api/config/vm_lifecycle/tenants/tenant/admin/deployments"

    deployed_vm_page = s.post(u, data=data)
    r_deployed_vm_page = str(deployed_vm_page)
    if "201" in r_deployed_vm_page:
        return True
    else:
        return False

def nfv_delete_vm(s, url, data):
	u = url + "/api/config/vm_lifecycle/tenants/tenant/admin/deployments/deployment/" + data

	deleted_vm_page = s.delete(u)
	r_deleted_vm_page = str(deleted_vm_page)
	if "204" in r_deleted_vm_page:
		return True
	else:
		return False

if __name__ == '__main__':

    # basic credential setup for NFVIS device
    nip, url, login, password = nvfis_getgcred()
    s = requests.Session()
    s.auth = (login, password)
    s.headers = ({'Content-type': 'application/vnd.yang.data+json', 'Accept': 'application/vnd.yang.data+json'})
    s.verify = False
    print (nip, url, login, password)

    print ("STEP 1 - Verify device deployments and delete if there are any")
    r_vm_device_deployment = nfv_verify_device_deployment(s, url)
    if r_vm_device_deployment != False:
        for deployment in r_vm_device_deployment['collection']['vmlc:deployments']:
            delete_deployment = deployment['deployment_name']

            nfv_delete_vm(s, url, delete_deployment)
            time.sleep(10)

    print ("STEP 2 - Verify images exist")
    images = nfv_get_image_configuration(s,url)
    for image in images['vmlc:images']['image']:
        print (image['name'])

    print ("STEP 3.1 - Create bridge")
    r_create_lanbridge = nfv_create_newbridge(s, url, new_bridge)

    print ("STEP 3.2 - Create network and associate with bridge")
    r_create_net = nfv_create_new_network(s, url, new_network, new_bridge)

    print ("STEP 4.1 - Start ISR")
    r_create_isr = nfv_deploy_vm(s, url, json.dumps(nfvis_payload.isr_payload))
    print (r_create_isr)

    print ("STEP 4.2 - Start ASA")
    r_create_asa = nfv_deploy_vm(s, url, json.dumps(nfvis_payload.asa_payload))
    print (r_create_asa)

    print ("STEP 5.1 - Count running VMs")
    r_vm_deployed_count = nfv_get_count_of_vm_deployments(s, url)
    print (r_vm_deployed_count)

    print ("STEP 5.2 - Verify device deployments")
    r_vm_device_deployment = nfv_verify_device_deployment(s, url)
    print (json.dumps(r_vm_device_deployment, indent=4, sort_keys=True))
