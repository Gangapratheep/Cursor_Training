# Deploy (optional Kubernetes)

Day-to-day use is local (`python app.py` on `127.0.0.1`). The files below are for lab/demo clusters only.

## Artifacts

| Path | Role |
|------|------|
| `Dockerfile` | Image with Gunicorn on `0.0.0.0:5000` |
| `deploy/k8s/namespace.yaml` | Namespace `demomonitor` |
| `deploy/k8s/secret.yaml` | `FLASK_SECRET_KEY`, `ADMIN_PASSWORD` |
| `deploy/k8s/pvc.yaml` | SQLite data volume (1Gi RWO) |
| `deploy/k8s/deployment.yaml` | Single replica, probes on `/login` |
| `deploy/k8s/service.yaml` | ClusterIP port 80 → 5000 |
| `deploy/k8s/ingress.yaml` | Optional host `demomonitor.local` |

**Constraint:** one replica only — SQLite on a PVC is not multi-writer safe.

## Steps

```bash
docker build -t demomonitor:latest .
# kind load docker-image demomonitor:latest
# or: minikube image load demomonitor:latest

# Edit deploy/k8s/secret.yaml first
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/secret.yaml
kubectl apply -f deploy/k8s/pvc.yaml
kubectl apply -f deploy/k8s/deployment.yaml
kubectl apply -f deploy/k8s/service.yaml
# kubectl apply -f deploy/k8s/ingress.yaml

kubectl -n demomonitor port-forward svc/demomonitor 8080:80
# http://127.0.0.1:8080
```

Full walkthrough: [README.md](../README.md#deploy-on-kubernetes).

## Security notes for k8s

- Set strong values in `secret.yaml`; do not commit real secrets
- Pod sets `BIND_HOST=0.0.0.0` so the Service can reach the process
- Session auth and “no SSH secrets in JSON/HTML” still apply inside the cluster
