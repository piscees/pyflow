from flask import Flask
from flask import request
from flask import jsonify

import os
import json

import nodemaker
import fbp

app = Flask(__name__, static_url_path="")


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/nodestree", methods=['GET'])
def nodestree():
    tree = list()
    repository = fbp.repository()
    node_specs = repository.get("nodespec")

    for k, v in node_specs.iteritems():
        _insert(tree, v)
    return jsonify(tree)


def _insert(treeroot, node):
    id = node["id"]
    ids = id.split(".")
    found = False

    for n in treeroot:
        if n["id"] == ids[0]:
            found = True
            _inset_node(n, node, ids)

    if not found:
        item = dict()
        item["id"] = ids[0]
        item["title"] = ids[0]
        item["children"] = list()
        treeroot.append(item)
        _inset_node(item, node, ids)

    return


def _inset_node(parent, node, path):
    if len(path) == 1:
        if path[0] == parent["id"]:
            parent["value"] = node
    else:
        if path[0] == parent["id"]:
            children = parent["children"]
            found = False
            for item in children:
                if item["id"] == path[1]:
                    _inset_node(item, node, path[1:])
                    found = True

            if not found:
                item = dict()
                item["id"] = path[1]
                item["title"] = path[1]
                item["children"] = list()
                parent["children"].append(item)
                _inset_node(item, node, path[1:])
    return


@app.route("/nodes", methods=['GET'])
def nodes():
    repository = fbp.repository()
    node_specs = repository.get("nodespec")

    # Adding default output when it is not there
    for k, v in node_specs.iteritems():
        if not v["port"].has_key("output"):
            v["port"]["output"] = list()
            v["port"]["output"].append({"name": "out"})

    return jsonify(node_specs)


@app.route("/flows", methods=['GET', 'POST'])
def flows():
    repository = fbp.repository()
    if request.method == 'POST':
        data = request.form['data']
        flow = json.loads(data)
        repository.register("flow", flow["id"], flow)
        return jsonify(data)
    else:
        flows = repository.get("flow")
        result = [v for k, v in flows.items()]
        return jsonify(result)


@app.route("/runflow", methods=['POST'])
def runflow():
    data = request.form['data']
    return jsonify(fbp.run_flow(data))


def init():
    records = []
    for file in os.listdir('node_specs'):
        if file.endswith('.py') and file != '__init__.py':
            with open('node_specs' + os.path.sep + file)as f:
                spec = nodemaker.create_node_spec(f.read())
                records.append(json.dumps(spec))

    repository = fbp.repository()
    for r in records:
        node = json.loads(r)
        repository.register("nodespec", node["id"], node)


if __name__ == "__main__":
    init()
    app.run(host="0.0.0.0", threaded=True)
