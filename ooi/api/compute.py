# -*- coding: utf-8 -*-

# Copyright 2015 Spanish National Research Council
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from ooi.api import base
from ooi.occi.core import collection
from ooi.occi.infrastructure import compute
from ooi.openstack import helpers
from ooi.openstack import templates


class Controller(base.Controller):
    def index(self, req):
        tenant_id = req.environ["keystone.token_auth"].user.project_id
        req = self._get_req(req, path="/%s/servers" % tenant_id)
        response = req.get_response(self.app)

        servers = response.json_body.get("servers", [])
        occi_compute_resources = []
        if servers:
            for s in servers:
                s = compute.ComputeResource(title=s["name"], id=s["id"])
                occi_compute_resources.append(s)

        return collection.Collection(resources=occi_compute_resources)

    def show(self, id, req):
        tenant_id = req.environ["keystone.token_auth"].user.project_id

        # get info from server
        req = self._get_req(req, path="/%s/servers/%s" % (tenant_id, id))
        response = req.get_response(self.app)
        s = response.json_body.get("server", {})

        # get info from flavor
        req = self._get_req(req, path="/%s/flavors/%s" % (tenant_id,
                                                          s["flavor"]["id"]))
        response = req.get_response(self.app)
        flavor = response.json_body.get("flavor", {})
        res_tpl = templates.OpenStackResourceTemplate(flavor["name"],
                                                      flavor["vcpus"],
                                                      flavor["ram"],
                                                      flavor["disk"])

        # get info from image
        req = self._get_req(req, path="/%s/images/%s" % (tenant_id,
                                                         s["image"]["id"]))
        response = req.get_response(self.app)
        image = response.json_body.get("image", {})
        os_tpl = templates.OpenStackOSTemplate(image["id"],
                                               image["name"])

        # build the compute object
        # TODO(enolfc): link to network + storage
        comp = compute.ComputeResource(title=s["name"], id=s["id"],
                                       cores=flavor["vcpus"],
                                       hostname=s["name"],
                                       memory=flavor["ram"],
                                       state=helpers.occi_state(s["status"]),
                                       mixins=[os_tpl, res_tpl])
        return [comp]
