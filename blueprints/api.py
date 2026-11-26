"""JSON metrics API (login-required, no secrets in payloads)."""

from __future__ import annotations

from flask import Blueprint, jsonify
from flask_restful import Api, Resource

from extensions import db
from metrics import collect_for_server
from models import Server
from schemas.metrics import MetricsSchema, ServerMetricsBatchSchema
from schemas.server import ServerPublicSchema
from utils.auth import login_required

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

_metrics_schema = MetricsSchema()
_batch_schema = ServerMetricsBatchSchema()
_server_public = ServerPublicSchema()


class ServerMetricsResource(Resource):
    """GET /api/servers/<id>/metrics"""

    method_decorators = [login_required]

    def get(self, server_id: int):
        server = db.session.get(Server, server_id)
        if server is None:
            return {"error": "Not found"}, 404
        payload = collect_for_server(server)
        return _metrics_schema.dump(payload)


class ServersMetricsBatchResource(Resource):
    """GET /api/servers/metrics"""

    method_decorators = [login_required]

    def get(self):
        servers = Server.query.order_by(Server.display_name).all()
        items = []
        for server in servers:
            public = _server_public.dump(server)
            public["metrics"] = collect_for_server(server)
            items.append(public)
        return _batch_schema.dump({"servers": items})


api.add_resource(ServersMetricsBatchResource, "/servers/metrics")
api.add_resource(ServerMetricsResource, "/servers/<int:server_id>/metrics")
