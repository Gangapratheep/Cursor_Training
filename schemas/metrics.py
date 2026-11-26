"""Marshmallow schemas for metrics API payloads."""

from __future__ import annotations

from marshmallow import Schema, fields


class MemorySchema(Schema):
    used_bytes = fields.Int(allow_none=True)
    total_bytes = fields.Int(allow_none=True)
    percent = fields.Float(allow_none=True)


class NetworkSchema(Schema):
    bytes_sent = fields.Int(allow_none=True)
    bytes_recv = fields.Int(allow_none=True)


class ListeningPortSchema(Schema):
    proto = fields.Str()
    port = fields.Int()
    address = fields.Str()


class MetricsSchema(Schema):
    server_id = fields.Int(allow_none=True)
    status = fields.Str()
    error = fields.Str(allow_none=True)
    collected_at = fields.Str(allow_none=True)
    cpu_percent = fields.Float(allow_none=True)
    memory = fields.Nested(MemorySchema, allow_none=True)
    network = fields.Nested(NetworkSchema, allow_none=True)
    listening_ports = fields.List(fields.Nested(ListeningPortSchema))


class ServerMetricsItemSchema(Schema):
    id = fields.Int()
    display_name = fields.Str()
    hostname = fields.Str()
    ssh_port = fields.Int()
    auth_type = fields.Str()
    metrics = fields.Nested(MetricsSchema)


class ServerMetricsBatchSchema(Schema):
    servers = fields.List(fields.Nested(ServerMetricsItemSchema))
